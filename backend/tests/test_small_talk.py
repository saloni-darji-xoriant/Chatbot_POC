from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login() -> str:
    resp = client.post(
        "/api/auth/login",
        json={"email": "jordan.reyes@installer.qcells.com", "password": "installer123"},
    )
    assert resp.status_code == 200
    return resp.json()["token"]


def test_greeting_does_not_trigger_handoff() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/chat/conversations", json={}, headers=headers).json()

    resp = client.post(
        f"/api/chat/conversations/{conv['id']}/messages",
        json={"text": "hi"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["conversation_status"] == "active"
    assert body["assistant_message"]["is_grounded"] is True
    assert "Qcells L1 Assistant" in body["assistant_message"]["text"]
    assert body["assistant_message"]["citations"] == []


def test_thanks_and_farewell_are_conversational() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}

    for text, expected_snippet in [("thanks a lot", "welcome"), ("bye", "Take care")]:
        conv = client.post("/api/chat/conversations", json={}, headers=headers).json()
        resp = client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"text": text},
            headers=headers,
        ).json()
        assert resp["conversation_status"] == "active"
        assert expected_snippet.lower() in resp["assistant_message"]["text"].lower()


def test_greeting_prefix_with_real_question_still_routes_to_knowledge_base() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/chat/conversations", json={}, headers=headers).json()

    resp = client.post(
        f"/api/chat/conversations/{conv['id']}/messages",
        json={"text": "hi, my inverter is showing an E02 error code"},
        headers=headers,
    ).json()
    assert resp["conversation_status"] == "active"
    assert resp["assistant_message"]["is_grounded"] is True
    assert len(resp["assistant_message"]["citations"]) > 0


def test_stream_endpoint_handles_greeting_without_handoff() -> None:
    import json

    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/chat/conversations", json={}, headers=headers).json()

    with client.stream(
        "POST",
        f"/api/chat/conversations/{conv['id']}/messages/stream",
        json={"text": "hello"},
        headers=headers,
    ) as resp:
        raw = "".join(resp.iter_text())

    events = []
    for block in raw.strip().split("\n\n"):
        event_name = "message"
        data = ""
        for line in block.splitlines():
            if line.startswith("event:"):
                event_name = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data = line.removeprefix("data:").strip()
        if data:
            events.append((event_name, data))

    event_names = [name for name, _ in events]
    assert "handoff" not in event_names
    done_payload = json.loads(next(data for name, data in events if name == "done"))
    assert done_payload["conversation_status"] == "active"
