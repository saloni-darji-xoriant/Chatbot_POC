"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Badge, Card, Input } from "@/components/ui";
import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import {
  HISTORY_SORT_LABELS,
  formatDateTime,
  groupByDay,
  sortConversations,
  type HistorySort,
} from "@/lib/history";
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
  const [sort, setSort] = useState<HistorySort>("newest");

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
    const matches = !q
      ? conversations
      : conversations.filter(
          (c) =>
            c.title.toLowerCase().includes(q) ||
            (c.last_message_preview ?? "").toLowerCase().includes(q)
        );
    return sortConversations(matches, sort);
  }, [conversations, query, sort]);

  const groups = useMemo(() => groupByDay(filtered), [filtered]);

  if (!user) return null;

  return (
    <AppShell>
      <div className="flex flex-1 flex-col overflow-y-auto px-4 py-6 sm:px-6 sm:py-8">
        <div className="mx-auto flex w-full max-w-chat flex-col gap-5">
          <div>
            <h1 className="font-display text-2xl font-semibold text-text">History</h1>
            <p className="mt-1 font-body text-sm text-text-dim">
              Every conversation you&apos;ve had with the assistant.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="flex-1">
              <Input
                aria-label="Search conversations"
                placeholder="Search conversations..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <label className="flex items-center gap-2 font-body text-sm text-text-dim">
              Sort by date
              <select
                aria-label="Sort conversations by date and time"
                value={sort}
                onChange={(e) => setSort(e.target.value as HistorySort)}
                className="rounded-md border border-border bg-surface px-2.5 py-2 font-body text-sm text-text outline-none focus:border-accent"
              >
                {(Object.keys(HISTORY_SORT_LABELS) as HistorySort[]).map((key) => (
                  <option key={key} value={key}>
                    {HISTORY_SORT_LABELS[key]}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {loading ? (
            <p className="font-body text-md text-text-dim">Loading history...</p>
          ) : filtered.length === 0 ? (
            <p className="font-body text-md text-text-dim">
              {conversations.length === 0
                ? "You haven't started a conversation yet."
                : "No conversations match your search."}
            </p>
          ) : (
            <div className="flex flex-col gap-5">
              {groups.map((group) => (
                <section key={group.label} aria-label={group.label} className="flex flex-col gap-3">
                  <h2 className="font-body text-xs font-semibold uppercase tracking-wide text-text-dim">
                    {group.label}
                  </h2>
                  {group.items.map((c) => (
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
                          {formatDateTime(c.updated_at ?? c.created_at)}
                        </p>
                      </Card>
                    </button>
                  ))}
                </section>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
