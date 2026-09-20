"""Render a conversation as a PDF transcript.

Timestamps are converted to the *viewer's* timezone (an IANA name such as
"Asia/Kolkata" sent by the browser), so the PDF matches what the person sees
on screen wherever the app is being used. An unknown/missing zone falls back
to UTC and the zone is always printed, so the document is never ambiguous.

Uses fpdf2 with the built-in Helvetica font (no font files to ship), which only
covers Latin-1 - `_latin1` maps common typographic characters to ASCII
equivalents and replaces anything else rather than raising.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fpdf import FPDF

from app.models import Conversation, Message, MessageSender, User

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

NAVY = (16, 27, 54)
BLUE = (30, 111, 235)
GRAY = (102, 112, 133)
LIGHT = (244, 246, 250)

_REPLACEMENTS = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", "•": "-", " ": " ",
    "→": "->", "≤": "<=", "≥": ">=", "×": "x",
}


def _latin1(text: str) -> str:
    for src, dst in _REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", "replace").decode("latin-1")


def resolve_timezone(name: str | None) -> ZoneInfo | timezone:
    if name:
        try:
            return ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError, OSError):
            pass
    return timezone.utc


def format_local(moment: datetime, tz: ZoneInfo | timezone) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    local = moment.astimezone(tz)
    hour = local.strftime("%I").lstrip("0") or "12"
    zone = local.strftime("%Z") or "UTC"
    return f"{local.day} {local.strftime('%b %Y')}, {hour}:{local.strftime('%M %p')} {zone}"


class _TranscriptPdf(FPDF):
    def __init__(self, footer_label: str) -> None:
        super().__init__(format="A4", unit="mm")
        self._footer_label = footer_label
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 18, 18)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Helvetica", size=8)
        self.set_text_color(*GRAY)
        self.cell(0, 6, _latin1(self._footer_label), align="L")
        self.cell(0, 6, f"Page {self.page_no()} of {{nb}}", align="R")


def _image_path(url: str) -> Path | None:
    """Map a /static/... URL to a file on disk, refusing anything that
    escapes the static directory."""
    if not url.startswith("/static/"):
        return None
    candidate = (_STATIC_DIR / url.removeprefix("/static/")).resolve()
    if _STATIC_DIR.resolve() not in candidate.parents or not candidate.is_file():
        return None
    return candidate


def _write_message(pdf: _TranscriptPdf, msg: Message, user_name: str, tz: ZoneInfo | timezone) -> None:
    is_user = msg.sender == MessageSender.user
    who = user_name if is_user else "Qcells Assistant"
    accent = BLUE if is_user else NAVY

    if pdf.get_y() > pdf.h - 45:  # keep the sender line with at least a few lines of body
        pdf.add_page()

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*accent)
    pdf.cell(0, 6, _latin1(who), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 4, _latin1(format_local(msg.created_at, tz)), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    pdf.set_font("Helvetica", size=10.5)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 5.5, _latin1(msg.text), align="L", new_x="LMARGIN", new_y="NEXT")

    for att in msg.attachments:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*GRAY)
        pdf.multi_cell(0, 5, _latin1(f"Attached: {att.filename}"), new_x="LMARGIN", new_y="NEXT")

    for image in msg.images:
        path = _image_path(image.url)
        if path is None:
            continue
        width = pdf.w - pdf.l_margin - pdf.r_margin
        height = width * 675 / 1200
        if pdf.get_y() + height + 8 > pdf.h - pdf.b_margin:
            pdf.add_page()
        pdf.ln(2)
        pdf.image(str(path), x=pdf.l_margin, w=width)
        if image.caption:
            pdf.set_font("Helvetica", "I", 8.5)
            pdf.set_text_color(*GRAY)
            pdf.multi_cell(0, 4.5, _latin1(f"Figure: {image.caption}"), new_x="LMARGIN", new_y="NEXT")

    if msg.citations:
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*GRAY)
        pdf.cell(0, 5, "Sources", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=8.5)
        for cit in msg.citations:
            section = f" - {cit.section}" if cit.section else ""
            pdf.multi_cell(0, 4.5, _latin1(f"- {cit.label} ({cit.document}{section})"), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)
    pdf.set_draw_color(225, 229, 238)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)


def build_conversation_pdf(
    conv: Conversation, user: User, tz_name: str | None, exported_at: datetime
) -> bytes:
    tz = resolve_timezone(tz_name)
    pdf = _TranscriptPdf(footer_label="Hanwha Qcells L1 Assistant - chat transcript")
    pdf.alias_nb_pages()
    pdf.set_title(_latin1(conv.title))
    pdf.set_author("Hanwha Qcells L1 Assistant")
    pdf.add_page()

    pdf.set_fill_color(*BLUE)
    pdf.rect(0, 0, pdf.w, 4, style="F")
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, 9, _latin1(conv.title), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", size=9)
    pdf.set_text_color(*GRAY)
    meta = [
        f"Exported by {user.name} on {format_local(exported_at, tz)}",
        f"Conversation status: {conv.status.value} | Messages: {len(conv.messages)}",
        f"Started: {format_local(conv.created_at, tz)} | Times shown in {getattr(tz, 'key', 'UTC')}",
    ]
    for line in meta:
        pdf.cell(0, 5, _latin1(line), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_draw_color(*BLUE)
    pdf.set_line_width(0.6)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(6)

    if not conv.messages:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, "This conversation has no messages yet.", new_x="LMARGIN", new_y="NEXT")

    for msg in conv.messages:
        _write_message(pdf, msg, user.name, tz)

    return bytes(pdf.output())
