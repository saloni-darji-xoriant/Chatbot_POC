from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(email: str = "jordan.reyes@installer.qcells.com", password: str = "installer123") -> str:
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["token"]


def _admin_token() -> str:
    return _login("casey.kim@qcells.com", "admin123")


def _parse_sse(raw_text: str) -> list[tuple[str, str]]:
    events = []
    for block in raw_text.strip().split("\n\n"):
        event_name = "message"
        data = ""
        for line in block.splitlines():
            if line.startswith("event:"):
                event_name = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data = line.removeprefix("data:").strip()
        if data:
            events.append((event_name, data))
    return events


def test_stream_endpoint_emits_full_pipeline_for_grounded_query() -> None:
    import json

    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/chat/conversations", json={}, headers=headers).json()

    with client.stream(
        "POST",
        f"/api/chat/conversations/{conv['id']}/messages/stream",
        json={"text": "my inverter shows an E02 error code"},
        headers=headers,
    ) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        raw = "".join(resp.iter_text())

    events = _parse_sse(raw)
    event_names = [name for name, _ in events]
    assert "user_message" in event_names
    assert "trace" in event_names
    assert "assistant_message" in event_names
    assert "done" in event_names

    trace_events = [json.loads(data) for name, data in events if name == "trace"]
    agents = {step["agent"] for step in trace_events[-1]["steps"]}
    assert agents == {"Router Agent", "Retrieval Agent (RAG)", "Response Agent", "Grounding Agent"}

    assistant_payload = json.loads(next(data for name, data in events if name == "assistant_message"))
    assert assistant_payload["is_grounded"] is True
    assert assistant_payload["knowledge_graph"]["nodes"]

    done_payload = json.loads(next(data for name, data in events if name == "done"))
    assert done_payload["conversation_status"] == "active"


def test_stream_endpoint_emits_handoff_for_human_request() -> None:
    import json

    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/chat/conversations", json={}, headers=headers).json()

    with client.stream(
        "POST",
        f"/api/chat/conversations/{conv['id']}/messages/stream",
        json={"text": "zzz can I talk to a human please zzz"},
        headers=headers,
    ) as resp:
        raw = "".join(resp.iter_text())

    events = _parse_sse(raw)
    event_names = [name for name, _ in events]
    assert "handoff" in event_names
    done_payload = json.loads(next(data for name, data in events if name == "done"))
    assert done_payload["conversation_status"] == "handoff"


def test_thumbs_down_vote_with_reason_creates_admin_feedback() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/chat/conversations", json={}, headers=headers).json()
    send = client.post(
        f"/api/chat/conversations/{conv['id']}/messages",
        json={"text": "how do I file a warranty claim"},
        headers=headers,
    ).json()
    message_id = send["assistant_message"]["id"]

    vote_resp = client.post(
        f"/api/chat/messages/{message_id}/vote",
        json={"vote": "down", "reason": "Didn't mention the claim portal URL"},
        headers=headers,
    )
    assert vote_resp.status_code == 200
    assert vote_resp.json()["vote"] == "down"
    assert vote_resp.json()["vote_reason"] == "Didn't mention the claim portal URL"

    admin_headers = {"Authorization": f"Bearer {_admin_token()}"}
    feedback = client.get("/api/admin/feedback", headers=admin_headers).json()
    matching = [f for f in feedback if f["message_id"] == message_id]
    assert len(matching) == 1
    assert matching[0]["comment"] == "Didn't mention the claim portal URL"


def test_admin_can_add_correction_to_negative_feedback() -> None:
    admin_headers = {"Authorization": f"Bearer {_admin_token()}"}
    feedback = client.get("/api/admin/feedback", headers=admin_headers).json()
    negative = next(f for f in feedback if f["sentiment"] == "down" and f["correction"] is None)

    resp = client.post(
        f"/api/admin/feedback/{negative['id']}/correction",
        json={
            "text": "Also check for storm/hail damage before the standard low-output steps.",
            "document_filename": "storm-damage-addendum.md",
            "add_as_document": True,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["correction"]["text"].startswith("Also check for storm")

    docs = client.get("/api/admin/documents", headers=admin_headers).json()
    assert any(d["filename"] == "storm-damage-addendum.md" for d in docs)

    # The correction should now let a similar future query resolve directly.
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/chat/conversations", json={}, headers=headers).json()
    followup = client.post(
        f"/api/chat/conversations/{conv['id']}/messages",
        json={"text": negative["query"]},
        headers=headers,
    ).json()
    assert followup["assistant_message"]["is_grounded"] is True


def test_admin_can_list_and_fetch_any_conversation() -> None:
    admin_headers = {"Authorization": f"Bearer {_admin_token()}"}
    convs = client.get("/api/admin/conversations", headers=admin_headers).json()
    assert len(convs) > 0
    detail = client.get(f"/api/admin/conversations/{convs[0]['id']}", headers=admin_headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == convs[0]["id"]


def test_help_contacts_endpoint() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/chat/help-contacts", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 4


def test_conversation_history_lists_titles_and_previews() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    history = client.get("/api/chat", headers=headers)
    assert history.status_code == 200
    body = history.json()
    assert len(body) > 0
    assert "last_message_preview" in body[0]
