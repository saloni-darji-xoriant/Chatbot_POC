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

import re
from dataclasses import dataclass
from datetime import datetime

from app.models import AttachmentSummary, Citation, Message, MessageImage, MessageSender, ProcessStep, ProcessStepStatus
from app.services.attachment_store import AttachmentRecord, get as get_attachment, search_attachments
from app.services import llm
from app.services.knowledge_base import KBEntry, find_entry, is_follow_up_question
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


# A single keyword hit ("panel") is a weak signal: the question is probably
# open-ended, so - when a language model is configured - it is answered
# conversationally from that entry instead of pasting the canned text.
WEAK_MATCH_SCORE = 1

# Each of these is also a routed KB follow-up (or a human request), so clicking
# one never dead-ends.
AI_QUICK_REPLIES = [
    "What do the inverter error codes mean?",
    "How do I diagnose low panel output?",
    "How do I escalate this to L2?",
    "Connect me to a live specialist",
]

_HUMAN_REQUEST_RE = re.compile(
    r"\b(talk|speak|chat)\s+(to|with)\s+(a\s+|an\s+|the\s+)?(human|person|agent|specialist|representative|someone|somebody|real)\b"
    r"|\b(live|human|real)\s+(agent|person|specialist|support|representative)\b"
    r"|\bconnect\s+me\b|\bhand\s*off\b|\bescalate\s+me\b",
    re.IGNORECASE,
)

OFFLINE_GUIDANCE = (
    "I'm sorry you're running into this - let's narrow it down together.\n\n"
    "A few quick things that will help me point you the right way:\n"
    "1. What is the inverter display or the monitoring app showing right now - any error code, or a red/orange light?\n"
    "2. When did it start, and did anything change just before (a storm, a power cut, a router or firmware update)?\n"
    "3. Is the whole system affected, or only some panels or strings?\n\n"
    "While you check, please stay safe: don't open the DC junction box, touch wiring or work on the roof. "
    "If you notice a burning smell, smoke, sparks or crackling, switch off the AC disconnect if it's safe to do so and call the emergency line straight away.\n\n"
    "Tell me what you find and I'll dig into the specific steps - or say the word and I'll connect you with a live specialist."
)


def wants_human(text: str) -> bool:
    return bool(_HUMAN_REQUEST_RE.search(text))


def needs_handoff(message: Message) -> bool:
    """A reply only escalates to the L2 handoff screen when it is neither
    grounded in the knowledge base nor a model-written answer - i.e. when the
    user explicitly asked for a person."""
    return not message.is_grounded and not message.is_ai_generated


@dataclass
class Plan:
    """What the pipeline will do for one message. Derived from cheap, pure
    inputs so the live trace and the final reply always agree."""

    kind: str  # "chitchat" | "kb" | "kb_ai" | "ai" | "handoff"
    chitchat: str | None = None
    entry: KBEntry | None = None
    attachment_hit: tuple | None = None


def plan_for(conversation_id: str, text: str, use_llm: bool = True) -> Plan:
    chitchat = classify_chitchat(text)
    if chitchat is not None:
        return Plan("chitchat", chitchat=chitchat)

    # An explicit request for a person wins over retrieval (whose loose keyword
    # matching could otherwise answer "connect me to a specialist" with a spec sheet).
    if wants_human(text) and not is_follow_up_question(text):
        return Plan("handoff")

    entry, score = find_entry(text)
    attachment_hit = search_attachments(conversation_id, text)

    if entry is None and attachment_hit is None:
        return Plan("ai")

    weak = (
        entry is not None
        and attachment_hit is None
        and score <= WEAK_MATCH_SCORE
        and not is_follow_up_question(text)
        and use_llm
        and llm.is_enabled()
    )
    return Plan("kb_ai" if weak else "kb", entry=entry, attachment_hit=attachment_hit)


def build_ai_steps(llm_on: bool) -> list[ProcessStep]:
    return [
        ProcessStep(label="Classify intent and route the query", status=ProcessStepStatus.done, agent="Router Agent"),
        ProcessStep(
            label="Retrieve candidate sources from the knowledge graph (no matching subgraph)",
            status=ProcessStepStatus.done,
            agent="Retrieval Agent (RAG)",
        ),
        ProcessStep(
            label=(
                "Draft a conversational reply with the language model"
                if llm_on
                else "Draft a conversational reply from built-in guidance"
            ),
            status=ProcessStepStatus.done,
            agent="Response Agent",
        ),
        ProcessStep(
            label="Not from the knowledge base - labelled as general guidance, with escalation offered",
            status=ProcessStepStatus.done,
            agent="Grounding Agent",
        ),
    ]


def _history(conversation_id: str) -> list[tuple[str, str]]:
    """Prior user/assistant turns for the language model, excluding the
    message currently being answered."""
    from app.store import store  # lazy: store seeds itself using this module

    conv = store.get_conversation(conversation_id)
    if conv is None:
        return []
    messages = conv.messages
    if messages and messages[-1].sender == MessageSender.user:
        messages = messages[:-1]
    return [(m.sender.value, m.text) for m in messages if m.sender != MessageSender.system]


def build_steps_for(conversation_id: str, text: str) -> list[ProcessStep]:
    """Cheap, side-effect-free step planning used by the SSE endpoint to
    reveal live progress before the final message is assembled."""
    plan = plan_for(conversation_id, text)
    if plan.kind == "chitchat":
        return build_chitchat_steps(plan.chitchat or "")
    if plan.kind == "ai":
        return build_ai_steps(llm.is_enabled())

    graph = get_graph(plan.entry) if plan.entry is not None else None
    steps = build_process_steps(plan.entry is not None, len(graph.nodes) if graph else 0, plan.attachment_hit)
    if plan.kind == "kb_ai":
        for step in steps:
            if step.agent == "Response Agent":
                step.label = "Reword the retrieved answer conversationally with the language model"
    return steps


def handoff_reply(conversation_id: str, when: datetime | None = None) -> Message:
    """The reply that sends the conversation to a live specialist (L2)."""
    return Message(
        id=new_id("msg"),
        conversation_id=conversation_id,
        sender=MessageSender.assistant,
        text="Of course - I'm connecting you with a live specialist (L2) who can take it from here.",
        created_at=when or utcnow(),
        citations=[],
        quick_replies=[],
        process_trace=build_process_steps(False, 0, None),
        knowledge_graph=None,
        is_grounded=False,
    )


def generate_assistant_reply(
    conversation_id: str, text: str, created_at: datetime | None = None, use_llm: bool = True
) -> Message:
    """Run the full pipeline for one user message and return the assistant's
    reply. Order of preference:

    1. Small talk -> friendly conversational reply.
    2. Knowledge base / attachment match -> grounded answer with citations,
       a diagram and follow-ups (reworded by the model when the match is weak).
    3. No match -> a human-sounding general-guidance reply (model-written, or
       built-in when no model is configured), never a handoff by itself.
    4. Only an explicit request for a person -> L2 handoff.
    """
    when = created_at or utcnow()
    plan = plan_for(conversation_id, text, use_llm)

    if plan.kind == "chitchat":
        kind = plan.chitchat or ""
        return Message(
            id=new_id("msg"),
            conversation_id=conversation_id,
            sender=MessageSender.assistant,
            text=CHITCHAT_RESPONSES[kind],
            created_at=when,
            citations=[],
            quick_replies=CHITCHAT_QUICK_REPLIES[kind],
            process_trace=build_chitchat_steps(kind),
            knowledge_graph=None,
            is_grounded=True,
        )

    if plan.kind == "handoff":
        return handoff_reply(conversation_id, when)

    if plan.kind == "ai":
        return build_ai_steps(llm.is_enabled())

    graph = get_graph(plan.entry) if plan.entry is not None else None
    steps = build_process_steps(plan.entry is not None, len(graph.nodes) if graph else 0, plan.attachment_hit)
    if plan.kind == "kb_ai":
        for step in steps:
            if step.agent == "Response Agent":
                step.label = "Reword the retrieved answer conversationally with the language model"
    return steps


def handoff_reply(conversation_id: str, when: datetime | None = None) -> Message:
    """The reply that sends the conversation to a live specialist (L2)."""
    return Message(
        id=new_id("msg"),
        conversation_id=conversation_id,
        sender=MessageSender.assistant,
        text="Of course - I'm connecting you with a live specialist (L2) who can take it from here.",
        created_at=when or utcnow(),
        citations=[],
        quick_replies=[],
        process_trace=build_process_steps(False, 0, None),
        knowledge_graph=None,
        is_grounded=False,
    )


def generate_assistant_reply(
    conversation_id: str, text: str, created_at: datetime | None = None, use_llm: bool = True
) -> Message:
    """Run the full pipeline for one user message and return the assistant's
    reply. Order of preference:

    1. Small talk -> friendly conversational reply.
    2. Knowledge base / attachment match -> grounded answer with citations,
       a diagram and follow-ups (reworded by the model when the match is weak).
    3. No match -> a human-sounding general-guidance reply (model-written, or
       built-in when no model is configured), never a handoff by itself.
    4. Only an explicit request for a person -> L2 handoff.
    """
    when = created_at or utcnow()
    plan = plan_for(conversation_id, text, use_llm)

    if plan.kind == "chitchat":
        kind = plan.chitchat or ""
        return Message(
            id=new_id("msg"),
            conversation_id=conversation_id,
            sender=MessageSender.assistant,
            text=CHITCHAT_RESPONSES[kind],
            created_at=when,
            citations=[],
            quick_replies=CHITCHAT_QUICK_REPLIES[kind],
            process_trace=build_chitchat_steps(kind),
            knowledge_graph=None,
            is_grounded=True,
        )

    if plan.kind == "handoff":
        return Message(
            id=new_id("msg"),
            conversation_id=conversation_id,
            sender=MessageSender.assistant,
            text=(
                "Of course - I'm connecting you with a live specialist (L2) who can take it from here."
            ),
            created_at=when,
            citations=[],
            quick_replies=[],
            process_trace=build_process_steps(False, 0, None),
            knowledge_graph=None,
            is_grounded=False,
        )

    if plan.kind == "ai":
        generated = llm.generate_reply(text, _history(conversation_id)) if use_llm else None
        return Message(
            id=new_id("msg"),
            conversation_id=conversation_id,
            sender=MessageSender.assistant,
            text=generated or OFFLINE_GUIDANCE,
            created_at=when,
            citations=[],
            quick_replies=list(AI_QUICK_REPLIES),
            process_trace=build_ai_steps(generated is not None),
            knowledge_graph=None,
            is_grounded=False,
            is_ai_generated=True,
        )

    entry, attachment_hit = plan.entry, plan.attachment_hit
    graph = get_graph(entry) if entry is not None else None
    steps = build_process_steps(entry is not None, len(graph.nodes) if graph else 0, attachment_hit)

    citations: list[Citation] = []
    answer_parts: list[str] = []
    ai_written = False

    if entry is not None:
        citations.extend(
            Citation(id=new_id("cit"), label=c["label"], document=c["document"], section=c.get("section"))
            for c in entry.citations
        )
        answer = entry.answer
        if plan.kind == "kb_ai":
            reworded = llm.generate_reply(text, _history(conversation_id), reference=entry.answer)
            if reworded:
                answer, ai_written = reworded, True
        answer_parts.append(answer)

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

    if plan.kind == "kb_ai":
        for step in steps:
            if step.agent == "Response Agent":
                step.label = (
                    "Reword the retrieved answer conversationally with the language model"
                    if ai_written
                    else "Compose a grounded answer from retrieved sources"
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
        is_ai_generated=ai_written,
    )
