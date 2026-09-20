import uuid
from datetime import datetime, timezone


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def utcnow() -> datetime:
    """Timezone-aware current UTC time.

    Naive `datetime.utcnow()` serializes to JSON without an offset, which
    browsers then parse as *local* time — silently shifting every timestamp by
    the viewer's UTC offset. Aware datetimes serialize with `+00:00`, so the
    frontend converts them to the viewer's local time correctly.
    """
    return datetime.now(timezone.utc)
