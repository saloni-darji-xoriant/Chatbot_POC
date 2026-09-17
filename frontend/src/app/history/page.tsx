"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Badge, Card, Input } from "@/components/ui";
import { Sidebar } from "@/components/layout/Sidebar";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { ConversationSummary } from "@/lib/types";

const STATUS_TONE: Record<ConversationSummary["status"], "positive" | "negative" | "neutral"> = {
  resolved: "positive",
  handoff: "negative",
  active: "neutral",
};

const STATUS_LABEL: Record<ConversationSummary["status"], string> = {
  resolved: "Resolved",
  handoff: "Escalated",
  active: "In progress",
};

export default function HistoryPage() {
  const { user, token, isLoading } = useAuth();
  const router = useRouter();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    api
      .listConversations(token)
      .then(setConversations)
      .finally(() => setLoading(false));
  }, [token]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return conversations;
    return conversations.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        (c.last_message_preview ?? "").toLowerCase().includes(q)
    );
  }, [conversations, query]);

  if (!user) return null;

  return (
    <div className="flex min-h-screen bg-bg">
      <Sidebar />

      <main className="flex flex-1 flex-col overflow-y-auto px-6 py-8">
        <div className="mx-auto flex w-full max-w-chat flex-col gap-5">
          <div>
            <h1 className="font-display text-2xl font-semibold text-text">History</h1>
            <p className="mt-1 font-body text-sm text-text-dim">
              Every conversation you&apos;ve had with the assistant.
            </p>
          </div>

          <Input
            aria-label="Search conversations"
            placeholder="Search conversations..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />

          {loading ? (
            <p className="font-body text-md text-text-dim">Loading history...</p>
          ) : filtered.length === 0 ? (
            <p className="font-body text-md text-text-dim">
              {conversations.length === 0
                ? "You haven't started a conversation yet."
                : "No conversations match your search."}
            </p>
          ) : (
            <div className="flex flex-col gap-3">
              {filtered.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => router.push(`/chat?conversationId=${c.id}`)}
                  className="text-left"
                >
                  <Card className="flex flex-col gap-1.5 transition-colors hover:border-accent">
                    <div className="flex items-center justify-between gap-3">
                      <p className="truncate font-body text-md font-semibold text-text">{c.title}</p>
                      <Badge tone={STATUS_TONE[c.status]}>{STATUS_LABEL[c.status]}</Badge>
                    </div>
                    {c.last_message_preview && (
                      <p className="truncate font-body text-sm text-text-dim">{c.last_message_preview}</p>
                    )}
                    <p className="font-mono text-xs text-text-dim">
                      {new Date(c.created_at).toLocaleString()}
                    </p>
                  </Card>
                </button>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
