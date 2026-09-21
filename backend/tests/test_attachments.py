import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login() -> str:
    resp = client.post(
        "/api/auth/login",
        json={"email": "jordan.reyes@installer.qcells.com", "password": "installer123"},
    )
    return resp.json()["token"]


def _new_conversation(headers: dict) -> str:
    return client.post("/api/chat/conversations", json={}, headers=headers).json()["id"]


def test_upload_text_attachment_and_reference_it_in_chat() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv_id = _new_conversation(headers)

    file_content = (
        b"Site Survey Notes\n\n"
        b"The array at 42 Solar Lane uses a Q.PEAK DUO BLK ML-G10+ panel array "
        b"with a known shading issue from a neighboring oak tree between 3pm and 5pm."
    )
    upload = client.post(
        f"/api/chat/conversations/{conv_id}/attachments",
        files={"file": ("site-survey.txt", io.BytesIO(file_content), "text/plain")},
        headers=headers,
    )
    assert upload.status_code == 200
    body = upload.json()
    assert body["filename"] == "site-survey.txt"
    assert body["kind"] == "document"
    assert body["has_extracted_text"] is True
    assert "Site Survey" in body["preview"]

    # A question whose only real answer lives in the attachment (not the KB)
    # should now resolve directly instead of escalating.
    send = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"text": "What shading issue was noted at 42 Solar Lane?", "attachment_ids": [body["id"]]},
        headers=headers,
    )
    assert send.status_code == 200
    result = send.json()
    assert result["conversation_status"] == "active"
    assistant = result["assistant_message"]
    assert assistant["is_grounded"] is True
    assert "oak tree" in assistant["text"]
    assert any(c["document"] == "site-survey.txt" for c in assistant["citations"])
    agents = {step["agent"] for step in assistant["process_trace"]}
    assert "Document Agent" in agents

    # The user message should carry the attachment metadata for display.
    assert len(result["user_message"]["attachments"]) == 1
    assert result["user_message"]["attachments"][0]["filename"] == "site-survey.txt"


def test_image_attachment_gets_metadata_not_fake_vision_claims() -> None:
    from PIL import Image

    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv_id = _new_conversation(headers)

    buf = io.BytesIO()
    Image.new("RGB", (100, 50), color="red").save(buf, format="PNG")
    buf.seek(0)

    upload = client.post(
        f"/api/chat/conversations/{conv_id}/attachments",
        files={"file": ("panel-photo.png", buf, "image/png")},
        headers=headers,
    )
    assert upload.status_code == 200
    body = upload.json()
    assert body["kind"] == "image"
    assert body["has_extracted_text"] is False
    assert "100x50" in body["extraction_note"]


def test_attachment_over_size_limit_is_rejected() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv_id = _new_conversation(headers)

    oversized = b"x" * (5 * 1024 * 1024 + 1)
    resp = client.post(
        f"/api/chat/conversations/{conv_id}/attachments",
        files={"file": ("big.txt", io.BytesIO(oversized), "text/plain")},
        headers=headers,
    )
    assert resp.status_code == 413


def test_attachments_persist_across_messages_in_the_same_conversation() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv_id = _new_conversation(headers)

    client.post(
        f"/api/chat/conversations/{conv_id}/attachments",
        files={"file": ("notes.txt", io.BytesIO(b"The backup generator model is Honda EU2200i."), "text/plain")},
        headers=headers,
    )

    # First message doesn't even reference the attachment by id — the
    # pipeline should still find it because it's remembered for the whole
    # conversation, not just the message it was uploaded alongside.
    resp = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"text": "What is the backup generator model?"},
        headers=headers,
    )
    assistant = resp.json()["assistant_message"]
    assert assistant["is_grounded"] is True
    assert "Honda EU2200i" in assistant["text"]


def test_list_and_delete_attachments() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv_id = _new_conversation(headers)

    upload = client.post(
        f"/api/chat/conversations/{conv_id}/attachments",
        files={"file": ("a.txt", io.BytesIO(b"hello"), "text/plain")},
        headers=headers,
    )
    attachment_id = upload.json()["id"]

    listed = client.get(f"/api/chat/conversations/{conv_id}/attachments", headers=headers)
    assert len(listed.json()) == 1

    deleted = client.delete(f"/api/chat/conversations/{conv_id}/attachments/{attachment_id}", headers=headers)
    assert deleted.status_code == 204

    listed_after = client.get(f"/api/chat/conversations/{conv_id}/attachments", headers=headers)
    assert len(listed_after.json()) == 0


def test_unsupported_query_with_no_attachment_match_still_hands_off() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv_id = _new_conversation(headers)

    client.post(
        f"/api/chat/conversations/{conv_id}/attachments",
        files={"file": ("notes.txt", io.BytesIO(b"The backup generator model is Honda EU2200i."), "text/plain")},
        headers=headers,
    )

    resp = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"text": "Do you offer gift cards for referrals? Connect me to a live agent."},
        headers=headers,
    )
    result = resp.json()
    assert result["conversation_status"] == "handoff"
    assert result["assistant_message"]["is_grounded"] is False
