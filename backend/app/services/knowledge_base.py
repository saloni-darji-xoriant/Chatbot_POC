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
    quick_replies: list[str] = field(default_factory=list)


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
            quick_replies=r.get("quick_replies", []),
        )
        for r in records
    ]


KNOWLEDGE_BASE: list[KBEntry] = [
    entry for filename in _SOURCE_FILES for entry in _load_entries(filename)
]

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
