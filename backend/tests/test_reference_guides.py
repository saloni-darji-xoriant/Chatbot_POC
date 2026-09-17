"""Locks in the "Reference Guide" KB category — general solar PV content
distilled from two real source documents (a CAMTECH/Indian Railways
installation & maintenance handbook, and SEAI's "A Homeowner's Guide to
Solar PV") so a random installer/homeowner question can be answered without
needing a Qcells-specific product match or falling through to a handoff."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.knowledge_base import KNOWLEDGE_BASE, search

client = TestClient(app)


def _login() -> str:
    resp = client.post(
        "/api/auth/login",
        json={"email": "jordan.reyes@installer.qcells.com", "password": "installer123"},
    )
    return resp.json()["token"]


def test_reference_guide_category_is_loaded() -> None:
    reference_entries = [e for e in KNOWLEDGE_BASE if e.category == "Reference Guide"]
    assert len(reference_entries) == 7
    documents = {c["document"] for e in reference_entries for c in e.citations}
    assert documents == {"Handbook-Solar-Panel-Install-Maintenance.pdf", "Homeowners-Guide-To-Solar-PV.pdf"}


def test_random_homeowner_style_queries_resolve_from_reference_guides() -> None:
    queries_and_topics = [
        ("What is the difference between a solar cell, module, and panel?", "spv_system_components_reference"),
        ("How much clearance do I need from a tree to avoid shading my panels?", "panel_siting_reference"),
        ("How often should I clean my solar panels?", "spv_maintenance_cadence_reference"),
        ("My panel shows no charging indication, what should I check?", "spv_troubleshooting_reference_table"),
        ("Should I add a battery to my solar system or use a diverter switch instead?", "battery_storage_homeowner_reference"),
        ("Does solar still generate power on a cloudy day?", "cloudy_day_output_reference"),
        ("What questions should I ask before hiring a solar installer?", "choosing_installer_reference"),
    ]
    for query, expected_topic in queries_and_topics:
        entry, score = search(query)
        assert entry is not None, f"expected a match for {query!r}"
        assert entry.topic == expected_topic, f"{query!r} matched {entry.topic}, expected {expected_topic}"


def test_random_query_answered_via_chat_endpoint_without_handoff() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/chat/conversations", json={}, headers=headers).json()

    resp = client.post(
        f"/api/chat/conversations/{conv['id']}/messages",
        json={"text": "Does solar still generate power on a cloudy day?"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["conversation_status"] == "active"
    assistant = body["assistant_message"]
    assert assistant["is_grounded"] is True
    assert any(c["document"] == "Homeowners-Guide-To-Solar-PV.pdf" for c in assistant["citations"])


def test_reference_documents_appear_in_admin_documents_with_correct_category() -> None:
    admin_token = client.post(
        "/api/auth/login", json={"email": "casey.kim@qcells.com", "password": "admin123"}
    ).json()["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    docs = client.get("/api/admin/documents", headers=headers).json()

    by_filename = {d["filename"]: d for d in docs}
    assert by_filename["Handbook-Solar-Panel-Install-Maintenance.pdf"]["category"] == "Reference Guide"
    assert by_filename["Homeowners-Guide-To-Solar-PV.pdf"]["category"] == "Reference Guide"
