from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Shared enums
# ---------------------------------------------------------------------------

class UserRole(str, Enum):
    installer = "installer"
    admin = "admin"


class MessageSender(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class VoteValue(str, Enum):
    up = "up"
    down = "down"


class ConversationStatus(str, Enum):
    active = "active"
    handoff = "handoff"
    resolved = "resolved"


class ProcessStepStatus(str, Enum):
    pending = "pending"
    active = "active"
    done = "done"


class DocumentType(str, Enum):
    pdf = "PDF"
    md = "MD"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class User(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole
    region: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Work email address")
    password: str = Field(..., min_length=1, description="Account password")


class SsoLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Work email used to resolve SSO identity")


class LoginResponse(BaseModel):
    token: str
    user: User


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class Citation(BaseModel):
    id: str
    label: str
    document: str
    section: Optional[str] = None


class ProcessStep(BaseModel):
    label: str
    status: ProcessStepStatus
    agent: Optional[str] = Field(
        default=None, description="Name of the pipeline agent that performed this step"
    )


class KGNode(BaseModel):
    id: str
    label: str
    type: str  # "topic" | "document" | "entity" | "correction"


class KGEdge(BaseModel):
    source: str
    target: str
    relation: str


class KnowledgeGraph(BaseModel):
    nodes: list[KGNode] = Field(default_factory=list)
    edges: list[KGEdge] = Field(default_factory=list)


class AttachmentSummary(BaseModel):
    id: str
    conversation_id: str
    filename: str
    mime_type: str
    kind: str  # "document" | "image"
    size_bytes: int
    has_extracted_text: bool
    preview: Optional[str] = Field(default=None, description="First ~200 chars of extracted text, if any")
    extraction_note: Optional[str] = None
    uploaded_at: datetime


class MessageImage(BaseModel):
    url: str = Field(description="Server-relative path, e.g. /static/kb-images/power-cycle-procedure.png")
    alt: str
    caption: Optional[str] = None


class Message(BaseModel):
    id: str
    conversation_id: str
    sender: MessageSender
    text: str
    created_at: datetime
    citations: list[Citation] = Field(default_factory=list)
    quick_replies: list[str] = Field(default_factory=list)
    process_trace: list[ProcessStep] = Field(default_factory=list)
    knowledge_graph: Optional[KnowledgeGraph] = None
    attachments: list[AttachmentSummary] = Field(default_factory=list)
    images: list[MessageImage] = Field(default_factory=list)
    vote: Optional[VoteValue] = None
    vote_reason: Optional[str] = None
    is_grounded: bool = True


class Conversation(BaseModel):
    id: str
    user_id: str
    title: str
    status: ConversationStatus
    created_at: datetime
    messages: list[Message] = Field(default_factory=list)


class ConversationSummary(BaseModel):
    id: str
    title: str
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime = Field(description="Time of the last message (or creation time if empty)")
    last_message_preview: Optional[str] = None


class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field(default=None, description="Optional title; defaults to 'New question'")


class SendMessageRequest(BaseModel):
    text: str = Field(..., min_length=1, description="The user's message text")
    attachment_ids: list[str] = Field(
        default_factory=list,
        description="IDs of files uploaded via /attachments to tag as sent with this message",
    )


class SendMessageResponse(BaseModel):
    user_message: Message
    assistant_message: Message
    conversation_status: ConversationStatus


class VoteRequest(BaseModel):
    vote: Optional[VoteValue] = Field(
        default=None, description="'up', 'down', or null to clear the vote"
    )
    reason: Optional[str] = Field(
        default=None, max_length=1000, description="Optional reason, typically provided with a thumbs-down vote"
    )


class HandoffRequest(BaseModel):
    reason: Optional[str] = Field(default=None, description="Why the handoff was triggered")


class HandoffContact(BaseModel):
    label: str
    value: str
    icon: str


class HandoffInfo(BaseModel):
    message: str
    contacts: list[HandoffContact]
    queue_position: Optional[int] = None


class RatingRequest(BaseModel):
    stars: int = Field(..., ge=1, le=5)
    thumbs: Optional[VoteValue] = None
    comment: Optional[str] = Field(default=None, max_length=2000)


class RatingResponse(BaseModel):
    conversation_id: str
    stars: int
    thumbs: Optional[VoteValue]
    comment: Optional[str]
    created_at: datetime


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

class KpiCards(BaseModel):
    conversations: int
    total_messages: int
    unique_users: int
    messages_today: int


class QualityRings(BaseModel):
    grounding_rate: float = Field(..., ge=0, le=100)
    satisfaction: float = Field(..., ge=0, le=100)


class FeedbackBreakdown(BaseModel):
    positive: int
    negative: int


class ActivityPoint(BaseModel):
    day: str
    value: int


class DashboardResponse(BaseModel):
    kpis: KpiCards
    quality: QualityRings
    feedback_breakdown: FeedbackBreakdown
    activity: list[ActivityPoint]


class Correction(BaseModel):
    text: str
    document_filename: Optional[str] = None
    created_at: datetime


class CorrectionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    document_filename: Optional[str] = Field(default=None, description="Optional filename to register as a KB document")
    add_as_document: bool = Field(
        default=False, description="If true, also registers document_filename in the Documents list"
    )


class FeedbackItem(BaseModel):
    id: str
    conversation_id: str
    message_id: Optional[str] = None
    query: str
    sentiment: VoteValue
    stars: Optional[int] = None
    comment: Optional[str] = None
    created_at: datetime
    user_name: str
    correction: Optional[Correction] = None


class DocumentItem(BaseModel):
    id: str
    filename: str
    category: str
    file_type: DocumentType
    updated_at: datetime


class CreateDocumentRequest(BaseModel):
    filename: str
    category: str
    file_type: DocumentType
