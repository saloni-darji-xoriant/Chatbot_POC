"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { api } from "@/lib/api";
import type {
  AttachmentSummary,
  Conversation,
  ConversationStatus,
  HandoffInfo,
  Message,
  ProcessStep,
  VoteValue,
} from "@/lib/types";
import { useAuth } from "./AuthContext";

interface ChatContextValue {
  conversation: Conversation | null;
  status: ConversationStatus | "idle";
  isSending: boolean;
  liveTrace: ProcessStep[] | null;
  handoffInfo: HandoffInfo | null;
  error: string | null;
  pendingAttachments: AttachmentSummary[];
  isUploadingAttachment: boolean;
  attachmentError: string | null;
  startConversation: () => Promise<void>;
  loadConversation: (id: string) => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  attachFile: (file: File) => Promise<void>;
  removeAttachment: (id: string) => Promise<void>;
  voteOnMessage: (messageId: string, vote: VoteValue | null, reason?: string) => Promise<void>;
  submitRating: (stars: number, thumbs: VoteValue | null, comment: string) => Promise<void>;
  resetConversation: () => void;
}

const ChatContext = createContext<ChatContextValue | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [liveTrace, setLiveTrace] = useState<ProcessStep[] | null>(null);
  const [handoffInfo, setHandoffInfo] = useState<HandoffInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pendingAttachments, setPendingAttachments] = useState<AttachmentSummary[]>([]);
  const [isUploadingAttachment, setIsUploadingAttachment] = useState(false);
  const [attachmentError, setAttachmentError] = useState<string | null>(null);

  const startConversation = useCallback(async () => {
    if (!token) return;
    setError(null);
    const conv = await api.createConversation(token);
    setConversation(conv);
    setHandoffInfo(null);
  }, [token]);

  const loadConversation = useCallback(
    async (id: string) => {
      if (!token) return;
      setError(null);
      const conv = await api.getConversation(token, id);
      setConversation(conv);
      setHandoffInfo(null);
      setPendingAttachments([]);
      if (conv.status === "handoff") {
        try {
          const info = await api.triggerHandoff(token, id);
          setHandoffInfo(info);
        } catch {
          // best-effort — the conversation still loads without fresh contact info
        }
      }
    },
    [token]
  );

  /** Creates a conversation on first use — shared by sendMessage and
   * attachFile, since a user can attach a file before typing anything. */
  const ensureConversation = useCallback(async (): Promise<Conversation> => {
    if (conversation) return conversation;
    if (!token) throw new Error("Not authenticated");
    const conv = await api.createConversation(token);
    setConversation(conv);
    return conv;
  }, [token, conversation]);

  const attachFile = useCallback(
    async (file: File) => {
      if (!token) return;
      setAttachmentError(null);
      setIsUploadingAttachment(true);
      try {
        const conv = await ensureConversation();
        // Uploaded (and text-extracted) immediately on selection, well before
        // the user hits send — so send-time latency is unaffected by file
        // parsing, and the attachment is already searchable by the time
        // they ask a question about it.
        const summary = await api.uploadAttachment(token, conv.id, file);
        setPendingAttachments((prev) => [...prev, summary]);
      } catch (err) {
        setAttachmentError(err instanceof Error ? err.message : "Could not attach that file");
      } finally {
        setIsUploadingAttachment(false);
      }
    },
    [token, ensureConversation]
  );

  const removeAttachment = useCallback(
    async (id: string) => {
      if (!token || !conversation) return;
      setPendingAttachments((prev) => prev.filter((a) => a.id !== id));
      try {
        await api.deleteAttachment(token, conversation.id, id);
      } catch {
        // already removed from the pending list client-side; a stale
        // server-side record is harmless and self-limited by the per-
        // conversation attachment cap
      }
    },
    [token, conversation]
  );

  const sendMessage = useCallback(
    async (text: string) => {
      if (!token) return;
      setError(null);
      const conv = await ensureConversation();
      const attachmentsForMessage = pendingAttachments;

      const optimisticId = `temp_${Date.now()}`;
      const optimisticUser: Message = {
        id: optimisticId,
        conversation_id: conv.id,
        sender: "user",
        text,
        created_at: new Date().toISOString(),
        citations: [],
        quick_replies: [],
        process_trace: [],
        attachments: attachmentsForMessage,
        vote: null,
        is_grounded: true,
      };
      setConversation((prev) =>
        prev ? { ...prev, messages: [...prev.messages, optimisticUser] } : prev
      );
      setPendingAttachments([]);
      setIsSending(true);
      setLiveTrace(null);

      const convId = conv.id;
      await api.streamMessage(
        token,
        convId,
        text,
        {
          onUserMessage: (real) => {
            setConversation((prev) =>
              prev
                ? { ...prev, messages: prev.messages.map((m) => (m.id === optimisticId ? real : m)) }
                : prev
            );
          },
          onTrace: (steps) => setLiveTrace(steps),
          onAssistantMessage: (assistantMsg) => {
            setConversation((prev) =>
              prev ? { ...prev, messages: [...prev.messages, assistantMsg] } : prev
            );
            setLiveTrace(null);
          },
          onHandoff: (info) => setHandoffInfo(info),
          onDone: (nextStatus) => {
            setConversation((prev) => (prev ? { ...prev, status: nextStatus } : prev));
          },
          onError: (message) => setError(message),
        },
        attachmentsForMessage.map((a) => a.id)
      );

      setIsSending(false);
    },
    [token, ensureConversation, pendingAttachments]
  );

  const voteOnMessage = useCallback(
    async (messageId: string, vote: VoteValue | null, reason?: string) => {
      if (!token) return;
      const updated = await api.voteMessage(token, messageId, vote, reason);
      setConversation((prev) =>
        prev
          ? { ...prev, messages: prev.messages.map((m) => (m.id === messageId ? updated : m)) }
          : prev
      );
    },
    [token]
  );

  const submitRating = useCallback(
    async (stars: number, thumbs: VoteValue | null, comment: string) => {
      if (!token || !conversation) return;
      await api.rateConversation(token, conversation.id, {
        stars,
        thumbs: thumbs ?? undefined,
        comment: comment || undefined,
      });
      setConversation((prev) => (prev ? { ...prev, status: "resolved" } : prev));
    },
    [token, conversation]
  );

  const resetConversation = useCallback(() => {
    setConversation(null);
    setHandoffInfo(null);
    setError(null);
    setLiveTrace(null);
    setPendingAttachments([]);
    setAttachmentError(null);
  }, []);

  const value = useMemo<ChatContextValue>(
    () => ({
      conversation,
      status: conversation?.status ?? "idle",
      isSending,
      liveTrace,
      handoffInfo,
      error,
      pendingAttachments,
      isUploadingAttachment,
      attachmentError,
      startConversation,
      loadConversation,
      sendMessage,
      attachFile,
      removeAttachment,
      voteOnMessage,
      submitRating,
      resetConversation,
    }),
    [
      conversation,
      isSending,
      liveTrace,
      handoffInfo,
      error,
      pendingAttachments,
      isUploadingAttachment,
      attachmentError,
      startConversation,
      loadConversation,
      sendMessage,
      attachFile,
      removeAttachment,
      voteOnMessage,
      submitRating,
      resetConversation,
    ]
  );

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat(): ChatContextValue {
  const ctx = useContext(ChatContext);
  if (!ctx) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return ctx;
}
