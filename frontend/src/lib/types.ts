export type UserRole = "installer" | "admin";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  region?: string | null;
}

export type MessageSender = "user" | "assistant" | "system";
export type VoteValue = "up" | "down";
export type ConversationStatus = "active" | "handoff" | "resolved";
export type ProcessStepStatus = "pending" | "active" | "done";
export type KGNodeType = "topic" | "document" | "entity" | "correction";

export interface Citation {
  id: string;
  label: string;
  document: string;
  section?: string | null;
}

export interface ProcessStep {
  label: string;
  status: ProcessStepStatus;
  agent?: string | null;
}

export interface KGNode {
  id: string;
  label: string;
  type: KGNodeType;
}

export interface KGEdge {
  source: string;
  target: string;
  relation: string;
}

export interface KnowledgeGraph {
  nodes: KGNode[];
  edges: KGEdge[];
}

export type AttachmentKind = "document" | "image";

export interface AttachmentSummary {
  id: string;
  conversation_id: string;
  filename: string;
  mime_type: string;
  kind: AttachmentKind;
  size_bytes: number;
  has_extracted_text: boolean;
  preview?: string | null;
  extraction_note?: string | null;
  uploaded_at: string;
}

export interface MessageImage {
  url: string;
  alt: string;
  caption?: string | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender: MessageSender;
  text: string;
  created_at: string;
  citations: Citation[];
  quick_replies: string[];
  process_trace: ProcessStep[];
  knowledge_graph?: KnowledgeGraph | null;
  attachments: AttachmentSummary[];
  images?: MessageImage[];
  vote: VoteValue | null;
  vote_reason?: string | null;
  is_grounded: boolean;
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  status: ConversationStatus;
  created_at: string;
  messages: Message[];
}

export interface ConversationSummary {
  id: string;
  title: string;
  status: ConversationStatus;
  created_at: string;
  /** Time of the last message (or creation if empty) — drives history ordering. */
  updated_at: string;
  last_message_preview?: string | null;
}

export interface HandoffContact {
  label: string;
  value: string;
  icon: string;
}

export interface HandoffInfo {
  message: string;
  contacts: HandoffContact[];
  queue_position?: number | null;
}

export interface KpiCards {
  conversations: number;
  total_messages: number;
  unique_users: number;
  messages_today: number;
}

export interface QualityRings {
  grounding_rate: number;
  satisfaction: number;
}

export interface FeedbackBreakdown {
  positive: number;
  negative: number;
}

export interface ActivityPoint {
  day: string;
  value: number;
}

export interface DashboardResponse {
  kpis: KpiCards;
  quality: QualityRings;
  feedback_breakdown: FeedbackBreakdown;
  activity: ActivityPoint[];
}

export type DocumentType = "PDF" | "MD";

export interface Correction {
  text: string;
  document_filename?: string | null;
  created_at: string;
}

export interface FeedbackItem {
  id: string;
  conversation_id: string;
  message_id?: string | null;
  query: string;
  sentiment: VoteValue;
  stars?: number | null;
  comment?: string | null;
  created_at: string;
  user_name: string;
  correction?: Correction | null;
}

export interface DocumentItem {
  id: string;
  filename: string;
  category: string;
  file_type: DocumentType;
  updated_at: string;
}
