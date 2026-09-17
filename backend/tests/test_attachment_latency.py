"""Latency regression guards for the attachment feature.

These don't assert a specific millisecond number (that would be flaky across
machines/CI runners) — they assert generous upper bounds that would only be
breached by an actual regression (e.g. someone accidentally adding a
synchronous network call, an O(n^2) scan, or removing the extraction/length
caps in attachment_store.py). The thresholds are 10-50x the latencies actually
observed against this backend during manual testing, so real regressions have
plenty of room to trip them while normal variance doesn't.

Synthetic fixtures are generated in-memory rather than checked into the repo:
a large text document sized at the MAX_EXTRACTED_CHARS cap (the worst case for
the keyword-scoring code we actually wrote and could regress), and a
multi-page PDF built with pypdf's own writer (guaranteed valid, exercises the
real page-iteration/parsing path pypdf-based extraction goes through).
"""

from __future__ import annotations

import io
import time

from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.main import app
from app.services.attachment_store import MAX_EXTRACTED_CHARS, MAX_PDF_PAGES

client = TestClient(app)

# Generous upper bounds — see module docstring for why these aren't tighter.
UPLOAD_LATENCY_BUDGET_S = 1.0
CHAT_ROUNDTRIP_LATENCY_BUDGET_S = 1.5


def _login() -> str:
    resp = client.post(
        "/api/auth/login",
        json={"email": "jordan.reyes@installer.qcells.com", "password": "installer123"},
    )
    return resp.json()["token"]


def _new_conversation(headers: dict) -> str:
    return client.post("/api/chat/conversations", json={}, headers=headers).json()["id"]


def _make_large_text(topic_sentence: str, target_chars: int) -> bytes:
    """A repeated-paragraph document sized at (just over) the extraction cap,
    with one distinctive sentence buried in the middle for the search to find."""
    filler = (
        "This section covers general installer guidance for residential solar "
        "arrays, including routine inspection intervals and safety notes. "
    )
    paragraphs = [filler] * (target_chars // (2 * len(filler)))
    paragraphs.insert(len(paragraphs) // 2, topic_sentence)
    text = "\n\n".join(paragraphs)
    # Pad further if still short, so we reliably exceed the cap.
    while len(text) < target_chars:
        text += "\n\n" + filler
    return text.encode("utf-8")


def _make_pdf(num_pages: int) -> bytes:
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_large_text_attachment_upload_latency_is_bounded() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv_id = _new_conversation(headers)

    content = _make_large_text(
        "The Q.INVERTER-9000 backup unit requires a firmware check every 90 days.",
        target_chars=MAX_EXTRACTED_CHARS * 2,  # bigger than the cap, to test truncation cost too
    )

    start = time.perf_counter()
    resp = client.post(
        f"/api/chat/conversations/{conv_id}/attachments",
        files={"file": ("large-manual.txt", io.BytesIO(content), "text/plain")},
        headers=headers,
    )
    elapsed = time.perf_counter() - start

    assert resp.status_code == 200
    assert resp.json()["has_extracted_text"] is True
    assert elapsed < UPLOAD_LATENCY_BUDGET_S, f"Upload took {elapsed:.3f}s, budget is {UPLOAD_LATENCY_BUDGET_S}s"


def test_multi_page_pdf_attachment_upload_latency_is_bounded() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv_id = _new_conversation(headers)

    # One more page than the cap, to also exercise the truncation-to-MAX_PDF_PAGES path.
    content = _make_pdf(MAX_PDF_PAGES + 1)

    start = time.perf_counter()
    resp = client.post(
        f"/api/chat/conversations/{conv_id}/attachments",
        files={"file": ("multi-page.pdf", io.BytesIO(content), "application/pdf")},
        headers=headers,
    )
    elapsed = time.perf_counter() - start

    assert resp.status_code == 200
    assert elapsed < UPLOAD_LATENCY_BUDGET_S, f"PDF upload took {elapsed:.3f}s, budget is {UPLOAD_LATENCY_BUDGET_S}s"


def test_chat_roundtrip_referencing_an_attachment_latency_is_bounded() -> None:
    """End-to-end: upload a large attachment, then ask a question the
    knowledge base can't answer but the attachment can. Times the full
    request (attachment search + pipeline + response assembly) since that's
    the latency a user actually feels when they hit send."""
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv_id = _new_conversation(headers)

    content = _make_large_text(
        "The Q.INVERTER-9000 backup unit requires a firmware check every 90 days.",
        target_chars=MAX_EXTRACTED_CHARS,
    )
    upload = client.post(
        f"/api/chat/conversations/{conv_id}/attachments",
        files={"file": ("large-manual.txt", io.BytesIO(content), "text/plain")},
        headers=headers,
    ).json()

    start = time.perf_counter()
    resp = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"text": "How often does the Q.INVERTER-9000 backup unit need a firmware check?"},
        headers=headers,
    )
    elapsed = time.perf_counter() - start

    assert resp.status_code == 200
    body = resp.json()
    assert body["conversation_status"] == "active"  # answered from the attachment, no handoff
    assistant = body["assistant_message"]
    assert assistant["is_grounded"] is True
    assert "90 days" in assistant["text"]
    assert any(c["document"] == "large-manual.txt" for c in assistant["citations"])
    assert elapsed < CHAT_ROUNDTRIP_LATENCY_BUDGET_S, (
        f"Chat round trip took {elapsed:.3f}s, budget is {CHAT_ROUNDTRIP_LATENCY_BUDGET_S}s"
    )
    _ = upload  # uploaded id isn't needed — attachments are remembered for the whole conversation


def test_multiple_large_attachments_query_latency_is_bounded() -> None:
    """Mirrors attaching two sizable documents and asking one question that
    must be scored against both — the scenario doesn't degrade badly just
    because there's more than one file in play."""
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv_id = _new_conversation(headers)

    doc_a = _make_large_text(
        "Installation handbook section 4: torque all racking bolts to 30 Nm.",
        target_chars=MAX_EXTRACTED_CHARS,
    )
    doc_b = _make_large_text(
        "Homeowner guide appendix B: solar PV systems typically pay back within 7 years.",
        target_chars=MAX_EXTRACTED_CHARS,
    )
    for filename, content in [("handbook.txt", doc_a), ("homeowner-guide.txt", doc_b)]:
        upload = client.post(
            f"/api/chat/conversations/{conv_id}/attachments",
            files={"file": (filename, io.BytesIO(content), "text/plain")},
            headers=headers,
        )
        assert upload.status_code == 200

    start = time.perf_counter()
    resp = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"text": "What is the typical payback period for solar PV systems?"},
        headers=headers,
    )
    elapsed = time.perf_counter() - start

    assert resp.status_code == 200
    assistant = resp.json()["assistant_message"]
    assert assistant["is_grounded"] is True
    assert "7 years" in assistant["text"]
    assert any(c["document"] == "homeowner-guide.txt" for c in assistant["citations"])
    assert elapsed < CHAT_ROUNDTRIP_LATENCY_BUDGET_S, (
        f"Two-attachment query took {elapsed:.3f}s, budget is {CHAT_ROUNDTRIP_LATENCY_BUDGET_S}s"
    )
