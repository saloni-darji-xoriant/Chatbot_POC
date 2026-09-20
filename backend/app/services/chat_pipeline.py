"""A small simulated multi-agent RAG pipeline.

This is intentionally lightweight (no real LLM calls) so the POC runs fully
offline, but the *shape* of the pipeline mirrors a real one:

1. Router Agent       - classifies the query and decides whether to route it
                         to the knowledge base at all.
2. Retrieval Agent     - runs a (keyword-based) RAG lookup and pulls the
   (RAG)                 matching subgraph out of the knowledge graph.
2b. Document Agent     - (only when the conversation has attachments) scores
                         any files the user attached this session the same
                         way, so an uploaded document can ground an answer
                         the knowledge base alone couldn't.
3. Response Agent      - drafts an answer from whatever was retrieved.
4. Grounding Agent     - checks the draft is actually grounded in what was
                         retrieved; only if NEITHER the knowledge base NOR any
                         attachment matched does it flag the conversation for
                         an L1 -> L2 human handoff instead of guessing.

Each step produces a `ProcessStep` (with an `agent` label) that the frontend
renders as the live "thinking" trace and, per message, the developer trace
panel. `build_steps_for` and `generate_assistant_reply` independently derive
the same decision from the same (cheap, pure) inputs, so the live SSE trace
and the final message always agree — the same pattern already used for
chit-chat detection.
"""

from __future__ import annotations

from datetime import datetime

from app.models import AttachmentSummary, Citation, Message, MessageImage, MessageSender, ProcessStep, ProcessStepStatus
from app.services.attachment_store import AttachmentRecord, get as get_attachment, search_attachments
from app.services.knowledge_base import find_entry
from app.services.knowledge_graph import get_graph
from app.services.small_talk import CHITCHAT_QUICK_REPLIES, CHITCHAT_RESPONSES, classify_chitchat
from app.utils import new_id, utcnow


def _attachment_summary(record: AttachmentRecord) -> AttachmentSummary:
    return AttachmentSummary(
        id=record.id,
        conversation_id=record.conversation_id,
        filename=record.filename,
        mime_type=record.mime_type,
        kind=record.kind,
        size_bytes=record.size_bytes,
        has_extracted_text=bool(record.extracted_text),
        preview=(record.extracted_text[:200] if record.extracted_text else None),
        extraction_note=record.extraction_note,
        uploaded_at=record.uploaded_at,
    )


def resolve_attachments(attachment_ids: list[str]) -> list[AttachmentSummary]:
    """Look up uploaded-file metadata for tagging onto a user message."""
    summaries = []
    for attachment_id in attachment_ids:
        record = get_attachment(attachment_id)
        if record is not None:
            summaries.append(_attachment_summary(record))
    return summaries


def build_chitchat_steps(kind: str) -> list[ProcessStep]:
    return [
        ProcessStep(
            label="Classify intent and route the query",
            status=ProcessStepStatus.done,
            agent="Router Agent",
        ),
        ProcessStep(
            label=f"Recognized as conversational small talk ({kind}) — knowledge graph lookup skipped",
            status=ProcessStepStatus.done,
            agent="Retrieval Agent (RAG)",
        ),
        ProcessStep(
            label="Compose a friendly conversational reply",
            status=ProcessStepStatus.done,
            agent="Response Agent",
        ),
        ProcessStep(
            label="No factual claims to verify — nothing to ground",
            status=ProcessStepStatus.done,
            agent="Grounding Agent",
        ),
    ]


def build_attachment_step(filename: str) -> ProcessStep:
    return ProcessStep(
        label=f"Cross-referenced your attached file ({filename})",
        status=ProcessStepStatus.done,
        agent="Document Agent",
    )


def build_process_steps(matched: bool, node_count: int, attachment_hit: tuple | None = None) -> list[ProcessStep]:
    steps = [
        ProcessStep(
            label="Classify intent and route the query",
            status=ProcessStepStatus.done,
            agent="Router Agent",
        ),
        ProcessStep(
            label=(
                f"Retrieve candidate sources from the knowledge graph ({node_count} nodes matched)"
                if matched
                else "Retrieve candidate sources from the knowledge graph (no matching subgraph)"
            ),
            status=ProcessStepStatus.done,
            agent="Retrieval Agent (RAG)",
        ),
    ]

    grounded = matched or attachment_hit is not None
    if attachment_hit is not None:
        steps.append(build_attachment_step(attachment_hit[0].filename))

    steps.append(
        ProcessStep(
            label=(
                "Compose a grounded answer from retrieved sources"
                if grounded
                else "No sources available to compose a grounded answer"
            ),
            status=ProcessStepStatus.done,
            agent="Response Agent",
        )
    )
    steps.append(
        ProcessStep(
            label=(
                "Verify the answer is grounded and confidence is sufficient"
                if grounded
                else "Confidence too low — flag for human handoff"
            ),
            status=ProcessStepStatus.done,
            agent="Grounding Agent",
        )
    )
    return steps


def build_steps_for(conversation_id: str, text: str) -> list[ProcessStep]:
    """Cheap, side-effect-free step planning used by the SSE endpoint to
    reveal live progress before the final message is assembled."""
    chitchat = classify_chitchat(text)
    if chitchat is not None:
        return build_chitchat_steps(chitchat)

    entry, _score = find_entry(text)
    graph = get_graph(entry) if entry is not None else None
    attachment_hit = search_attachments(conversation_id, text)
    return build_process_steps(entry is not None, len(graph.nodes) if graph else 0, attachment_hit)


def generate_assistant_reply(conversation_id: str, text: str, created_at: datetime | None = None) -> Message:
    """Run the full mock pipeline for one user message and return the
    assistant's reply message (grounded — from the knowledge base and/or an
    attachment — or an ungrounded handoff message).

    Greetings/thanks/farewells are handled conversationally and never trigger
    a handoff — only a real support question with no knowledge-base match
    AND no matching attachment does.
    """
    when = created_at or utcnow()

    chitchat = classify_chitchat(text)
    if chitchat is not None:
        return Message(
            id=new_id("msg"),
            conversation_id=conversation_id,
            sender=MessageSender.assistant,
            text=CHITCHAT_RESPONSES[chitchat],
            created_at=when,
            citations=[],
            quick_replies=CHITCHAT_QUICK_REPLIES[chitchat],
            process_trace=build_chitchat_steps(chitchat),
            knowledge_graph=None,
            is_grounded=True,
        )

    entry, _score = find_entry(text)
    graph = get_graph(entry) if entry is not None else None
    attachment_hit = search_attachments(conversation_id, text)
    steps = build_process_steps(entry is not None, len(graph.nodes) if graph else 0, attachment_hit)

    if entry is None and attachment_hit is None:
        return Message(
            id=new_id("msg"),
            conversation_id=conversation_id,
            sender=MessageSender.assistant,
            text=(
                "I wasn't able to find a grounded answer to that in the knowledge "
                "base or your attached files, so I'm connecting you with a live "
                "specialist (L2) who can help."
            ),
            created_at=when,
            citations=[],
            quick_replies=[],
            process_trace=steps,
            knowledge_graph=None,
            is_grounded=False,
        )

    citations: list[Citation] = []
    answer_parts: list[str] = []

    if entry is not None:
        citations.extend(
            Citation(id=new_id("cit"), label=c["label"], document=c["document"], section=c.get("section"))
            for c in entry.citations
        )
        answer_parts.append(entry.answer)

    if attachment_hit is not None:
        record, chunk = attachment_hit
        answer_parts.append(f'From your attached file "{record.filename}":\n\n"{chunk.strip()}"')
        citations.append(
            Citation(
                id=new_id("cit"),
                label=f"Your attachment: {record.filename}",
                document=record.filename,
                section="Uploaded document",
            )
        )

    return Message(
        id=new_id("msg"),
        conversation_id=conversation_id,
        sender=MessageSender.assistant,
        text="\n\n".join(answer_parts),
        created_at=when,
        citations=citations,
        quick_replies=[fu["question"] for fu in entry.follow_ups] if entry is not None else [],
        process_trace=steps,
        knowledge_graph=graph,
        images=[MessageImage(**img) for img in entry.images] if entry is not None else [],
        is_grounded=True,
    )
