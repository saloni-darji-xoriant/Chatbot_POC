"""Generates the illustrative diagrams shown alongside chatbot answers.

Run from the backend/ directory:  python scripts/generate_kb_images.py

All artwork is original and drawn programmatically with Pillow (already a
backend dependency), so there are no third-party image licences to worry about
and every diagram can be regenerated or restyled from this one file. Each
diagram restates facts already present in the matching knowledge-base answer
(see app/data/*.json) — it visualises the answer, it doesn't introduce new
claims. Output goes to app/static/kb-images/ and is served at /static/kb-images/.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent.parent / "app" / "static" / "kb-images"
W, H = 1200, 675

NAVY, BLUE, TEAL, RED, AMBER = "#101B36", "#1E6FEB", "#22C3A6", "#D0413B", "#E8A317"
GRAY, LIGHT, BORDER, WHITE = "#66708C", "#F5F8FC", "#D5DDEB", "#FFFFFF"
BLUE_SOFT, TEAL_SOFT, RED_SOFT, AMBER_SOFT = "#E6EFFD", "#E1F6F2", "#FBE8E7", "#FDF1D6"
COPPER = "#B8672B"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.load_default(size=size)


class Canvas:
    def __init__(self, title: str, subtitle: str | None = None) -> None:
        self.img = Image.new("RGB", (W, H), WHITE)
        self.d = ImageDraw.Draw(self.img)
        # Brand gradient bar along the top edge (teal -> blue), like the app's mark.
        for x in range(W):
            t = x / (W - 1)
            r = int(0x22 + (0x1E - 0x22) * t)
            g = int(0xC3 + (0x6F - 0xC3) * t)
            b = int(0xA6 + (0xEB - 0xA6) * t)
            self.d.line([(x, 0), (x, 9)], fill=(r, g, b))
        self.text(48, 34, title, 40, NAVY, bold=True)
        if subtitle:
            self.text(48, 86, subtitle, 24, GRAY)
        self.text(48, H - 38, "Qcells L1 Assistant  |  illustrative diagram", 18, GRAY)

    # -- primitives ---------------------------------------------------------
    def text(self, x, y, s, size, color=NAVY, bold=False, anchor="la") -> None:
        self.d.text((x, y), s, font=font(size), fill=color, anchor=anchor, stroke_width=1 if bold else 0, stroke_fill=color)

    def wrap(self, s: str, size: int, max_w: int) -> list[str]:
        f = font(size)
        lines: list[str] = []
        for para in s.split("\n"):
            cur = ""
            for word in para.split():
                trial = f"{cur} {word}".strip()
                if self.d.textlength(trial, font=f) <= max_w:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = word
            lines.append(cur)
        return lines

    def text_block(self, cx, cy, s, size, color=NAVY, bold=False, max_w=300, line_gap=6) -> None:
        lines = self.wrap(s, size, max_w)
        total = len(lines) * size + (len(lines) - 1) * line_gap
        y = cy - total / 2
        for line in lines:
            self.d.text((cx, y), line, font=font(size), fill=color, anchor="ma", stroke_width=1 if bold else 0, stroke_fill=color)
            y += size + line_gap

    def box(self, x, y, w, h, s, fill=LIGHT, outline=BORDER, color=NAVY, size=26, bold=False, radius=18, width=3) -> None:
        self.d.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill, outline=outline, width=width)
        self.text_block(x + w / 2, y + h / 2, s, size, color, bold, max_w=w - 28)

    def pill(self, cx, cy, s, fill=AMBER_SOFT, color=NAVY, size=22, outline=None) -> None:
        w = self.d.textlength(s, font=font(size)) + 34
        self.d.rounded_rectangle([cx - w / 2, cy - 21, cx + w / 2, cy + 21], radius=21, fill=fill, outline=outline or fill)
        self.d.text((cx, cy), s, font=font(size), fill=color, anchor="mm", stroke_width=1, stroke_fill=color)

    def circle_num(self, cx, cy, n, fill=BLUE) -> None:
        self.d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=fill)
        self.d.text((cx, cy), str(n), font=font(26), fill=WHITE, anchor="mm", stroke_width=1, stroke_fill=WHITE)

    def arrow(self, x1, y1, x2, y2, color=GRAY, width=5, head=16) -> None:
        import math

        self.d.line([(x1, y1), (x2, y2)], fill=color, width=width)
        ang = math.atan2(y2 - y1, x2 - x1)
        for sign in (-1, 1):
            a = ang + math.pi + sign * 0.45
            self.d.polygon(
                [(x2, y2), (x2 + head * math.cos(a), y2 + head * math.sin(a)),
                 (x2 + head * 0.55 * math.cos(ang + math.pi), y2 + head * 0.55 * math.sin(ang + math.pi))],
                fill=color,
            )

    def dashed_rect(self, x0, y0, x1, y1, color=BLUE, width=4, dash=16, gap=10) -> None:
        for (ax, ay, bx, by) in [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]:
            length = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
            n = int(length // (dash + gap)) + 1
            for i in range(n):
                s = i * (dash + gap) / length
                e = min((i * (dash + gap) + dash) / length, 1)
                self.d.line([(ax + (bx - ax) * s, ay + (by - ay) * s), (ax + (bx - ax) * e, ay + (by - ay) * e)], fill=color, width=width)

    def banner(self, y, s, fill=AMBER_SOFT, outline=AMBER, size=25) -> None:
        self.d.rounded_rectangle([48, y, W - 48, y + 70], radius=16, fill=fill, outline=outline, width=3)
        self.text_block(W / 2, y + 35, s, size, NAVY, max_w=W - 130)

    def module_grid(self, x, y, cols, rows, cw=52, ch=34, gap=5, fill=BLUE, outline=NAVY) -> None:
        for r in range(rows):
            for c in range(cols):
                self.d.rectangle([x + c * (cw + gap), y + r * (ch + gap), x + c * (cw + gap) + cw, y + r * (ch + gap) + ch], fill=fill, outline=outline, width=2)

    def save(self, name: str) -> None:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        self.img.save(OUT_DIR / f"{name}.png", optimize=True)
        print("wrote", name)


# ---------------------------------------------------------------------------
def power_cycle_procedure() -> None:
    c = Canvas("Inverter power-cycle procedure", "Try this once before escalating - always in this order")
    steps = [
        ("Switch OFF the AC disconnect", RED_SOFT, RED),
        ("Switch OFF the DC disconnect", RED_SOFT, RED),
        ("Restore AC first", TEAL_SOFT, TEAL),
        ("Then restore DC", TEAL_SOFT, TEAL),
    ]
    bw, bh, gap, x0, y = 230, 190, 76, 26, 220
    for i, (label, fill, edge) in enumerate(steps):
        x = x0 + i * (bw + gap)
        c.box(x, y, bw, bh, label, fill=fill, outline=edge, size=28, bold=True)
        c.circle_num(x + 30, y - 6, i + 1, fill=edge)
        if i < 3:
            c.arrow(x + bw + 8, y + bh / 2, x + bw + gap - 8, y + bh / 2, color=GRAY)
    for i in (0, 1):
        c.pill(x0 + (i + 1) * bw + i * gap + gap / 2, y + bh + 44, "wait 60 s", fill=AMBER_SOFT, outline=AMBER)
    c.banner(H - 170, "Same code back within 10 minutes? Treat it as hardware-related: log the exact code, inverter serial number and a timestamp, then escalate to L2 instead of cycling again.")
    c.save("power-cycle-procedure")


def inverter_error_codes() -> None:
    c = Canvas("Q.VOLT inverter error codes - quick reference", "What each code usually means and the first action to take")
    cols = [("Code", 25, 165), ("Meaning", 190, 360), ("First action", 550, 470), ("Access", 1020, 155)]
    y = 138
    c.d.rounded_rectangle([25, y, 1175, y + 52], radius=12, fill=NAVY)
    for name, x, _w in cols:
        c.text(x + 16, y + 12, name, 24, WHITE, bold=True)
    rows = [
        ("E01 / E02", "Internal communication fault", "Power-cycle (AC then DC); re-check after 10 minutes", "Installer", BLUE_SOFT),
        ("E03", "Grid fault - utility voltage/frequency out of range", "Confirm line voltage with the utility; settings change needs L2", "L2 needed", AMBER_SOFT),
        ("E04", "DC arc fault detected", "De-energize and inspect DC wiring (rodent damage is common)", "Installer, then L2", RED_SOFT),
        ("E05", "Isolation fault", "Inspect connectors for moisture ingress", "Installer", BLUE_SOFT),
        ("E06", "Overtemperature", "Check ventilation clearance around the unit", "Installer", BLUE_SOFT),
    ]
    ry, rh = y + 60, 84
    for code, meaning, action, who, fill in rows:
        c.d.rounded_rectangle([25, ry, 1175, ry + rh - 8], radius=12, fill=fill, outline=BORDER, width=2)
        c.text(cols[0][1] + 16, ry + 22, code, 28, NAVY, bold=True)
        for (name, x, w), text in zip(cols[1:], (meaning, action, who)):
            lines = c.wrap(text, 22, w - 32)
            ty = ry + (rh - 8) / 2 - (len(lines) * 26) / 2
            for line in lines:
                c.text(x + 16, ty, line, 22, NAVY)
                ty += 26
        ry += rh
    c.save("inverter-error-codes")


def rapid_shutdown_layout() -> None:
    c = Canvas("Rapid shutdown (NEC 690.12) - what gets checked", "Initiate at the disconnect, then meter the array")
    # array + boundary
    c.dashed_rect(40, 150, 470, 400, color=BLUE)
    c.text(56, 160, "ARRAY BOUNDARY", 20, BLUE, bold=True)
    c.module_grid(70, 200, 4, 3, cw=76, ch=46)
    c.text(255, 366, "modules with module-level shutdown devices", 18, GRAY, anchor="ma")
    # chain
    c.box(560, 210, 170, 120, "Combiner box", fill=LIGHT, size=26, bold=True)
    c.box(790, 210, 170, 120, "Disconnect / RSD initiator", fill=AMBER_SOFT, outline=AMBER, size=24, bold=True)
    c.box(1010, 210, 150, 120, "Inverter", fill=BLUE_SOFT, outline=BLUE, size=26, bold=True)
    c.arrow(470, 270, 552, 270)
    c.arrow(730, 270, 782, 270)
    c.arrow(960, 270, 1002, 270)
    # limits
    c.box(40, 430, 540, 96, "Inside the array boundary:\n<= 80 V within 30 seconds", fill=BLUE_SOFT, outline=BLUE, size=26, bold=True)
    c.box(620, 430, 540, 96, "Conductors outside the boundary:\n<= 30 V / 240 VA within 30 seconds", fill=TEAL_SOFT, outline=TEAL, size=26, bold=True)
    c.banner(H - 130, "A failed initiation test is almost always a loose transmitter wire at the combiner box, or a device not fully seated behind the module.", size=23)
    c.save("rapid-shutdown-layout")


def installation_sequence() -> None:
    c = Canvas("Standard residential installation sequence", "Complete each stage before moving to the next")
    labels = ["Site survey", "Racking layout per structural plan", "Module mounting", "DC wiring + rapid shutdown", "Inverter install + AC tie-in", "Commissioning checklist", "Homeowner walkthrough"]
    bw, bh = 245, 118
    pos = [(26, 190), (328, 190), (630, 190), (932, 190), (177, 380), (479, 380), (781, 380)]
    for i, ((x, y), label) in enumerate(zip(pos, labels)):
        fill, edge = (TEAL_SOFT, TEAL) if i == 5 else (LIGHT, BORDER)
        c.box(x, y, bw, bh, label, fill=fill, outline=edge, size=25, bold=True)
        c.circle_num(x + 26, y + 4, i + 1, fill=TEAL if i == 5 else BLUE)
        if i in (0, 1, 2, 4, 5):
            c.arrow(x + bw + 6, y + bh / 2, x + bw + 52, y + bh / 2)
    c.d.line([(1054, 314), (1054, 348), (299, 348)], fill=GRAY, width=5)
    c.arrow(299, 348, 299, 376)
    c.banner(H - 150, "Register the system in Q.OMMAND only after the commissioning checklist is complete. The full guide includes torque specs and grounding requirements.", fill=TEAL_SOFT, outline=TEAL, size=23)
    c.save("installation-sequence")


def grounding_bonding() -> None:
    c = Canvas("Grounding and bonding", "Every module frame bonded to the racking, one continuous EGC back to the inverter")
    c.text(90, 150, "module frames", 22, NAVY, bold=True)
    for i in range(3):
        x = 90 + i * 200
        c.d.rectangle([x, 185, x + 180, 275], fill=BLUE, outline=NAVY, width=3)
        c.d.rectangle([x + 40, 275, x + 60, 287], fill=TEAL)
        c.d.rectangle([x + 120, 275, x + 140, 287], fill=TEAL)
    c.d.rectangle([60, 287, 700, 305], fill=GRAY)
    c.d.rectangle([60, 372, 700, 390], fill=GRAY)
    c.text(60, 398, "racking rails", 20, GRAY)
    c.pill(380, 330, "listed bonding hardware (WEEB) at every frame", fill=TEAL_SOFT, outline=TEAL, size=20)
    c.d.line([(700, 381), (790, 381), (790, 470), (930, 470)], fill=COPPER, width=8)
    c.text(60, 452, "copper line = continuous equipment grounding conductor (EGC)", 21, COPPER, bold=True)
    c.box(930, 410, 220, 120, "Inverter\nground bus", fill=BLUE_SOFT, outline=BLUE, size=26, bold=True)
    c.box(760, 150, 390, 200, "Torque bonding hardware to the manufacturer's spec - typically 90-120 in-lbs for standard WEEB washers", fill=AMBER_SOFT, outline=AMBER, size=22)
    c.banner(H - 130, "Do not rely on rail-to-rail bonding alone without a listed splice. Under-torqued bonding is a top cause of failed inspections and intermittent ground-fault trips.", size=22)
    c.save("grounding-bonding")


def escalation_flow() -> None:
    c = Canvas("When and how to escalate to L2", "Escalate with complete information - it decides how fast L2 can resolve it")
    c.box(40, 175, 230, 90, "Issue reported", fill=BLUE_SOFT, outline=BLUE, size=26, bold=True)
    c.box(330, 175, 290, 90, "Try L1 steps: power cycle, check the portal", fill=LIGHT, size=24, bold=True)
    c.arrow(272, 220, 322, 220)
    # decision diamond
    cx, cy = 790, 220
    c.d.polygon([(cx, cy - 70), (cx + 120, cy), (cx, cy + 70), (cx - 120, cy)], fill=AMBER_SOFT, outline=AMBER)
    c.text_block(cx, cy, "Resolved?", 26, NAVY, bold=True, max_w=180)
    c.arrow(622, 220, 662, 220)
    c.box(960, 175, 200, 90, "Close and rate the chat", fill=TEAL_SOFT, outline=TEAL, size=24, bold=True)
    c.arrow(912, 220, 952, 220, color=TEAL)
    c.text(925, 185, "yes", 22, TEAL, bold=True)
    c.arrow(790, 292, 790, 338, color=RED)
    c.text(802, 300, "no", 22, RED, bold=True)
    c.box(40, 342, 1120, 100, "Escalate to L2 when: a code persists after a full power cycle  |  settings need L2 access (grid protection, BMS)  |  suspected safety hazard (burning smell, arcing, damaged wiring)  |  a warranty claim needs engineering review", fill=RED_SOFT, outline=RED, size=23)
    c.box(40, 494, 1120, 92, "Always include: serial number  +  exact error code and timestamp  +  the troubleshooting steps already tried", fill=BLUE_SOFT, outline=BLUE, size=25, bold=True)
    c.arrow(600, 446, 600, 486, color=BLUE)
    c.save("escalation-flow")


def battery_clearances() -> None:
    c = Canvas("Q.HOME ESS siting and clearances", "Confirm local AHJ (Authority Having Jurisdiction) rules before final placement")
    # wall + floor
    c.d.rectangle([60, 160, 100, 500], fill=LIGHT, outline=BORDER)
    c.d.rectangle([60, 500, 700, 540], fill=GRAY)
    c.text(380, 520, "non-combustible surface or approved fire barrier", 20, WHITE, anchor="mm")
    # battery
    c.d.rounded_rectangle([250, 250, 510, 480], radius=14, fill=BLUE_SOFT, outline=BLUE, width=4)
    c.text_block(380, 365, "Q.HOME ESS", 30, NAVY, bold=True, max_w=220)
    for (x1, y1, x2, y2, lx, ly) in [(250, 365, 130, 365, 190, 335), (510, 365, 640, 365, 575, 335), (380, 250, 380, 170, 470, 200)]:
        c.arrow(x1, y1, x2, y2, color=TEAL, width=4)
        c.arrow(x2, y2, x1, y1, color=TEAL, width=4)
        c.pill(lx, ly, "3 in", fill=TEAL_SOFT, outline=TEAL, size=22)
    c.box(740, 160, 420, 150, "Minimum 3-inch clearance on all sides for ventilation", fill=TEAL_SOFT, outline=TEAL, size=24, bold=True)
    c.box(740, 340, 420, 200, "Do not install in: habitable rooms, a garage vehicle path, or directly beneath egress windows (in most jurisdictions)", fill=RED_SOFT, outline=RED, size=23)
    c.banner(H - 118, "Update the BMS firmware to the latest version before the first charge cycle.", fill=BLUE_SOFT, outline=BLUE, size=24)
    c.save("battery-clearances")


def monitoring_connectivity() -> None:
    c = Canvas("How monitoring data reaches the portal", "Most 'system offline' reports are a home-network problem, not an inverter fault")
    nodes = [("Inverter\n+ Wi-Fi dongle", BLUE_SOFT, BLUE), ("Home router\n(SSID / password)", AMBER_SOFT, AMBER), ("Internet", LIGHT, BORDER), ("Q.OMMAND\ncloud", LIGHT, BORDER), ("App / web\nportal", TEAL_SOFT, TEAL)]
    bw, bh, gap, x0, y = 176, 130, 52, 56, 190
    for i, (label, fill, edge) in enumerate(nodes):
        x = x0 + i * (bw + gap)
        c.box(x, y, bw, bh, label, fill=fill, outline=edge, size=25, bold=True)
        if i < 4:
            c.arrow(x + bw + 6, y + bh / 2, x + bw + gap - 6, y + bh / 2)
    c.box(40, 372, 480, 110, "Router firmware update or SSID / password change drops the dongle's connection", fill=RED_SOFT, outline=RED, size=23)
    c.arrow(372, 366, 372, 328, color=RED)
    c.box(560, 372, 600, 110, "The inverter keeps producing normally - only reporting stops. Re-pair the dongle with the current network name and password.", fill=TEAL_SOFT, outline=TEAL, size=23)
    c.banner(H - 150, "Check the site's Wi-Fi first. Only if the network is healthy and the unit is still offline, escalate.", fill=BLUE_SOFT, outline=BLUE, size=24)
    c.save("monitoring-connectivity")


def panel_troubleshooting_flow() -> None:
    c = Canvas("Low or no panel output - what to check", "Work top to bottom; fix the first thing you find, then re-measure")
    c.box(40, 245, 250, 150, "Symptom:\nlow output or no charging indication", fill=RED_SOFT, outline=RED, size=25, bold=True)
    rows = [
        ("1  Shading or dirt on the module?", "Remove the shade or relocate; clean the surface"),
        ("2  Broken, corroded or loose wiring?", "Repair or replace the cable / connection"),
        ("3  Cracked module or broken front glass?", "Replace the module (check warranty first)"),
        ("4  Blocking diode or charge controller failed?", "Replace the failed part"),
    ]
    ry = 140
    for i, (check, fix) in enumerate(rows):
        y = ry + i * 100
        c.box(350, y, 400, 84, check, fill=LIGHT, size=22, bold=True)
        c.box(800, y, 360, 84, fix, fill=TEAL_SOFT, outline=TEAL, size=22)
        c.arrow(752, y + 42, 792, y + 42, color=TEAL)
        c.arrow(292, 320, 342, y + 42, color=GRAY, width=3, head=12)
    c.banner(H - 120, "Still low after all four checks? Escalate to L2 with the serial number and measured voltage / current.", size=23)
    c.save("panel-troubleshooting-flow")


def shading_clearance() -> None:
    c = Canvas("Keeping obstructions out of the array's shade", "Rule of thumb for arrays facing south (northern hemisphere) - drawn to scale")
    h_px = 150
    for x0, label, factor, mult in [(40, "East / West of the array", "> 2 x h", 2.0), (620, "South of the array", "> 0.5 x h", 0.5)]:
        c.d.rounded_rectangle([x0, 140, x0 + 540, 520], radius=18, fill=LIGHT, outline=BORDER, width=3)
        c.text(x0 + 24, 156, label, 26, NAVY, bold=True)
        gy = 410
        c.d.line([(x0 + 20, gy), (x0 + 520, gy)], fill=GRAY, width=4)
        px1 = x0 + 130
        c.d.polygon([(x0 + 40, gy - 8), (px1, gy - 8), (px1, gy - 44), (x0 + 40, gy - 30)], fill=BLUE, outline=NAVY)
        c.text(x0 + 85, gy - 76, "array", 20, GRAY, anchor="ma")
        ox = int(px1 + mult * h_px)
        c.d.rectangle([ox, gy - h_px, ox + 46, gy], fill="#7A8AA8", outline=NAVY, width=2)
        c.text(ox + 23, gy - h_px - 30, "obstruction", 20, GRAY, anchor="ma")
        hx = ox + 64
        c.arrow(hx, gy - 6, hx, gy - h_px, color=RED, width=3, head=12)
        c.arrow(hx, gy - h_px, hx, gy - 6, color=RED, width=3, head=12)
        c.text(hx + 12, gy - h_px / 2 - 16, "h", 30, RED, bold=True)
        ay = gy + 36
        c.arrow(px1, ay, ox, ay, color=TEAL, width=4)
        c.arrow(ox, ay, px1, ay, color=TEAL, width=4)
        c.pill((px1 + ox) / 2, ay + 38, "distance " + factor, fill=TEAL_SOFT, outline=TEAL, size=22)
    c.banner(H - 118, "Row spacing for tilted arrays should also grow with site latitude - the sun sits lower and casts longer shadows.", size=23)
    c.save("shading-clearance")


def pv_system_components() -> None:
    c = Canvas("Solar PV building blocks", "From a single cell to a complete battery-backed system")
    tiers = [("Cell", 1, 1), ("Module", 3, 2), ("Panel", 3, 3), ("Array", 5, 3)]
    x = 60
    for i, (label, cols, rows) in enumerate(tiers):
        c.text(x, 150, label, 26, NAVY, bold=True)
        c.module_grid(x, 200, cols, rows, cw=26, ch=18, gap=3, fill=BLUE)
        if i < 3:
            c.arrow(x + cols * 29 + 26, 232, x + 176, 232, color=GRAY, width=4, head=12)
        x += 270
    c.text(60, 290, "cells wire into a module -> modules form a panel -> panels mount together as an array", 21, GRAY)
    chain = [("Array", BLUE_SOFT, BLUE), ("Field junction\nbox (FJB)", LIGHT, BORDER), ("Charge\ncontroller", AMBER_SOFT, AMBER), ("Battery\nbank", TEAL_SOFT, TEAL), ("Load", LIGHT, BORDER)]
    bw, bh, gap, y = 170, 120, 56, 360
    x0 = (W - (5 * bw + 4 * gap)) // 2
    for i, (label, fill, edge) in enumerate(chain):
        bx = x0 + i * (bw + gap)
        c.box(bx, y, bw, bh, label, fill=fill, outline=edge, size=24, bold=True)
        if i < 4:
            c.arrow(bx + bw + 6, y + bh / 2, bx + bw + gap - 6, y + bh / 2)
    c.banner(H - 150, "The charge controller protects the battery from overcharge; the FJB is where panel wiring and the wiring to the controller are terminated.", size=22)
    c.save("pv-system-components")


if __name__ == "__main__":
    for fn in (power_cycle_procedure, inverter_error_codes, rapid_shutdown_layout, installation_sequence, grounding_bonding,
               escalation_flow, battery_clearances, monitoring_connectivity, panel_troubleshooting_flow, shading_clearance,
               pv_system_components):
        fn()
