"""A small, static mock knowledge graph for the Hanwha Qcells L1 Assistant POC.

Each topic (matching a `KBEntry.topic` in knowledge_base.py) maps to a subgraph
of Topic -> Document -> Entity nodes. In a real system this would be backed by
a graph database (e.g. Neo4j/Amazon Neptune) populated by an ingestion
pipeline; here it's hand-authored so the Retrieval Agent has something
concrete to "retrieve" and the admin UI has something real to visualize per
conversation.
"""

from __future__ import annotations

from app.models import KGEdge, KGNode, KnowledgeGraph

_GRAPH_DATA: dict[str, dict] = {
    "inverter_fault": {
        "nodes": [
            {"id": "topic_inverter_fault", "label": "Inverter Fault Codes", "type": "topic"},
            {"id": "doc_qhome_manual", "label": "QHOME-ESS-Install-Guide.pdf", "type": "document"},
            {"id": "doc_inverter_ts", "label": "Inverter-Troubleshooting.md", "type": "document"},
            {"id": "entity_fault_codes", "label": "E01 / E02 Fault Codes", "type": "entity"},
            {"id": "entity_power_cycle", "label": "Power Cycle Procedure", "type": "entity"},
        ],
        "edges": [
            {"source": "topic_inverter_fault", "target": "doc_qhome_manual", "relation": "DOCUMENTED_IN"},
            {"source": "topic_inverter_fault", "target": "doc_inverter_ts", "relation": "DOCUMENTED_IN"},
            {"source": "topic_inverter_fault", "target": "entity_fault_codes", "relation": "INCLUDES"},
            {"source": "entity_fault_codes", "target": "entity_power_cycle", "relation": "RESOLVED_BY"},
        ],
    },
    "panel_output": {
        "nodes": [
            {"id": "topic_panel_output", "label": "Panel Output & Performance", "type": "topic"},
            {"id": "doc_qtron_perf", "label": "QTRON-Performance-Guide.pdf", "type": "document"},
            {"id": "entity_rapid_shutdown", "label": "Rapid Shutdown Switch", "type": "entity"},
            {"id": "entity_shading", "label": "Shading / Soiling", "type": "entity"},
        ],
        "edges": [
            {"source": "topic_panel_output", "target": "doc_qtron_perf", "relation": "DOCUMENTED_IN"},
            {"source": "topic_panel_output", "target": "entity_rapid_shutdown", "relation": "INCLUDES"},
            {"source": "topic_panel_output", "target": "entity_shading", "relation": "INCLUDES"},
        ],
    },
    "monitoring_portal": {
        "nodes": [
            {"id": "topic_monitoring_portal", "label": "Monitoring Portal Access", "type": "topic"},
            {"id": "doc_portal_faq", "label": "Monitoring-Portal-FAQ.md", "type": "document"},
            {"id": "entity_password_reset", "label": "Password Reset Flow", "type": "entity"},
            {"id": "entity_account_lockout", "label": "Account Lockout Policy", "type": "entity"},
        ],
        "edges": [
            {"source": "topic_monitoring_portal", "target": "doc_portal_faq", "relation": "DOCUMENTED_IN"},
            {"source": "topic_monitoring_portal", "target": "entity_password_reset", "relation": "INCLUDES"},
            {"source": "topic_monitoring_portal", "target": "entity_account_lockout", "relation": "INCLUDES"},
        ],
    },
    "warranty": {
        "nodes": [
            {"id": "topic_warranty", "label": "Warranty Claims", "type": "topic"},
            {"id": "doc_warranty_terms", "label": "Qcells-Warranty-Terms.pdf", "type": "document"},
            {"id": "entity_panel_warranty", "label": "25-yr Panel Warranty", "type": "entity"},
            {"id": "entity_inverter_warranty", "label": "12-yr Inverter Warranty", "type": "entity"},
        ],
        "edges": [
            {"source": "topic_warranty", "target": "doc_warranty_terms", "relation": "DOCUMENTED_IN"},
            {"source": "topic_warranty", "target": "entity_panel_warranty", "relation": "INCLUDES"},
            {"source": "topic_warranty", "target": "entity_inverter_warranty", "relation": "INCLUDES"},
        ],
    },
    "firmware": {
        "nodes": [
            {"id": "topic_firmware", "label": "Firmware Updates", "type": "topic"},
            {"id": "doc_firmware_guide", "label": "Firmware-Update-Guide.md", "type": "document"},
            {"id": "entity_auto_update", "label": "Automatic Update Trigger", "type": "entity"},
        ],
        "edges": [
            {"source": "topic_firmware", "target": "doc_firmware_guide", "relation": "DOCUMENTED_IN"},
            {"source": "topic_firmware", "target": "entity_auto_update", "relation": "INCLUDES"},
        ],
    },
    "installation": {
        "nodes": [
            {"id": "topic_installation", "label": "Residential Installation", "type": "topic"},
            {"id": "doc_install_guide", "label": "Residential-Install-Guide.pdf", "type": "document"},
            {"id": "entity_racking", "label": "Racking & Mounting", "type": "entity"},
            {"id": "entity_commissioning", "label": "Commissioning Checklist", "type": "entity"},
        ],
        "edges": [
            {"source": "topic_installation", "target": "doc_install_guide", "relation": "DOCUMENTED_IN"},
            {"source": "topic_installation", "target": "entity_racking", "relation": "INCLUDES"},
            {"source": "topic_installation", "target": "entity_commissioning", "relation": "INCLUDES"},
        ],
    },
}


def _graph_from_data(data: dict) -> KnowledgeGraph:
    return KnowledgeGraph(
        nodes=[KGNode(**n) for n in data["nodes"]],
        edges=[KGEdge(**e) for e in data["edges"]],
    )


def _auto_graph(entry) -> KnowledgeGraph:
    """Build a subgraph on the fly from a KB entry's own metadata (its
    citations become document nodes, a few of its keywords become entity
    nodes) for any topic that doesn't have a hand-curated graph above. A real
    ingestion pipeline would do this at index time; here it happens at
    lookup time since the KB itself is small and static."""
    topic_id = f"topic_{entry.topic}"
    nodes = [{"id": topic_id, "label": entry.title, "type": "topic"}]
    edges: list[dict] = []

    for i, citation in enumerate(entry.citations):
        doc_id = f"doc_{entry.topic}_{i}"
        nodes.append({"id": doc_id, "label": citation["document"], "type": "document"})
        edges.append({"source": topic_id, "target": doc_id, "relation": "DOCUMENTED_IN"})

    for i, keyword in enumerate(entry.keywords[:3]):
        entity_id = f"entity_{entry.topic}_{i}"
        nodes.append({"id": entity_id, "label": keyword.title(), "type": "entity"})
        edges.append({"source": topic_id, "target": entity_id, "relation": "INCLUDES"})

    return _graph_from_data({"nodes": nodes, "edges": edges})


def get_graph(entry) -> KnowledgeGraph | None:
    """Look up the knowledge graph for a matched KB entry — a hand-curated
    one if this topic has one, otherwise an auto-generated one built from
    the entry's own citations/keywords so every entry has something to show."""
    if entry is None:
        return None
    if entry.topic in _GRAPH_DATA:
        return _graph_from_data(_GRAPH_DATA[entry.topic])
    return _auto_graph(entry)


def register_correction_node(topic: str, label: str) -> None:
    """Attach an admin-supplied correction as a new entity node on a topic's
    subgraph, so the graph itself reflects what was learned from feedback."""
    graph = _GRAPH_DATA.setdefault(
        topic,
        {"nodes": [{"id": f"topic_{topic}", "label": topic.replace("_", " ").title(), "type": "topic"}], "edges": []},
    )
    node_id = f"entity_correction_{len(graph['nodes'])}"
    graph["nodes"].append({"id": node_id, "label": label, "type": "correction"})
    graph["edges"].append({"source": graph["nodes"][0]["id"], "target": node_id, "relation": "CORRECTED_BY"})
