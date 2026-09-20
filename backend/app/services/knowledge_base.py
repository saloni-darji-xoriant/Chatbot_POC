"""The Hanwha Qcells L1 Assistant knowledge base.

Content lives in `app/data/*.json` as four source categories — solar system
product specs, historical support case tickets, installer FAQ entries, and
general reference guides distilled from real third-party solar PV
documentation — matching the scope requested for this POC. In a real
deployment this would be a vector-search / RAG service backed by a document
store and a knowledge graph; here we do keyword matching over these same
categories so the app is fully runnable offline while keeping the response
shape (answer + citations + topic + confidence) the multi-agent pipeline
expects.

The "Reference Guide" entries (reference_guides.json) are original summaries
of the real facts in two source PDFs (a CAMTECH/Indian Railways installation
& maintenance handbook, and SEAI's "A Homeowner's Guide to Solar PV") —
written in our own words rather than copied verbatim, and scoped to the
jurisdiction-agnostic technical/consumer-education content. Region-specific
regulatory or grant figures from those source documents (which are
Ireland-specific) were deliberately left out so they don't contradict this
app's US-oriented installer content (NEC codes, federal ITC, etc.) elsewhere
in the knowledge base.

Admin-submitted corrections (see routers/admin.py) are appended to
KNOWLEDGE_BASE at runtime, so a query that previously fell through to
handoff can be answered directly next time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_SOURCE_FILES = [
    "solar_systems.json",
    "case_tickets.json",
    "installer_queries.json",
    "reference_guides.json",
]


@dataclass
class KBEntry:
    keywords: list[str]
    answer: str
    citations: list[dict]
    topic: str
    title: str
    category: str = "Installer FAQ"
    # Curated next-step questions, each routed to a specific other entry
    # ({"question": ..., "topic": ...}) so a click never dead-ends.
    follow_ups: list[dict] = field(default_factory=list)
    # Diagrams shown with the answer ({"url", "alt", "caption"}).
    images: list[dict] = field(default_factory=list)


def _load_entries(filename: str) -> list[KBEntry]:
    path = _DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)
    return [
        KBEntry(
            keywords=r["keywords"],
            answer=r["answer"],
            citations=r["citations"],
            topic=r["topic"],
            title=r["title"],
            category=r.get("category", "Installer FAQ"),
            follow_ups=r.get("follow_ups", []),
            images=r.get("images", []),
        )
        for r in records
    ]


KNOWLEDGE_BASE: list[KBEntry] = [
    entry for filename in _SOURCE_FILES for entry in _load_entries(filename)
]


def _normalize(question: str) -> str:
    return " ".join(question.lower().split())


def _build_follow_up_routes() -> dict[str, str]:
    """normalized follow-up question -> target topic. A given question text
    must always mean the same topic (enforced here, so a bad edit to the JSON
    fails at import time rather than misrouting a click)."""
    routes: dict[str, str] = {}
    for entry in KNOWLEDGE_BASE:
        for fu in entry.follow_ups:
            key = _normalize(fu["question"])
            if routes.setdefault(key, fu["topic"]) != fu["topic"]:
                raise ValueError(f"Follow-up '{fu['question']}' routes to two different topics")
    return routes


FOLLOW_UP_ROUTES: dict[str, str] = _build_follow_up_routes()


def entry_by_topic(topic: str) -> KBEntry | None:
    return next((e for e in KNOWLEDGE_BASE if e.topic == topic), None)


def find_entry(query: str) -> tuple[KBEntry | None, int]:
    """Like `search`, but a query that is exactly one of the curated
    follow-up questions goes straight to its target entry - keyword search is
    only a fallback for free-typed questions."""
    topic = FOLLOW_UP_ROUTES.get(_normalize(query))
    if topic is not None:
        routed = entry_by_topic(topic)
        if routed is not None:
            return routed, len(routed.keywords)
    return search(query)


CONFIDENCE_THRESHOLD = 1  # minimum keyword hits required to consider it "grounded"


def search(query: str) -> tuple[KBEntry | None, int]:
    """Return the best-matching KB entry and its match score."""
    normalized = query.lower()
    best_entry: KBEntry | None = None
    best_score = 0

    for entry in KNOWLEDGE_BASE:
        score = sum(1 for kw in entry.keywords if kw in normalized)
        if score > best_score:
            best_score = score
            best_entry = entry

    if best_score < CONFIDENCE_THRESHOLD:
        return None, 0
    return best_entry, best_score


def add_correction(query: str, correction_text: str, document_filename: str | None) -> KBEntry:
    """Turn an admin correction into a new KB entry so the same negative
    feedback query is answered directly next time, instead of handing off."""
    stopwords = {
        "the", "a", "an", "is", "are", "my", "to", "for", "of", "and", "on",
        "in", "it", "i", "was", "with", "how", "do", "does", "not", "won't",
    }
    keywords = [w for w in query.lower().split() if len(w) > 2 and w not in stopwords][:6]
    topic = f"correction_{len(KNOWLEDGE_BASE)}"
    citations = (
        [{"label": document_filename, "document": document_filename, "section": "Admin correction"}]
        if document_filename
        else [{"label": "Admin correction", "document": "admin-correction.md", "section": None}]
    )
    entry = KBEntry(
        keywords=keywords or [query.lower()[:20]],
        answer=correction_text,
        citations=citations,
        topic=topic,
        title=f"Correction: {query[:50]}",
        category="Admin Correction",
    )
    KNOWLEDGE_BASE.append(entry)
    return entry


HANDOFF_CONTACTS = [
    {"label": "Installer Hotline", "value": "1-800-555-0142", "icon": "phone"},
    {"label": "Emergency / Safety", "value": "1-800-555-0199", "icon": "alert-triangle"},
    {"label": "Email Support", "value": "installer-support@qcells.com", "icon": "mail"},
    {"label": "Warranty Claims", "value": "warranty@qcells.com", "icon": "shield-check"},
]
