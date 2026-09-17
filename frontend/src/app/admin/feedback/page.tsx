"use client";

import { useEffect, useMemo, useState } from "react";

import { FeedbackListItem } from "@/components/admin/FeedbackListItem";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { FeedbackItem } from "@/lib/types";

type Filter = "all" | "positive" | "negative";

export default function AdminFeedbackPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    api
      .listFeedback(token)
      .then(setItems)
      .finally(() => setLoading(false));
  }, [token]);

  const filtered = useMemo(() => {
    if (filter === "all") return items;
    return items.filter((item) => (filter === "positive" ? item.sentiment === "up" : item.sentiment === "down"));
  }, [items, filter]);

  const handleCorrectionSaved = (updated: FeedbackItem) => {
    setItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
  };

  return (
    <div className="flex flex-col gap-5">
      <div className="flex gap-1 self-start rounded-pill bg-surface-2 p-1">
        {(["all", "positive", "negative"] as Filter[]).map((f) => (
          <button
            key={f}
            type="button"
            onClick={() => setFilter(f)}
            className={[
              "rounded-pill px-4 py-2 font-body text-sm font-medium capitalize transition-colors",
              filter === f ? "bg-surface text-accent shadow-sm" : "text-text-dim hover:text-text",
            ].join(" ")}
          >
            {f}
          </button>
        ))}
      </div>

      {loading || !token ? (
        <p className="font-body text-md text-text-dim">Loading feedback...</p>
      ) : filtered.length === 0 ? (
        <p className="font-body text-md text-text-dim">No feedback in this category yet.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {filtered.map((item) => (
            <FeedbackListItem key={item.id} item={item} token={token} onCorrectionSaved={handleCorrectionSaved} />
          ))}
        </div>
      )}
    </div>
  );
}
