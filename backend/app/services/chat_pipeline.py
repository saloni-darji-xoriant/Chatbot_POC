"""A small simulated multi-agent RAG pipeline.

This is intentionally lightweight (no real LLM calls) so the POC runs fully
offline, but the *shape* of the pipeline mirrors a real one:

1. Router Agent       - classifies the query and decides whether to route it
                         to the knowledge base at all.
2. Retrieval Agent     - runs a (keyword-based) RAG lookup and pulls the
   (RAG)                 matching subgraph out of the knowledge graph.
3. Response Agent      - drafts an answer from the retrieved sources.
4. Grounding Agent     - checks the draft is actually grounded in what was
                         retrieved; if not, flags the conversation for an L1
                         -> L2 human handoff instead of guessing.

Each step produces a `ProcessStep` (with an `agent` label) that the frontend
renders as the live "thinking" trace and, per message, the developer trace
panel. The same function is used by the live chat endpoints and by
`store.py`'s seed data, so seeded conversations carry real knowledge-graph
attachments too.
"""

from __future__ import annotations

from datetime import datetime

from app.models import Citation, Message, MessageSender, ProcessStep, ProcessStepStatus
from app.services.knowledge_base import search
from app.services.knowledge_graph import get_graph
from app.services.small_talk import CHITCHAT_QUICK_REPLIES, CHITCHAT_RESPONSES, classify_chitchat
from app.utils import new_id


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


def build_process_steps(matched: bool, node_count: int) -> list[ProcessStep]:
    return [
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
        ProcessStep(
            label=(
                "Compose a grounded answer from retrieved sources"
                if matched
                else "No sources available to compose a grounded answer"
            ),
            status=ProcessStepStatus.done,
            agent="Response Agent",
        ),
        ProcessStep(
            label=(
                "Verify the answer is grounded and confidence is sufficient"
                if matched
                else "Confidence too low — flag for human handoff"
            ),
            status=ProcessStepStatus.done,
            agent="Grounding Agent",
        ),
    ]


def generate_assistant_reply(conversation_id: str, text: str, created_at: datetime | None = None) -> Message:
    """Run the full mock pipeline for one user message and return the
    assistant's reply message (grounded, with its knowledge graph attached,
    or an ungrounded handoff message).

    Greetings/thanks/farewells are handled conversationally and never trigger
    a handoff — only a real support question with no knowledge-base match does.
    """
    when = created_at or datetime.utcnow()

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

    entry, _score = search(text)
    matched = entry is not None
    graph = get_graph(entry) if matched else None
    steps = build_process_steps(matched, len(graph.nodes) if graph else 0)

    if entry is None:
        return Message(
            id=new_id("msg"),
            conversation_id=conversation_id,
            sender=MessageSender.assistant,
            text=(
                "I wasn't able to find a grounded answer to that in the knowledge "
                "base, so I'm connecting you with a live specialist (L2) who can help."
            ),
            created_at=when,
            citations=[],
            quick_replies=[],
            process_trace=steps,
            knowledge_graph=None,
            is_grounded=False,
        )

    citations = [
        Citation(id=new_id("cit"), label=c["label"], document=c["document"], section=c.get("section"))
        for c in entry.citations
    ]
    return Message(
        id=new_id("msg"),
        conversation_id=conversation_id,
        sender=MessageSender.assistant,
        text=entry.answer,
        created_at=when,
        citations=citations,
        quick_replies=entry.quick_replies,
        process_trace=steps,
        knowledge_graph=graph,
        is_grounded=True,
    )
