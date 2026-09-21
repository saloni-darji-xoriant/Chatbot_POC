"""Open-ended questions get a human-sounding reply (not the handoff screen);
only an explicit request for a person escalates to L2."""

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import llm
from app.services.chat_pipeline import (
    AI_QUICK_REPLIES,
    OFFLINE_GUIDANCE,
    generate_assistant_reply,
    needs_handoff,
    plan_for,
    wants_human,
)
from app.services.knowledge_base import FOLLOW_UP_ROUTES

client = TestClient(app)

OPEN_ENDED = "asdkjaslkdj my rooftop setup is misbehaving again today"


def _headers() -> dict:
    resp = client.post(
        "/api/auth/login",
        json={"email": "jordan.reyes@installer.qcells.com", "password": "installer123"},
    )
    return {"Authorization": f"Bearer {resp.json()['token']}"}


def _conv(headers: dict) -> str:
    return client.post("/api/chat/conversations", json={}, headers=headers).json()["id"]


# --- routing decisions ------------------------------------------------------

def test_open_ended_question_is_answered_not_handed_off() -> None:
    reply = generate_assistant_reply("c", OPEN_ENDED)
    assert reply.is_ai_generated is True
    assert reply.text == OFFLINE_GUIDANCE  # no key configured -> built-in guidance
    assert needs_handoff(reply) is False
    assert reply.quick_replies == AI_QUICK_REPLIES


def test_only_an_explicit_request_for_a_person_hands_off() -> None:
    for text in ("Connect me to a live specialist", "can I talk to a human?", "I want to speak with an agent"):
        assert wants_human(text), text
        reply = generate_assistant_reply("c", text)
        assert needs_handoff(reply) is True, text
    assert not wants_human("my inverter shows error E04")


def test_ai_quick_replies_never_dead_end() -> None:
    for question in AI_QUICK_REPLIES:
        routed = question.lower() in FOLLOW_UP_ROUTES
        assert routed or wants_human(question), question


def test_offline_guidance_is_safe_and_asks_clarifying_questions() -> None:
    lowered = OFFLINE_GUIDANCE.lower()
    assert "?" in OFFLINE_GUIDANCE
    assert "don't open the dc junction box" in lowered
    assert "live specialist" in lowered


# --- language model behaviour ----------------------------------------------

def test_model_reply_is_used_for_open_ended_questions(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict = {}

    def fake(user_text, history=None, reference=None):
        calls.update(text=user_text, history=history, reference=reference)
        return "Sorry to hear that - is the inverter showing any error code?"

    monkeypatch.setattr(llm, "generate_reply", fake)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    reply = generate_assistant_reply("c", OPEN_ENDED)
    assert reply.text.startswith("Sorry to hear that")
    assert reply.is_ai_generated and not reply.is_grounded and not needs_handoff(reply)
    assert calls["reference"] is None


def test_weak_kb_match_is_reworded_from_the_reference(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict = {}

    def fake(user_text, history=None, reference=None):
        calls["reference"] = reference
        return "I'm sorry your panels aren't working - let's check the basics together."

    monkeypatch.setattr(llm, "generate_reply", fake)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    text = "my solar panel is not working"
    assert plan_for("c", text).kind == "kb_ai"
    reply = generate_assistant_reply("c", text)
    assert reply.text.startswith("I'm sorry")
    assert reply.is_grounded and reply.is_ai_generated
    assert reply.citations, "a reworded answer keeps its KB citations"
    assert calls["reference"], "the KB answer is passed to the model as the reference"


def test_routed_follow_ups_stay_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "generate_reply", lambda *a, **k: pytest.fail("model must not be called"))
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    reply = generate_assistant_reply("c", "What do the inverter error codes mean?")
    assert reply.is_grounded and not reply.is_ai_generated


def test_model_failure_falls_back_to_built_in_guidance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def boom(*args, **kwargs):
        raise httpx.ConnectError("network down")

    monkeypatch.setattr(httpx, "post", boom)
    reply = generate_assistant_reply("c", OPEN_ENDED)
    assert reply.text == OFFLINE_GUIDANCE
    assert needs_handoff(reply) is False


def test_weak_match_falls_back_to_the_kb_answer_when_model_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: (_ for _ in ()).throw(httpx.ReadTimeout("slow")))
    reply = generate_assistant_reply("c", "my solar panel is not working")
    assert reply.is_grounded and not reply.is_ai_generated
    assert reply.text  # the canned KB answer


# --- provider plumbing (no network) ----------------------------------------

def test_config_is_inferred_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    assert llm.get_config() is None and not llm.is_enabled()
    monkeypatch.setenv("OPENAI_API_KEY", "k1")
    assert llm.get_config().provider == "openai"
    monkeypatch.delenv("OPENAI_API_KEY")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k2")
    cfg = llm.get_config()
    assert cfg.provider == "anthropic" and cfg.model.startswith("claude")


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_openai_request_shape_and_history(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "secret-key")
    seen: dict = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        seen.update(url=url, headers=headers, body=json)
        return _FakeResponse({"choices": [{"message": {"content": "  Hello there  "}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    out = llm.generate_reply(
        "still nothing",
        history=[("assistant", "orphan"), ("user", "no power"), ("assistant", "check the display"), ("user", "dark")],
    )
    assert out == "Hello there"
    assert seen["url"].endswith("/chat/completions")
    assert seen["headers"]["Authorization"] == "Bearer secret-key"
    roles = [m["role"] for m in seen["body"]["messages"]]
    assert roles[0] == "system" and roles[1] == "user"  # leading assistant turn dropped
    assert seen["body"]["messages"][-1]["content"].endswith("still nothing")
    assert "roof" in seen["body"]["messages"][0]["content"]  # safety rule is in the prompt


def test_anthropic_request_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret-key")
    seen: dict = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        seen.update(url=url, headers=headers, body=json)
        return _FakeResponse({"content": [{"type": "text", "text": "Hi!"}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    assert llm.generate_reply("hello", reference="Power cycle the inverter.") == "Hi!"
    assert seen["url"].endswith("/v1/messages")
    assert seen["headers"]["x-api-key"] == "secret-key"
    assert "Power cycle the inverter." in seen["body"]["system"]
    assert seen["body"]["messages"] == [{"role": "user", "content": "hello"}]


def test_api_key_is_never_logged_or_returned(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "super-secret-key")

    def boom(*args, **kwargs):
        raise httpx.HTTPStatusError("401 super-secret-key", request=None, response=None)

    monkeypatch.setattr(httpx, "post", boom)
    with caplog.at_level("WARNING"):
        assert llm.generate_reply("hi") is None
    assert "super-secret-key" not in caplog.text


# --- end to end through the API --------------------------------------------

def test_api_open_ended_message_does_not_escalate() -> None:
    headers = _headers()
    conv_id = _conv(headers)
    body = client.post(
        f"/api/chat/conversations/{conv_id}/messages", json={"text": OPEN_ENDED}, headers=headers
    ).json()
    assert body["conversation_status"] == "active"
    assert body["assistant_message"]["is_ai_generated"] is True


def test_api_stream_open_ended_message_has_no_handoff_event() -> None:
    headers = _headers()
    conv_id = _conv(headers)
    with client.stream(
        "POST", f"/api/chat/conversations/{conv_id}/messages/stream", json={"text": OPEN_ENDED}, headers=headers
    ) as resp:
        raw = "".join(resp.iter_text())
    names = [line.removeprefix("event:").strip() for line in raw.splitlines() if line.startswith("event:")]
    assert "assistant_message" in names and "handoff" not in names
    done = json.loads(next(l for l in raw.splitlines() if l.startswith("data:") and "conversation_status" in l)[5:])
    assert done["conversation_status"] == "active"


def test_api_explicit_human_request_escalates() -> None:
    headers = _headers()
    conv_id = _conv(headers)
    body = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"text": "Connect me to a live specialist"},
        headers=headers,
    ).json()
    assert body["conversation_status"] == "handoff"
