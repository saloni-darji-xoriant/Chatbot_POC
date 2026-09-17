from app.services.knowledge_base import KNOWLEDGE_BASE, search
from app.services.knowledge_graph import get_graph
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login() -> str:
    resp = client.post(
        "/api/auth/login",
        json={"email": "jordan.reyes@installer.qcells.com", "password": "installer123"},
    )
    return resp.json()["token"]


def test_knowledge_base_covers_all_three_content_categories() -> None:
    categories = {entry.category for entry in KNOWLEDGE_BASE}
    assert "Solar System" in categories
    assert "Case Ticket" in categories
    assert "Installer FAQ" in categories
    # A meaningful KB, not just the original half-dozen entries.
    assert len(KNOWLEDGE_BASE) >= 30


def test_every_kb_entry_has_a_non_empty_graph() -> None:
    for entry in KNOWLEDGE_BASE:
        graph = get_graph(entry)
        assert graph is not None
        assert len(graph.nodes) > 0


def test_case_ticket_query_resolves_to_the_specific_case_not_generic_faq() -> None:
    entry, score = search("Two panels are showing near-zero output after a hailstorm")
    assert entry is not None
    assert entry.category == "Case Ticket"
    assert "Q-10287" in entry.title


def test_solar_system_spec_query_resolves_to_product_catalog_entry() -> None:
    entry, score = search("What's the usable capacity of the Q.HOME ESS battery?")
    assert entry is not None
    assert entry.category == "Solar System"


def test_seeded_history_spans_multiple_users_and_a_handoff_case() -> None:
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    history = client.get("/api/chat", headers=headers).json()
    assert len(history) >= 5

    admin_token_resp = client.post(
        "/api/auth/login", json={"email": "casey.kim@qcells.com", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_token_resp.json()['token']}"}
    all_convs = client.get("/api/admin/conversations", headers=admin_headers).json()
    assert any(c["status"] == "handoff" for c in all_convs)
    assert any(c["status"] == "resolved" for c in all_convs)


def test_documents_list_is_derived_from_kb_citations() -> None:
    token = _login()
    admin_token_resp = client.post(
        "/api/auth/login", json={"email": "casey.kim@qcells.com", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_token_resp.json()['token']}"}
    docs = client.get("/api/admin/documents", headers=admin_headers).json()
    filenames = {d["filename"] for d in docs}
    assert "QPEAK-DUO-BLK-Datasheet.pdf" in filenames
    assert "Case-Q-10287.md" in filenames
    assert len(docs) >= 15
