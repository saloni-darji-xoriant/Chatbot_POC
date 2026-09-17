import type {
  Conversation,
  ConversationStatus,
  ConversationSummary,
  DashboardResponse,
  DocumentItem,
  FeedbackItem,
  HandoffContact,
  HandoffInfo,
  Message,
  ProcessStep,
  User,
  VoteValue,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { token?: string | null } = {}
): Promise<T> {
  const { token, headers, ...rest } = options;
  const res = await fetch(`${API_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore json parse errors, fall back to statusText
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export interface StreamHandlers {
  onUserMessage?: (message: Message) => void;
  onTrace?: (steps: ProcessStep[]) => void;
  onAssistantMessage?: (message: Message) => void;
  onHandoff?: (info: HandoffInfo) => void;
  onDone?: (status: ConversationStatus) => void;
  onError?: (message: string) => void;
}

/**
 * Consumes the backend's `text/event-stream` chat response. We use `fetch`
 * with a manual reader (rather than the native `EventSource`) because
 * EventSource only supports unauthenticated GET requests — this endpoint
 * needs a POST body and a bearer token.
 */
async function streamMessage(
  token: string,
  conversationId: string,
  text: string,
  handlers: StreamHandlers
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/chat/conversations/${conversationId}/messages/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ text }),
    });
  } catch {
    handlers.onError?.("Could not reach the assistant. Check your connection and try again.");
    return;
  }

  if (!res.ok || !res.body) {
    handlers.onError?.(`Request failed (${res.status})`);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const dispatch = (eventName: string, dataStr: string) => {
    if (!dataStr) return;
    let data: unknown;
    try {
      data = JSON.parse(dataStr);
    } catch {
      return;
    }
    switch (eventName) {
      case "user_message":
        handlers.onUserMessage?.(data as Message);
        break;
      case "trace":
        handlers.onTrace?.((data as { steps: ProcessStep[] }).steps);
        break;
      case "assistant_message":
        handlers.onAssistantMessage?.(data as Message);
        break;
      case "handoff":
        handlers.onHandoff?.(data as HandoffInfo);
        break;
      case "done":
        handlers.onDone?.((data as { conversation_status: ConversationStatus }).conversation_status);
        break;
      case "error":
        handlers.onError?.((data as { message: string }).message);
        break;
    }
  };

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sepIndex = buffer.indexOf("\n\n");
    while (sepIndex !== -1) {
      const rawEvent = buffer.slice(0, sepIndex);
      buffer = buffer.slice(sepIndex + 2);

      let eventName = "message";
      let dataStr = "";
      for (const line of rawEvent.split("\n")) {
        if (line.startsWith("event:")) eventName = line.slice(6).trim();
        else if (line.startsWith("data:")) dataStr += line.slice(5).trim();
      }
      dispatch(eventName, dataStr);
      sepIndex = buffer.indexOf("\n\n");
    }
  }
}

export const api = {
  login: (email: string, password: string) =>
    request<{ token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  ssoLogin: (email: string) =>
    request<{ token: string; user: User }>("/auth/sso", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  me: (token: string) => request<User>("/auth/me", { token }),

  createConversation: (token: string, title?: string) =>
    request<Conversation>("/chat/conversations", {
      method: "POST",
      token,
      body: JSON.stringify({ title }),
    }),

  listConversations: (token: string) =>
    request<ConversationSummary[]>("/chat", { token }),

  getConversation: (token: string, id: string) =>
    request<Conversation>(`/chat/conversations/${id}`, { token }),

  streamMessage,

  voteMessage: (token: string, messageId: string, vote: VoteValue | null, reason?: string) =>
    request<Message>(`/chat/messages/${messageId}/vote`, {
      method: "POST",
      token,
      body: JSON.stringify({ vote, reason }),
    }),

  triggerHandoff: (token: string, conversationId: string, reason?: string) =>
    request<HandoffInfo>(`/chat/conversations/${conversationId}/handoff`, {
      method: "POST",
      token,
      body: JSON.stringify({ reason }),
    }),

  rateConversation: (
    token: string,
    conversationId: string,
    payload: { stars: number; thumbs?: VoteValue | null; comment?: string }
  ) =>
    request(`/chat/conversations/${conversationId}/rating`, {
      method: "POST",
      token,
      body: JSON.stringify(payload),
    }),

  helpContacts: (token: string) => request<HandoffContact[]>("/chat/help-contacts", { token }),

  getDashboard: (token: string) => request<DashboardResponse>("/admin/dashboard", { token }),

  listFeedback: (token: string) => request<FeedbackItem[]>("/admin/feedback", { token }),

  submitCorrection: (
    token: string,
    feedbackId: string,
    payload: { text: string; document_filename?: string; add_as_document?: boolean }
  ) =>
    request<FeedbackItem>(`/admin/feedback/${feedbackId}/correction`, {
      method: "POST",
      token,
      body: JSON.stringify(payload),
    }),

  listDocuments: (token: string) => request<DocumentItem[]>("/admin/documents", { token }),

  listAdminConversations: (token: string) =>
    request<ConversationSummary[]>("/admin/conversations", { token }),

  getAdminConversation: (token: string, id: string) =>
    request<Conversation>(`/admin/conversations/${id}`, { token }),
};
