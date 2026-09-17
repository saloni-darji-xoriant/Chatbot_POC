import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.auth import get_current_user
from app.models import (
    AttachmentSummary,
    Conversation,
    ConversationStatus,
    ConversationSummary,
    CreateConversationRequest,
    FeedbackItem,
    HandoffContact,
    HandoffInfo,
    HandoffRequest,
    Message,
    MessageSender,
    ProcessStep,
    ProcessStepStatus,
    RatingRequest,
    RatingResponse,
    SendMessageRequest,
    SendMessageResponse,
    User,
    VoteRequest,
)
from app.services import attachment_store
from app.services.chat_pipeline import build_steps_for, generate_assistant_reply, resolve_attachments
from app.store import store
from app.utils import new_id

router = APIRouter(prefix="/chat", tags=["Chat"])


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/conversations", response_model=Conversation, summary="Start a new conversation")
def create_conversation(
    payload: CreateConversationRequest, user: User = Depends(get_current_user)
) -> Conversation:
    return store.create_conversation(user.id, payload.title)


@router.get(
    "",
    response_model=list[ConversationSummary],
    summary="List the current user's conversation history",
)
def list_conversations(user: User = Depends(get_current_user)) -> list[ConversationSummary]:
    convs = sorted(
        store.list_conversations_for_user(user.id), key=lambda c: c.created_at, reverse=True
    )
    return [
        ConversationSummary(
            id=c.id,
            title=c.title,
            status=c.status,
            created_at=c.created_at,
            last_message_preview=c.messages[-1].text if c.messages else None,
        )
        for c in convs
    ]


@router.get(
    "/help-contacts",
    response_model=list[HandoffContact],
    summary="Get the standing support contact list shown on the Help Center page",
)
def help_contacts() -> list[HandoffContact]:
    from app.services.knowledge_base import HANDOFF_CONTACTS

    return [HandoffContact(**c) for c in HANDOFF_CONTACTS]


@router.get(
    "/conversations/{conversation_id}",
    response_model=Conversation,
    summary="Get a conversation with its full message history",
)
def get_conversation(conversation_id: str, user: User = Depends(get_current_user)) -> Conversation:
    conv = store.get_conversation(conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return conv


@router.post(
    "/conversations/{conversation_id}/attachments",
    response_model=AttachmentSummary,
    summary="Attach a document or image to the conversation",
    description="The file is held only in server memory for this conversation "
    "(never written to disk) and text is extracted once, immediately, so "
    "later questions against it are a fast in-memory lookup rather than "
    "re-parsing the file. Max 5MB per file, 8 attachments per conversation.",
)
async def upload_attachment(
    conversation_id: str, file: UploadFile = File(...), user: User = Depends(get_current_user)
) -> AttachmentSummary:
    conv = store.get_conversation(conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

    content = await file.read()
    try:
        record = attachment_store.add_attachment(
            conversation_id, file.filename or "untitled", file.content_type or "application/octet-stream", content
        )
    except attachment_store.AttachmentTooLarge as exc:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, str(exc)) from exc
    except attachment_store.AttachmentLimitReached as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    return resolve_attachments([record.id])[0]


@router.get(
    "/conversations/{conversation_id}/attachments",
    response_model=list[AttachmentSummary],
    summary="List files attached to this conversation this session",
)
def list_attachments(conversation_id: str, user: User = Depends(get_current_user)) -> list[AttachmentSummary]:
    conv = store.get_conversation(conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return resolve_attachments([a.id for a in attachment_store.get_for_conversation(conversation_id)])


@router.delete(
    "/conversations/{conversation_id}/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an attachment before it's referenced by any message",
)
def delete_attachment(
    conversation_id: str, attachment_id: str, user: User = Depends(get_current_user)
) -> None:
    conv = store.get_conversation(conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    if not attachment_store.delete(conversation_id, attachment_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Attachment not found")


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=SendMessageResponse,
    summary="Send a user message and get the assistant's grounded (or handoff) reply",
    description="Synchronous variant of the send-message flow. Prefer the "
    "`/messages/stream` SSE endpoint for the live UI so the multi-agent trace "
    "streams as it runs.",
)
def send_message(
    conversation_id: str, payload: SendMessageRequest, user: User = Depends(get_current_user)
) -> SendMessageResponse:
    conv = store.get_conversation(conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

    store.maybe_set_title(conv, payload.text)
    user_message = Message(
        id=new_id("msg"),
        conversation_id=conversation_id,
        sender=MessageSender.user,
        text=payload.text,
        created_at=datetime.utcnow(),
        attachments=resolve_attachments(payload.attachment_ids),
    )
    store.add_message(conversation_id, user_message)

    assistant_message = generate_assistant_reply(conversation_id, payload.text)
    if not assistant_message.is_grounded:
        conv.status = ConversationStatus.handoff
    store.add_message(conversation_id, assistant_message)

    return SendMessageResponse(
        user_message=user_message,
        assistant_message=assistant_message,
        conversation_status=conv.status,
    )


async def _stream_pipeline(conversation_id: str, text: str, attachment_ids: list[str]):
    conv = store.get_conversation(conversation_id)
    if conv is None:
        yield _sse("error", {"message": "Conversation not found"})
        return

    store.maybe_set_title(conv, text)
    user_message = Message(
        id=new_id("msg"),
        conversation_id=conversation_id,
        sender=MessageSender.user,
        text=text,
        created_at=datetime.utcnow(),
        attachments=resolve_attachments(attachment_ids),
    )
    store.add_message(conversation_id, user_message)
    yield _sse("user_message", json.loads(user_message.model_dump_json()))
    await asyncio.sleep(0.15)

    steps = build_steps_for(conversation_id, text)

    # Reveal each agent's step progressively so the UI can show real,
    # backend-driven "thinking" progress instead of a client-side fake timer.
    for i in range(len(steps)):
        progressive = [
            ProcessStep(
                label=s.label,
                agent=s.agent,
                status=(
                    ProcessStepStatus.done
                    if j < i
                    else (ProcessStepStatus.active if j == i else ProcessStepStatus.pending)
                ),
            )
            for j, s in enumerate(steps)
        ]
        yield _sse("trace", {"steps": [json.loads(s.model_dump_json()) for s in progressive]})
        await asyncio.sleep(0.4)

    yield _sse("trace", {"steps": [json.loads(s.model_dump_json()) for s in steps]})
    await asyncio.sleep(0.2)

    assistant_message = generate_assistant_reply(conversation_id, text)
    store.add_message(conversation_id, assistant_message)
    yield _sse("assistant_message", json.loads(assistant_message.model_dump_json()))

    if not assistant_message.is_grounded:
        conv.status = ConversationStatus.handoff
        from app.services.knowledge_base import HANDOFF_CONTACTS

        handoff_info = HandoffInfo(
            message="You're being connected to a live specialist. Average wait time is 3-5 minutes.",
            contacts=[HandoffContact(**c) for c in HANDOFF_CONTACTS],
            queue_position=2,
        )
        yield _sse("handoff", json.loads(handoff_info.model_dump_json()))

    yield _sse("done", {"conversation_status": conv.status.value})


@router.post(
    "/conversations/{conversation_id}/messages/stream",
    summary="Send a message and stream the multi-agent pipeline + reply via Server-Sent Events",
    description="Streams `text/event-stream` events as the request is "
    "processed: `user_message`, repeated `trace` updates (one per pipeline "
    "agent: Router, Retrieval/RAG, Response, Grounding), the final "
    "`assistant_message`, an optional `handoff` event, and a closing `done` "
    "event with the conversation's resulting status.",
)
async def send_message_stream(
    conversation_id: str, payload: SendMessageRequest, user: User = Depends(get_current_user)
) -> StreamingResponse:
    conv = store.get_conversation(conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

    return StreamingResponse(
        _stream_pipeline(conversation_id, payload.text, payload.attachment_ids),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/conversations/{conversation_id}/handoff",
    response_model=HandoffInfo,
    summary="Explicitly escalate a conversation from L1 to a live agent (L2)",
)
def trigger_handoff(
    conversation_id: str, payload: HandoffRequest, user: User = Depends(get_current_user)
) -> HandoffInfo:
    from app.services.knowledge_base import HANDOFF_CONTACTS

    conv = store.get_conversation(conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    conv.status = ConversationStatus.handoff
    return HandoffInfo(
        message="You're being connected to a live specialist. Average wait time is 3-5 minutes.",
        contacts=[HandoffContact(**c) for c in HANDOFF_CONTACTS],
        queue_position=2,
    )


@router.post(
    "/messages/{message_id}/vote",
    response_model=Message,
    summary="Thumbs up/down an assistant message, optionally with a reason (shown for thumbs-down)",
    description="A thumbs-down vote immediately records an admin-visible "
    "feedback item (with the optional reason) — it doesn't wait for the "
    "end-of-conversation rating, so negative signal surfaces right away.",
)
def vote_message(
    message_id: str, payload: VoteRequest, user: User = Depends(get_current_user)
) -> Message:
    found = store.find_message(message_id)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")
    conv, msg = found
    if conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")
    msg.vote = payload.vote
    msg.vote_reason = payload.reason

    if payload.vote is not None:
        preceding_query = next(
            (m.text for m in reversed(conv.messages) if m.sender == MessageSender.user and m.created_at <= msg.created_at),
            conv.title,
        )
        store.record_feedback(
            FeedbackItem(
                id=new_id("fb"),
                conversation_id=conv.id,
                message_id=msg.id,
                query=preceding_query,
                sentiment=payload.vote,
                stars=None,
                comment=payload.reason,
                created_at=datetime.utcnow(),
                user_name=user.name,
            )
        )

    return msg


@router.post(
    "/conversations/{conversation_id}/rating",
    response_model=RatingResponse,
    summary="Submit the end-of-conversation star rating / thumbs / free-text feedback",
)
def rate_conversation(
    conversation_id: str, payload: RatingRequest, user: User = Depends(get_current_user)
) -> RatingResponse:
    conv = store.get_conversation(conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

    conv.status = ConversationStatus.resolved
    first_user_message = next((m.text for m in conv.messages if m.sender == MessageSender.user), conv.title)

    if payload.thumbs is not None:
        store.record_feedback(
            FeedbackItem(
                id=new_id("fb"),
                conversation_id=conversation_id,
                message_id=None,
                query=first_user_message,
                sentiment=payload.thumbs,
                stars=payload.stars,
                comment=payload.comment,
                created_at=datetime.utcnow(),
                user_name=user.name,
            )
        )

    return RatingResponse(
        conversation_id=conversation_id,
        stars=payload.stars,
        thumbs=payload.thumbs,
        comment=payload.comment,
        created_at=datetime.utcnow(),
    )
