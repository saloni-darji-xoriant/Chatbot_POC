"""Follow-up questions, response images, PDF export, history ordering and
timezone-aware timestamps."""

from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.chat_pipeline import generate_assistant_reply
from app.services.knowledge_base import (
    FOLLOW_UP_ROUTES,
    KNOWLEDGE_BASE,
    entry_by_topic,
    find_entry,
)
from app.services.pdf_export import format_local, resolve_timezone
from app.utils import utcnow

client = TestClient(app)
STATIC = Path(__file__).resolve().parent.parent / "app" / "static"


def _headers() -> dict:
    resp = client.post(
        "/api/auth/login",
        json={"email": "jordan.reyes@installer.qcells.com", "password": "installer123"},
    )
    return {"Authorization": f"Bearer {resp.json()['token']}"}


def _ask(headers: dict, conv_id: str, text: str) -> dict:
    resp = client.post(f"/api/chat/conversations/{conv_id}/messages", json={"text": text}, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _new_conv(headers: dict, title: str = "Test chat") -> str:
    return client.post("/api/chat/conversations", json={"title": title}, headers=headers).json()["id"]


# --- follow-ups -------------------------------------------------------------

def test_every_entry_has_follow_ups_pointing_at_other_real_topics() -> None:
    topics = {e.topic for e in KNOWLEDGE_BASE}
    for entry in KNOWLEDGE_BASE:
        assert 2 <= len(entry.follow_ups) <= 4, entry.topic
        for fu in entry.follow_ups:
            assert fu["topic"] in topics, (entry.topic, fu)
            assert fu["topic"] != entry.topic, f"{entry.topic} follow-up repeats itself"


def test_no_follow_up_is_a_dead_end() -> None:
    """Clicking any follow-up lands on its target entry - never a handoff,
    never the same answer again."""
    for entry in KNOWLEDGE_BASE:
        for fu in entry.follow_ups:
            found, _ = find_entry(fu["question"])
            assert found is not None, fu
            assert found.topic == fu["topic"], (entry.topic, fu, found.topic)
            assert found.topic != entry.topic


def test_follow_up_question_text_maps_to_one_topic() -> None:
    seen: dict[str, str] = {}
    for entry in KNOWLEDGE_BASE:
        for fu in entry.follow_ups:
            assert seen.setdefault(fu["question"].lower(), fu["topic"]) == fu["topic"]
    assert len(FOLLOW_UP_ROUTES) == len(seen)


def test_reply_carries_follow_ups_end_to_end() -> None:
    headers = _headers()
    conv_id = _new_conv(headers)
    body = _ask(headers, conv_id, "my inverter shows an error code")
    assistant = body["assistant_message"]
    assert assistant["is_grounded"] is True
    assert len(assistant["quick_replies"]) >= 2

    follow = _ask(headers, conv_id, assistant["quick_replies"][0])["assistant_message"]
    assert follow["is_grounded"] is True
    assert follow["text"] != assistant["text"]


# --- images -----------------------------------------------------------------

def test_image_files_exist_and_are_referenced_correctly() -> None:
    referenced = 0
    for entry in KNOWLEDGE_BASE:
        for img in entry.images:
            assert img["url"].startswith("/static/kb-images/"), img
            assert (STATIC / img["url"].removeprefix("/static/")).is_file(), img
            assert img["alt"] and img["caption"]
            referenced += 1
    assert referenced >= 15


def test_troubleshooting_answers_include_an_image() -> None:
    for topic in ("inverter_fault", "error_code_reference", "rapid_shutdown", "battery_safety", "escalation_process"):
        assert entry_by_topic(topic).images, topic


def test_reply_includes_image_and_static_file_is_served() -> None:
    reply = generate_assistant_reply("conv_x", "how do I power cycle the inverter after a fault code")
    assert reply.images
    served = client.get(reply.images[0].url)
    assert served.status_code == 200
    assert served.headers["content-type"] == "image/png"


def test_small_talk_and_handoff_have_no_images() -> None:
    assert generate_assistant_reply("c", "hi").images == []
    assert generate_assistant_reply("c", "zxqv unrelated gibberish").images == []


# --- history ordering & timezone-aware timestamps ---------------------------

def test_history_is_most_recent_activity_first_with_updated_at() -> None:
    headers = _headers()
    first = _new_conv(headers, "History order A")
    second = _new_conv(headers, "History order B")
    # Activity in the older conversation makes it the most recent.
    _ask(headers, first, "how do I file a warranty claim")

    listing = client.get("/api/chat", headers=headers).json()
    ids = [c["id"] for c in listing]
    assert ids.index(first) < ids.index(second)
    stamps = [c["updated_at"] for c in listing]
    assert stamps == sorted(stamps, reverse=True)


def test_timestamps_are_timezone_aware_utc() -> None:
    assert utcnow().tzinfo is not None
    headers = _headers()
    conv_id = _new_conv(headers)
    msg = _ask(headers, conv_id, "hello")["assistant_message"]
    assert msg["created_at"].endswith("+00:00") or msg["created_at"].endswith("Z")


# --- PDF export -------------------------------------------------------------

def test_export_pdf_returns_pdf_with_filename() -> None:
    headers = _headers()
    conv_id = _new_conv(headers, "Inverter export check")
    _ask(headers, conv_id, "my inverter shows an error code")
    resp = client.get(f"/api/chat/conversations/{conv_id}/export.pdf?tz=Asia/Kolkata", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")
    assert "inverter-export-check" in resp.headers["content-disposition"]
    assert len(resp.content) > 20_000  # embeds a diagram


def test_export_pdf_handles_empty_conversation_and_bad_timezone() -> None:
    headers = _headers()
    conv_id = _new_conv(headers)
    resp = client.get(f"/api/chat/conversations/{conv_id}/export.pdf?tz=Not/AZone", headers=headers)
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")


def test_export_pdf_handles_non_latin_text() -> None:
    headers = _headers()
    conv_id = _new_conv(headers, "Smart “quotes” — 日本語")
    _ask(headers, conv_id, "café → 日本語 inverter fault")
    resp = client.get(f"/api/chat/conversations/{conv_id}/export.pdf", headers=headers)
    assert resp.status_code == 200


def test_export_pdf_requires_auth_and_ownership() -> None:
    headers = _headers()
    conv_id = _new_conv(headers)
    assert client.get(f"/api/chat/conversations/{conv_id}/export.pdf").status_code == 401
    assert client.get("/api/chat/conversations/nope/export.pdf", headers=headers).status_code == 404


def test_export_header_is_exposed_to_browsers() -> None:
    resp = client.options(
        "/api/chat/conversations/x/export.pdf",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert resp.status_code in (200, 400)
    headers = _headers()
    conv_id = _new_conv(headers)
    got = client.get(
        f"/api/chat/conversations/{conv_id}/export.pdf",
        headers={**headers, "Origin": "http://localhost:3000"},
    )
    assert "content-disposition" in got.headers["access-control-expose-headers"].lower()


def test_times_render_in_the_viewers_timezone() -> None:
    moment = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    assert format_local(moment, resolve_timezone("Asia/Kolkata")).startswith("15 Jan 2026, 5:30 PM")
    assert format_local(moment, resolve_timezone("America/New_York")).startswith("15 Jan 2026, 7:00 AM")
    assert format_local(moment, resolve_timezone(None)).endswith("UTC")
    assert format_local(moment, resolve_timezone("bogus")).endswith("UTC")
