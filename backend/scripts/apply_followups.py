"""One-off migration: replace legacy `quick_replies` in the KB JSON files with
curated, routed `follow_ups` ({question, topic}) and attach diagram `images`.

Every follow-up targets a *different* existing topic so clicking it always
lands on a real answer (never a repeat, never a handoff)."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "app" / "data"
SOURCES = ["solar_systems", "case_tickets", "installer_queries", "reference_guides"]

# slug -> (caption, alt)
IMAGES = {
    "power-cycle-procedure": ("Power-cycle procedure timeline", "Safe inverter power-cycle order: AC off, wait 60 s, DC off, wait 60 s, then AC on, DC on."),
    "inverter-error-codes": ("Q.VOLT inverter error code quick reference", "Common error codes and whether an installer can clear them or L2 must be involved."),
    "rapid-shutdown-layout": ("Rapid shutdown layout", "Where the RSD initiator sits and what gets de-energized within the required boundary."),
    "installation-sequence": ("Standard residential installation sequence", "The installation steps in order, from site survey to commissioning."),
    "battery-clearances": ("Battery installation clearances", "Required working space and clearances around a wall-mounted battery."),
    "escalation-flow": ("When to escalate to L2", "Decision flow: try the documented fix once, then escalate with the required details."),
    "grounding-bonding": ("Grounding and bonding overview", "Module frames bonded to the racking, with one continuous EGC to the inverter."),
    "panel-troubleshooting-flow": ("Low panel output troubleshooting flow", "Step-by-step flow from symptom to likely cause and action."),
    "monitoring-connectivity": ("Monitoring connectivity path", "How the inverter, router, cloud and the portal connect - check each hop in order."),
    "shading-clearance": ("Shading clearance rule of thumb", "Keep obstructions more than 2 x h away east/west and 0.5 x h south of the array."),
    "pv-system-components": ("Solar PV building blocks", "Cell, module, panel, array, then FJB, charge controller, battery and load."),
}
TOPIC_IMAGE = {
    "inverter_fault": "power-cycle-procedure",
    "error_code_reference": "inverter-error-codes",
    "case_rodent_arc_fault": "inverter-error-codes",
    "rapid_shutdown": "rapid-shutdown-layout",
    "case_rsd_inspection_fail": "rapid-shutdown-layout",
    "installation": "installation-sequence",
    "battery_safety": "battery-clearances",
    "qhome_battery": "battery-clearances",
    "escalation_process": "escalation-flow",
    "grounding_bonding": "grounding-bonding",
    "panel_output": "panel-troubleshooting-flow",
    "spv_troubleshooting_reference_table": "panel-troubleshooting-flow",
    "monitoring_portal": "monitoring-connectivity",
    "case_wifi_offline": "monitoring-connectivity",
    "qommand_platform": "monitoring-connectivity",
    "panel_siting_reference": "shading-clearance",
    "case_shading_underperformance": "shading-clearance",
    "spv_system_components_reference": "pv-system-components",
}

ESC = ("How do I escalate this to L2?", "escalation_process")

F = {
    # --- installer FAQ
    "inverter_fault": [("What does each inverter error code mean?", "error_code_reference"), ("When should I escalate an inverter fault to L2?", "escalation_process"), ("How do I push a firmware update to the inverter?", "firmware")],
    "panel_output": [("How do I check production in the monitoring portal?", "monitoring_portal"), ("Could shading be causing the low output?", "panel_siting_reference"), ("When should I escalate low output to L2?", "escalation_process")],
    "monitoring_portal": [("The system shows offline after a router change - what now?", "case_wifi_offline"), ("How do I set up underperformance alerts?", "qommand_platform"), ("When should I escalate a portal problem to L2?", "escalation_process")],
    "warranty": [("What is the standard installation sequence?", "installation"), ("Could cleaning have voided my panels' warranty?", "case_warranty_denied"), ("When should I escalate a warranty claim to L2?", "escalation_process")],
    "firmware": [("What if the firmware update is stuck at 40%?", "case_firmware_stuck"), ("What do the inverter error codes mean?", "error_code_reference"), ("When should I escalate a firmware issue to L2?", "escalation_process")],
    "installation": [("What are the grounding and bonding requirements?", "grounding_bonding"), ("What are the rapid shutdown requirements?", "rapid_shutdown"), ("Which permit and inspection documents do I need?", "permits_inspection")],
    "rapid_shutdown": [("Why did a rapid shutdown fail inspection?", "case_rsd_inspection_fail"), ("Which permit and inspection documents do I need?", "permits_inspection"), ("What are the grounding and bonding requirements?", "grounding_bonding")],
    "battery_safety": [("What are the Q.HOME ESS battery specifications?", "qhome_battery"), ("What if the battery is stuck at 20% charge?", "case_battery_bms_bug"), ("When should I escalate a battery issue to L2?", "escalation_process")],
    "permits_inspection": [("What are the rapid shutdown requirements?", "rapid_shutdown"), ("What are the grounding and bonding requirements?", "grounding_bonding"), ("How is system sizing and net metering handled?", "system_sizing")],
    "error_code_reference": [("How do I power-cycle the inverter safely?", "inverter_fault"), ("What if the inverter keeps shutting down with a grid fault?", "case_grid_fault_recurring"), ("When should I escalate an error code to L2?", "escalation_process")],
    "grounding_bonding": [("What is the standard installation sequence?", "installation"), ("What are the rapid shutdown requirements?", "rapid_shutdown"), ("What do the inverter error codes mean?", "error_code_reference")],
    "escalation_process": [("Which details should I collect before escalating?", "inverter_fault"), ("What if there is a burning smell near the inverter?", "case_burning_smell"), ("How do I file a warranty claim?", "warranty")],
    # --- case tickets
    "case_grid_fault_recurring": [("How do I power-cycle the inverter safely?", "inverter_fault"), ("What do the inverter error codes mean?", "error_code_reference"), ESC],
    "case_hail_microcrack": [("How do I file a warranty claim for damaged panels?", "warranty"), ("Could damaged panels be lowering output?", "panel_output"), ESC],
    "case_wifi_offline": [("How do I sign in to the monitoring portal?", "monitoring_portal"), ("How do I set up underperformance alerts?", "qommand_platform"), ESC],
    "case_battery_bms_bug": [("What are the battery installation clearances?", "battery_safety"), ("What are the Q.HOME ESS specifications?", "qhome_battery"), ("How do I file a warranty claim?", "warranty")],
    "case_rsd_inspection_fail": [("What are the rapid shutdown requirements?", "rapid_shutdown"), ("Which permit and inspection documents do I need?", "permits_inspection"), ESC],
    "case_rodent_arc_fault": [("What do the inverter error codes mean?", "error_code_reference"), ("What are the grounding and bonding requirements?", "grounding_bonding"), ESC],
    "case_shading_underperformance": [("What are the panel siting and shading clearance rules?", "panel_siting_reference"), ("How do I check production in the monitoring portal?", "monitoring_portal"), ("How do I diagnose low panel output?", "panel_output")],
    "case_firmware_stuck": [("How do I push a firmware update correctly?", "firmware"), ("How do I power-cycle the inverter safely?", "inverter_fault"), ESC],
    "case_serial_not_found": [("How do I file a warranty claim?", "warranty"), ("What is the standard installation sequence?", "installation"), ESC],
    "case_burning_smell": [ESC, ("What do the inverter error codes mean?", "error_code_reference"), ("What are the grounding and bonding requirements?", "grounding_bonding")],
    "case_warranty_denied": [("How do I file a warranty claim correctly?", "warranty"), ("How often should panels be cleaned?", "spv_maintenance_cadence_reference"), ESC],
    "case_itc_financing_question": [("How is system sizing and net metering handled?", "system_sizing"), ("Which permit and inspection documents do I need?", "permits_inspection"), ESC],
    # --- reference guides
    "spv_system_components_reference": [("How should panels be sited to avoid shading?", "panel_siting_reference"), ("How often should panels be cleaned and maintained?", "spv_maintenance_cadence_reference"), ("What happens to excess solar energy with a battery?", "battery_storage_homeowner_reference")],
    "panel_siting_reference": [("What if my system underperforms because of shading?", "case_shading_underperformance"), ("Does solar still work on cloudy days?", "cloudy_day_output_reference"), ("How is system sizing handled?", "system_sizing")],
    "spv_maintenance_cadence_reference": [("Could cleaning damage my warranty?", "case_warranty_denied"), ("What does general troubleshooting look like?", "spv_troubleshooting_reference_table"), ("How do I diagnose low panel output?", "panel_output")],
    "spv_troubleshooting_reference_table": [("How do I diagnose low panel output step by step?", "panel_output"), ("What do the inverter error codes mean?", "error_code_reference"), ("When should I escalate to L2?", "escalation_process")],
    "battery_storage_homeowner_reference": [("What are the Q.HOME ESS battery specifications?", "qhome_battery"), ("What are the battery installation clearances?", "battery_safety"), ("How is system sizing handled with a battery?", "system_sizing")],
    "cloudy_day_output_reference": [("How should panels be sited for best output?", "panel_siting_reference"), ("How is system sizing handled?", "system_sizing"), ("How do I check production in the monitoring portal?", "monitoring_portal")],
    "choosing_installer_reference": [("What is the standard installation sequence?", "installation"), ("Which permit and inspection documents are required?", "permits_inspection"), ("How do I file a warranty claim?", "warranty")],
    # --- solar systems
    "qpeak_panel": [("How does Q.TRON compare?", "qtron_panel"), ("What racking is compatible?", "racking_mounting"), ("How do I file a warranty claim?", "warranty")],
    "qtron_panel": [("What are the Q.PEAK DUO specifications?", "qpeak_panel"), ("What racking is compatible?", "racking_mounting"), ("How do I file a warranty claim?", "warranty")],
    "qhome_battery": [("What are the battery installation clearances?", "battery_safety"), ("What if the battery is stuck at 20% charge?", "case_battery_bms_bug"), ("Which hybrid inverter pairs with it?", "qvolt_hybrid_inverter")],
    "qvolt_hybrid_inverter": [("What do the inverter error codes mean?", "error_code_reference"), ("How do I push a firmware update?", "firmware"), ("What are the Q.HOME ESS battery specifications?", "qhome_battery")],
    "qvolt_string_inverter": [("What do the inverter error codes mean?", "error_code_reference"), ("How does the hybrid inverter differ?", "qvolt_hybrid_inverter"), ("How do I power-cycle the inverter safely?", "inverter_fault")],
    "racking_mounting": [("What are the grounding and bonding requirements?", "grounding_bonding"), ("What is the standard installation sequence?", "installation"), ("Which permit documents do I need?", "permits_inspection")],
    "qommand_platform": [("How do I sign in and fix portal lockouts?", "monitoring_portal"), ("What if the system shows offline?", "case_wifi_offline"), ("How do I diagnose low panel output?", "panel_output")],
    "system_sizing": [("Which permit and inspection documents do I need?", "permits_inspection"), ("What are the Q.HOME ESS battery specifications?", "qhome_battery"), ("What are the Q.PEAK DUO panel specifications?", "qpeak_panel")],
}

all_topics: set[str] = set()
for name in SOURCES:
    all_topics |= {r["topic"] for r in json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))}
assert not (all_topics - set(F)), all_topics - set(F)
for topic, follow_ups in F.items():
    assert topic in all_topics, topic
    for _q, target in follow_ups:
        assert target in all_topics and target != topic, (topic, target)

for name in SOURCES:
    path = DATA / f"{name}.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    for r in records:
        r.pop("quick_replies", None)
        r["follow_ups"] = [{"question": q, "topic": t} for q, t in F[r["topic"]]]
        slug = TOPIC_IMAGE.get(r["topic"])
        if slug:
            caption, alt = IMAGES[slug]
            r["images"] = [{"url": f"/static/kb-images/{slug}.png", "alt": alt, "caption": caption}]
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("migrated")
