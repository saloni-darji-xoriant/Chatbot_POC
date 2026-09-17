"""Small-talk detection so greetings/thanks/farewells get a normal
conversational reply instead of being treated as an ungrounded support
question and escalated to a human.

Handoff should only ever trigger when the user asked a real question the
knowledge base has no answer for — not when they just said "hi".
"""

from __future__ import annotations

import re

_WORD_RE = re.compile(r"[a-z']+")

GREETING_WORDS = {"hi", "hello", "hey", "hiya", "yo", "greetings", "howdy"}
GREETING_PHRASES = {
    "good morning",
    "good afternoon",
    "good evening",
    "how are you",
    "how are you doing",
    "how's it going",
    "hows it going",
    "what's up",
    "whats up",
}
THANKS_WORDS = {"thanks", "thank", "thankyou", "appreciate", "appreciated"}
FAREWELL_WORDS = {"bye", "goodbye", "cya", "seeya"}

CHITCHAT_RESPONSES: dict[str, str] = {
    "greeting": (
        "Hi! I'm the Qcells L1 Assistant. I can help with installer questions "
        "about inverter faults, panel output, warranty claims, firmware updates, "
        "monitoring portal access, and installation steps. What can I help you with today?"
    ),
    "thanks": "You're welcome! Let me know if there's anything else I can help with.",
    "farewell": "Take care! Come back anytime you have an installer question.",
}

CHITCHAT_QUICK_REPLIES: dict[str, list[str]] = {
    "greeting": [
        "My inverter is showing an error code",
        "How do I file a warranty claim?",
        "I can't log in to the monitoring portal",
    ],
    "thanks": [],
    "farewell": [],
}


def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def classify_chitchat(text: str) -> str | None:
    """Return 'greeting' / 'thanks' / 'farewell' if the WHOLE message is
    small talk, or None if it looks like a real support question (so
    "hi, my inverter won't turn on" still gets routed to the knowledge base
    instead of a canned greeting)."""
    normalized = text.lower().strip().rstrip("!.?")
    tokens = _tokens(normalized)
    if not tokens or len(tokens) > 4:
        return None

    if normalized in GREETING_PHRASES:
        return "greeting"
    if tokens[0] in GREETING_WORDS:
        return "greeting"
    if any(w in THANKS_WORDS for w in tokens):
        return "thanks"
    if any(w in FAREWELL_WORDS for w in tokens):
        return "farewell"
    return None
