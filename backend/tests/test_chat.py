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


def test_health() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_login_success() -> None:
    resp = client.post(
        "/api/auth/login",
        json={"email": "jordan.reyes@installer.qcells.com", "password": "installer123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["role"] == "installer"
    assert body["token"].startswith("token_")


def test_login_failure() -> None:
    resp = client.post(
        "/api/auth/login",
        json={"email": "jordan.reyes@installer.qcells.com", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_grounded_answer_flow() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}

    conv = client.post("/api/chat/conversations", json={}, headers=headers).json()
    resp = client.post(
        f"/api/chat/conversations/{conv['id']}/messages",
        json={"text": "My inverter is showing an E02 error code"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["conversation_status"] == "active"
    assert body["assistant_message"]["is_grounded"] is True
    assert len(body["assistant_message"]["citations"]) > 0


def test_explicit_human_request_triggers_handoff() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}

    conv = client.post("/api/chat/conversations", json={}, headers=headers).json()
    resp = client.post(
        f"/api/chat/conversations/{conv['id']}/messages",
        json={"text": "asdkjaslkdj please connect me to a live specialist"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["conversation_status"] == "handoff"
    assert body["assistant_message"]["is_grounded"] is False


def test_admin_endpoints_require_admin_role() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/admin/dashboard", headers=headers)
    assert resp.status_code == 403


def test_admin_dashboard_accessible_to_admin() -> None:
    resp = client.post(
        "/api/auth/login", json={"email": "casey.kim@qcells.com", "password": "admin123"}
    )
    token = resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    dash = client.get("/api/admin/dashboard", headers=headers)
    assert dash.status_code == 200
    assert "kpis" in dash.json()
