"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { Composer } from "@/components/chat/Composer";
import { EndOfConversationRating } from "@/components/chat/EndOfConversationRating";
import { ErrorBanner } from "@/components/chat/ErrorBanner";
import { HandoffScreen } from "@/components/chat/HandoffScreen";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { LiveProcessTrace } from "@/components/chat/ProcessTrace";
import { SuggestionChip } from "@/components/chat/SuggestionChip";
import { Sidebar } from "@/components/layout/Sidebar";
import { useAuth } from "@/context/AuthContext";
import { useChat } from "@/context/ChatContext";
import { SUGGESTED_QUESTIONS } from "@/lib/constants";

function ChatPageInner() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const conversationIdParam = searchParams.get("conversationId");
  const {
    conversation,
    status,
    isSending,
    liveTrace,
    handoffInfo,
    error,
    pendingAttachments,
    isUploadingAttachment,
    attachmentError,
    loadConversation,
    sendMessage,
    attachFile,
    removeAttachment,
    voteOnMessage,
    submitRating,
    resetConversation,
  } = useChat();
  const [showRating, setShowRating] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  useEffect(() => {
    if (conversationIdParam && conversation?.id !== conversationIdParam) {
      loadConversation(conversationIdParam);
    }
  }, [conversationIdParam, conversation?.id, loadConversation]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [conversation?.messages.length, isSending]);

  if (!user) return null;

  const messages = conversation?.messages ?? [];
  const isEmpty = messages.length === 0;

  const backToFreshChat = () => {
    resetConversation();
    router.push("/chat");
  };

  return (
    <div className="flex min-h-screen bg-bg">
      <Sidebar />

      <main className="flex flex-1 flex-col">
        {status === "handoff" && handoffInfo ? (
          <div className="flex-1 overflow-y-auto px-6">
            <HandoffScreen handoff={handoffInfo} onBackToChat={backToFreshChat} />
          </div>
        ) : (
          <>
            <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-8">
              <div className="mx-auto flex w-full max-w-chat flex-col gap-6">
                {isEmpty && !isSending && (
                  <div className="flex flex-col items-center gap-6 pt-16 text-center">
                    <h1 className="brand-gradient-text font-display text-4xl font-semibold">
                      Hi {user.name.split(" ")[0]}, how can I help?
                    </h1>
                    <p className="max-w-md font-body text-md text-text-dim">
                      Ask about inverter faults, panel output, warranty claims, firmware, or
                      installation steps — I&apos;ll answer from the Qcells knowledge base. You can
                      also attach a site photo or document for me to reference.
                    </p>
                    <div className="flex flex-wrap justify-center gap-2.5">
                      {SUGGESTED_QUESTIONS.map((q) => (
                        <SuggestionChip key={q} label={q} onClick={() => sendMessage(q)} />
                      ))}
                    </div>
                  </div>
                )}

                {messages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    onVote={
                      message.sender === "assistant"
                        ? (vote, reason) => voteOnMessage(message.id, vote, reason)
                        : undefined
                    }
                    onQuickReply={message.sender === "assistant" ? (text) => sendMessage(text) : undefined}
                  />
                ))}

                {isSending && <LiveProcessTrace steps={liveTrace} />}

                {error && <ErrorBanner message={error} />}

                {showRating && (
                  <EndOfConversationRating
                    onSubmit={submitRating}
                    onDismiss={() => {
                      setShowRating(false);
                      backToFreshChat();
                    }}
                  />
                )}
              </div>
            </div>

            {!showRating && (
              <div className="border-t border-border bg-bg px-6 py-4">
                <div className="mx-auto flex w-full max-w-chat flex-col gap-2">
                  {!isEmpty && status !== "resolved" && (
                    <button
                      type="button"
                      onClick={() => setShowRating(true)}
                      className="self-end font-body text-sm font-medium text-accent underline"
                    >
                      Mark as resolved
                    </button>
                  )}
                  <Composer
                    onSend={sendMessage}
                    disabled={isSending}
                    attachments={pendingAttachments}
                    isUploadingAttachment={isUploadingAttachment}
                    attachmentError={attachmentError}
                    onAttach={attachFile}
                    onRemoveAttachment={removeAttachment}
                  />
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={null}>
      <ChatPageInner />
    </Suspense>
  );
}
