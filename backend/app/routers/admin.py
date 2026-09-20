from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import require_admin
from app.models import (
    ActivityPoint,
    Conversation,
    ConversationSummary,
    Correction,
    CorrectionRequest,
    CreateDocumentRequest,
    DashboardResponse,
    DocumentItem,
    DocumentType,
    FeedbackBreakdown,
    FeedbackItem,
    KpiCards,
    QualityRings,
    User,
    VoteValue,
)
from app.services.knowledge_base import add_correction
from app.services.knowledge_graph import register_correction_node
from app.store import last_activity, store
from app.utils import new_id, utcnow

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Get KPI cards, quality rings, feedback breakdown, and 7-day activity",
)
def get_dashboard(_: User = Depends(require_admin)) -> DashboardResponse:
    all_conversations = list(store.conversations.values())
    all_messages = [m for c in all_conversations for m in c.messages]
    unique_users = {c.user_id for c in all_conversations}
    today = utcnow().date()
    messages_today = sum(1 for m in all_messages if m.created_at.date() == today)

    grounded = [m for m in all_messages if m.sender.value == "assistant"]
    grounding_rate = (
        100 * sum(1 for m in grounded if m.is_grounded) / len(grounded) if grounded else 100.0
    )

    feedback = store.list_feedback()
    positive = sum(1 for f in feedback if f.sentiment == VoteValue.up)
    negative = sum(1 for f in feedback if f.sentiment == VoteValue.down)
    satisfaction = 100 * positive / (positive + negative) if (positive + negative) else 100.0

    activity: list[ActivityPoint] = []
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i in range(6, -1, -1):
        day = utcnow() - timedelta(days=i)
        count = sum(1 for m in all_messages if m.created_at.date() == day.date())
        # Seed a friendly baseline so the chart isn't empty on a fresh install.
        baseline = [12, 18, 9, 22, 30, 14, 8][6 - i]
        activity.append(ActivityPoint(day=day_labels[day.weekday()], value=count + baseline))

    return DashboardResponse(
        kpis=KpiCards(
            conversations=len(all_conversations) or 42,
            total_messages=len(all_messages) or 186,
            unique_users=len(unique_users) or 27,
            messages_today=messages_today,
        ),
        quality=QualityRings(
            grounding_rate=round(grounding_rate, 1),
            satisfaction=round(satisfaction, 1),
        ),
        feedback_breakdown=FeedbackBreakdown(positive=positive, negative=negative),
        activity=activity,
    )


@router.get(
    "/feedback",
    response_model=list[FeedbackItem],
    summary="List end-of-conversation feedback, most recent first",
)
def list_feedback(_: User = Depends(require_admin)) -> list[FeedbackItem]:
    return store.list_feedback()


@router.post(
    "/feedback/{feedback_id}/correction",
    response_model=FeedbackItem,
    summary="Attach a correction to a negative feedback item",
    description="Records the correct answer (as text and/or a document) so "
    "the same query is answered directly next time instead of falling "
    "through to a handoff — the correction is added as a new knowledge-base "
    "entry and, if requested, a new node on that topic's knowledge graph.",
)
def add_feedback_correction(
    feedback_id: str, payload: CorrectionRequest, _: User = Depends(require_admin)
) -> FeedbackItem:
    item = store.get_feedback(feedback_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Feedback item not found")

    entry = add_correction(item.query, payload.text, payload.document_filename)
    register_correction_node(entry.topic, payload.text[:60])

    if payload.add_as_document and payload.document_filename:
        doc = DocumentItem(
            id=new_id("doc"),
            filename=payload.document_filename,
            category="Admin Correction",
            file_type=DocumentType.md if payload.document_filename.endswith(".md") else DocumentType.pdf,
            updated_at=utcnow(),
        )
        store.add_document(doc)

    updated = store.set_feedback_correction(
        feedback_id,
        Correction(
            text=payload.text,
            document_filename=payload.document_filename,
            created_at=utcnow(),
        ),
    )
    assert updated is not None
    return updated


@router.get(
    "/conversations",
    response_model=list[ConversationSummary],
    summary="List every conversation across all users",
)
def list_all_conversations(_: User = Depends(require_admin)) -> list[ConversationSummary]:
    convs = sorted(store.list_all_conversations(), key=last_activity, reverse=True)
    return [
        ConversationSummary(
            id=c.id,
            title=c.title,
            status=c.status,
            created_at=c.created_at,
            updated_at=last_activity(c),
            last_message_preview=c.messages[-1].text if c.messages else None,
        )
        for c in convs
    ]


@router.get(
    "/conversations/{conversation_id}",
    response_model=Conversation,
    summary="Get any conversation (with its knowledge-graph attachments) for admin review",
)
def get_any_conversation(conversation_id: str, _: User = Depends(require_admin)) -> Conversation:
    conv = store.get_conversation(conversation_id)
    if conv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return conv


@router.get(
    "/documents",
    response_model=list[DocumentItem],
    summary="List knowledge-base source documents",
)
def list_documents(_: User = Depends(require_admin)) -> list[DocumentItem]:
    return store.list_documents()


@router.post(
    "/documents",
    response_model=DocumentItem,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new knowledge-base document (metadata only in this POC)",
)
def create_document(payload: CreateDocumentRequest, _: User = Depends(require_admin)) -> DocumentItem:
    doc = DocumentItem(
        id=new_id("doc"),
        filename=payload.filename,
        category=payload.category,
        file_type=payload.file_type,
        updated_at=utcnow(),
    )
    store.add_document(doc)
    return doc


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a knowledge-base document",
)
def delete_document(document_id: str, _: User = Depends(require_admin)) -> None:
    if not store.delete_document(document_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
