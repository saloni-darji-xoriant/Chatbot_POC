"""In-memory, session-scoped attachment store.

Files a user attaches to a chat message are held ONLY in this process's
memory, keyed by conversation ID (the app's "session" unit) — never written
to disk, and never touching the project folder. They vanish on backend
restart, same as every other in-memory store in this POC (see store.py).

Text extraction happens once, synchronously, at upload time — not on every
chat message — so later messages just do a cheap in-memory lookup instead of
re-parsing the file. Combined with hard size/length caps, this keeps the
feature fast: uploading a file does a bounded amount of work exactly once,
and every subsequent question against it is just keyword scoring over an
already-extracted string.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from datetime import datetime

from app.utils import new_id, utcnow

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB per file — keeps extraction fast
MAX_ATTACHMENTS_PER_CONVERSATION = 8
MAX_EXTRACTED_CHARS = 20_000  # cap how much text we keep/search per file
MAX_PDF_PAGES = 15

DOCUMENT_EXTENSIONS = {".txt", ".md", ".csv", ".log", ".json"}
PDF_EXTENSIONS = {".pdf"}
DOCX_EXTENSIONS = {".docx"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


class AttachmentTooLarge(Exception):
    pass


class AttachmentLimitReached(Exception):
    pass


@dataclass
class AttachmentRecord:
    id: str
    conversation_id: str
    filename: str
    mime_type: str
    kind: str  # "document" | "image"
    size_bytes: int
    extracted_text: str | None
    extraction_note: str | None
    uploaded_at: datetime = field(default_factory=utcnow)


# conversation_id -> {attachment_id -> AttachmentRecord}
_by_conversation: dict[str, dict[str, AttachmentRecord]] = {}


def _extension(filename: str) -> str:
    idx = filename.rfind(".")
    return filename[idx:].lower() if idx != -1 else ""


def _extract_text(filename: str, content: bytes) -> tuple[str | None, str, str | None]:
    """Returns (extracted_text, kind, extraction_note)."""
    ext = _extension(filename)

    if ext in IMAGE_EXTENSIONS:
        try:
            from PIL import Image

            with Image.open(io.BytesIO(content)) as img:
                note = f"{img.format} image, {img.width}x{img.height}px — visual content is not analyzed in this POC"
        except Exception:
            note = "Image file — visual content is not analyzed in this POC"
        return None, "image", note

    if ext in DOCUMENT_EXTENSIONS:
        text = content.decode("utf-8", errors="ignore")
        return text[:MAX_EXTRACTED_CHARS], "document", None

    if ext in PDF_EXTENSIONS:
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            pages = reader.pages[:MAX_PDF_PAGES]
            text = "\n\n".join(page.extract_text() or "" for page in pages)
            note = None if text.strip() else "No extractable text found (likely a scanned/image-only PDF)"
            return text[:MAX_EXTRACTED_CHARS] or None, "document", note
        except Exception:
            return None, "document", "Could not parse this PDF"

    if ext in DOCX_EXTENSIONS:
        try:
            import docx

            document = docx.Document(io.BytesIO(content))
            text = "\n\n".join(p.text for p in document.paragraphs if p.text.strip())
            return text[:MAX_EXTRACTED_CHARS] or None, "document", None
        except Exception:
            return None, "document", "Could not parse this .docx file"

    return None, "document", "Unsupported file type — stored as an attachment without text extraction"


def add_attachment(conversation_id: str, filename: str, mime_type: str, content: bytes) -> AttachmentRecord:
    if len(content) > MAX_FILE_SIZE:
        raise AttachmentTooLarge(f"File exceeds the {MAX_FILE_SIZE // (1024 * 1024)}MB limit")

    existing = _by_conversation.setdefault(conversation_id, {})
    if len(existing) >= MAX_ATTACHMENTS_PER_CONVERSATION:
        raise AttachmentLimitReached(
            f"This conversation already has {MAX_ATTACHMENTS_PER_CONVERSATION} attachments"
        )

    extracted_text, kind, note = _extract_text(filename, content)
    record = AttachmentRecord(
        id=new_id("att"),
        conversation_id=conversation_id,
        filename=filename,
        mime_type=mime_type,
        kind=kind,
        size_bytes=len(content),
        extracted_text=extracted_text,
        extraction_note=note,
    )
    existing[record.id] = record
    return record


def get(attachment_id: str) -> AttachmentRecord | None:
    for bucket in _by_conversation.values():
        if attachment_id in bucket:
            return bucket[attachment_id]
    return None


def get_for_conversation(conversation_id: str) -> list[AttachmentRecord]:
    return sorted(_by_conversation.get(conversation_id, {}).values(), key=lambda a: a.uploaded_at)


def delete(conversation_id: str, attachment_id: str) -> bool:
    return _by_conversation.get(conversation_id, {}).pop(attachment_id, None) is not None


_WORD_RE = re.compile(r"[a-z0-9']+")


def _chunks(text: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) > 1:
        return paragraphs
    # No paragraph breaks (e.g. a single-line CSV/log) — fall back to fixed windows.
    window = 400
    return [text[i : i + window] for i in range(0, len(text), window)] or [text]


def search_attachments(conversation_id: str, query: str) -> tuple[AttachmentRecord, str] | None:
    """Find the best-matching excerpt across this conversation's attachments,
    using the same lightweight keyword-overlap scoring as the KB search."""
    query_words = set(_WORD_RE.findall(query.lower()))
    if not query_words:
        return None

    best: tuple[AttachmentRecord, str] | None = None
    best_score = 0
    for record in get_for_conversation(conversation_id):
        if not record.extracted_text:
            continue
        for chunk in _chunks(record.extracted_text):
            score = len(query_words & set(_WORD_RE.findall(chunk.lower())))
            if score > best_score:
                best_score = score
                best = (record, chunk)

    return best
