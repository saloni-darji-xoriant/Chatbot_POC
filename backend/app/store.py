"""Process-local in-memory data store for the POC.

Not persistent and not safe for multi-worker deployment — swap this for a
real database (e.g. DynamoDB/Postgres) before going to production. Kept as a
single module-level singleton so routers can share state easily.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.models import (
    Conversation,
    ConversationStatus,
    Correction,
    DocumentItem,
    DocumentType,
    FeedbackItem,
    Message,
    MessageSender,
    User,
    UserRole,
    VoteValue,
)
from app.services.knowledge_base import KNOWLEDGE_BASE
from app.utils import new_id, utcnow


def last_activity(conv: Conversation) -> datetime:
    """When the conversation last changed — its newest message, else creation."""
    return conv.messages[-1].created_at if conv.messages else conv.created_at


class Store:
    def __init__(self) -> None:
        self.users: dict[str, dict] = {}
        self.conversations: dict[str, Conversation] = {}
        self.feedback: dict[str, FeedbackItem] = {}
        self.documents: dict[str, DocumentItem] = {}
        self._seed()

    # ------------------------------------------------------------------
    def _seed(self) -> None:
        # Imported lazily to avoid a circular import (chat_pipeline imports
        # this module's `new_id` re-export via app.utils, not app.store).
        from app.services.chat_pipeline import generate_assistant_reply, handoff_reply

        installer = User(
            id="u_installer_1",
            name="Jordan Reyes",
            email="jordan.reyes@installer.qcells.com",
            role=UserRole.installer,
            region="Southwest Region",
        )
        second_installer = User(
            id="u_installer_2",
            name="Morgan Lee",
            email="morgan.lee@installer.qcells.com",
            role=UserRole.installer,
            region="Northeast Region",
        )
        admin = User(
            id="u_admin_1",
            name="Casey Kim",
            email="casey.kim@qcells.com",
            role=UserRole.admin,
            region="HQ - Irvine, CA",
        )
        self.users[installer.email] = {"user": installer, "password": "installer123"}
        self.users[second_installer.email] = {"user": second_installer, "password": "installer123"}
        self.users[admin.email] = {"user": admin, "password": "admin123"}

        now = utcnow()

        # The Documents list is derived directly from the knowledge base's own
        # citations (deduped by filename) so it always reflects the real KB
        # content, rather than a hand-maintained list that can drift out of
        # sync. Category is inferred from the filename itself (not "whichever
        # entry happened to cite it first") since reference manuals/guides are
        # shared across many entries regardless of which KB category asks for
        # them — only the per-incident "Case-Q-*" records are truly case tickets.
        def _infer_document_category(filename: str) -> str:
            if filename.startswith("Case-Q-"):
                return "Case Ticket"
            if "Datasheet" in filename:
                return "Solar System"
            if "Handbook" in filename or "Homeowners-Guide" in filename:
                return "Reference Guide"
            return "Installer FAQ"

        seen_docs: set[str] = set()
        for entry in KNOWLEDGE_BASE:
            for citation in entry.citations:
                seen_docs.add(citation["document"])

        for i, filename in enumerate(sorted(seen_docs)):
            category = _infer_document_category(filename)
            doc_id = new_id("doc")
            ftype = DocumentType.md if filename.endswith(".md") else DocumentType.pdf
            self.documents[doc_id] = DocumentItem(
                id=doc_id,
                filename=filename,
                category=category,
                file_type=ftype,
                updated_at=now - timedelta(days=(i * 3) % 60 + 1),
            )

        # Seed realistic, linked conversations (built with the same pipeline
        # the live chat endpoints use) spanning all three KB categories —
        # solar system product questions, case-ticket-style incidents, and
        # installer FAQs — plus one genuinely out-of-scope query that still
        # falls through to a handoff, so History/Admin have real, varied
        # data to show out of the box.
        seed_conversations = [
            dict(user=installer, query="What's the difference between the Q.PEAK and Q.TRON panels?",
                 sentiment=VoteValue.up, stars=5, comment="Clear comparison, exactly what I needed"),
            dict(user=second_installer, query="My inverter is showing an E02 error code",
                 sentiment=VoteValue.up, stars=5, comment="Fixed it in two minutes, thanks!"),
            dict(user=installer, query="My panels stopped producing after the storm",
                 sentiment=VoteValue.down, stars=2, comment="Answer didn't cover physical damage cases",
                 vote_reason="Didn't mention checking for storm/hail damage before the standard low-output steps"),
            dict(user=second_installer, query="Two panels are showing near-zero output after a hailstorm",
                 sentiment=VoteValue.up, stars=5, comment="The IV curve trace reference was exactly right"),
            dict(user=installer, query="Where do I file a warranty claim?",
                 sentiment=VoteValue.up, stars=4),
            dict(user=second_installer, query="Monitoring portal won't let me log in",
                 sentiment=VoteValue.up, stars=5, comment="Quick and accurate"),
            dict(user=installer, query="Firmware update stuck at 40%",
                 sentiment=VoteValue.down, stars=2, comment="Had to be escalated anyway",
                 vote_reason="Didn't give a fallback step for when the auto-update itself is stuck (vs. not starting)"),
            dict(user=second_installer, query="My battery won't charge past 20%",
                 sentiment=VoteValue.up, stars=5, comment="The BMS firmware tip saved a truck roll"),
            dict(user=installer, query="What's the usable capacity of the Q.HOME ESS battery?",
                 sentiment=VoteValue.up, stars=4),
            dict(user=second_installer, query="Rapid shutdown failed the initiation test during inspection",
                 sentiment=VoteValue.down, stars=3, comment="Right diagnosis but I'd already checked the transmitter wiring",
                 vote_reason="Could have mentioned checking torque on the combiner box terminals specifically"),
            dict(user=installer, query="I smell something burning near the inverter",
                 sentiment=VoteValue.up, stars=5, comment="Correctly told me to de-energize immediately"),
            dict(user=second_installer, query="What torque spec should I use for racking bolts?",
                 sentiment=VoteValue.up, stars=4),
            dict(user=second_installer, query="How long does the federal tax credit take with a state rebate?",
                 sentiment=VoteValue.up, stars=4, comment="Pointed me to the right team quickly"),
            dict(user=installer, query="Do you offer a referral bonus for bringing in new customers?",
                 status=ConversationStatus.handoff),
        ]

        for i, seed in enumerate(seed_conversations):
            user = seed["user"]
            query = seed["query"]
            created = now - timedelta(hours=i * 11 + 2)
            status = seed.get("status", ConversationStatus.resolved)

            conv = Conversation(
                id=new_id("conv"),
                user_id=user.id,
                title=query[:60],
                status=status,
                created_at=created,
                messages=[],
            )
            user_message = Message(
                id=new_id("msg"),
                conversation_id=conv.id,
                sender=MessageSender.user,
                text=query,
                created_at=created,
            )
            # Seed data must be deterministic and offline - never call a language model here.
            if status == ConversationStatus.handoff:
                assistant_message = handoff_reply(conv.id, created)
            else:
                assistant_message = generate_assistant_reply(conv.id, query, created_at=created, use_llm=False)

            sentiment = seed.get("sentiment")
            if sentiment is not None:
                assistant_message.vote = sentiment
                assistant_message.vote_reason = seed.get("vote_reason")

            conv.messages = [user_message, assistant_message]
            self.conversations[conv.id] = conv

            if sentiment is not None:
                feedback_id = new_id("fb")
                self.feedback[feedback_id] = FeedbackItem(
                    id=feedback_id,
                    conversation_id=conv.id,
                    message_id=assistant_message.id,
                    query=query,
                    sentiment=sentiment,
                    stars=seed.get("stars"),
                    comment=seed.get("comment"),
                    created_at=created,
                    user_name=user.name,
                )

    # ------------------------------------------------------------------
    def get_user_by_email(self, email: str) -> dict | None:
        return self.users.get(email)

    def get_user(self, user_id: str) -> User | None:
        for entry in self.users.values():
            if entry["user"].id == user_id:
                return entry["user"]
        return None

    # ------------------------------------------------------------------
    def create_conversation(self, user_id: str, title: str | None) -> Conversation:
        conv_id = new_id("conv")
        conv = Conversation(
            id=conv_id,
            user_id=user_id,
            title=title or "New question",
            status=ConversationStatus.active,
            created_at=utcnow(),
            messages=[],
        )
        self.conversations[conv_id] = conv
        return conv

    def get_conversation(self, conv_id: str) -> Conversation | None:
        return self.conversations.get(conv_id)

    def list_conversations_for_user(self, user_id: str) -> list[Conversation]:
        return [c for c in self.conversations.values() if c.user_id == user_id]

    def list_all_conversations(self) -> list[Conversation]:
        return list(self.conversations.values())

    def add_message(self, conv_id: str, message: Message) -> None:
        self.conversations[conv_id].messages.append(message)

    def find_message(self, message_id: str) -> tuple[Conversation, Message] | None:
        for conv in self.conversations.values():
            for msg in conv.messages:
                if msg.id == message_id:
                    return conv, msg
        return None

    def maybe_set_title(self, conv: Conversation, text: str) -> None:
        if not conv.messages and conv.title in (None, "New question"):
            conv.title = text[:60] + ("..." if len(text) > 60 else "")

    # ------------------------------------------------------------------
    def record_feedback(self, item: FeedbackItem) -> None:
        self.feedback[item.id] = item

    def list_feedback(self) -> list[FeedbackItem]:
        return sorted(self.feedback.values(), key=lambda f: f.created_at, reverse=True)

    def get_feedback(self, feedback_id: str) -> FeedbackItem | None:
        return self.feedback.get(feedback_id)

    def set_feedback_correction(self, feedback_id: str, correction: Correction) -> FeedbackItem | None:
        item = self.feedback.get(feedback_id)
        if item is None:
            return None
        updated = item.model_copy(update={"correction": correction})
        self.feedback[feedback_id] = updated
        return updated

    # ------------------------------------------------------------------
    def list_documents(self) -> list[DocumentItem]:
        return sorted(self.documents.values(), key=lambda d: d.updated_at, reverse=True)

    def add_document(self, doc: DocumentItem) -> None:
        self.documents[doc.id] = doc

    def delete_document(self, doc_id: str) -> bool:
        return self.documents.pop(doc_id, None) is not None


store = Store()
