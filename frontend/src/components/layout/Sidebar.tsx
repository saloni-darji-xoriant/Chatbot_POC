"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/context/AuthContext";
import { useChat } from "@/context/ChatContext";
import { api } from "@/lib/api";
import type { ConversationSummary } from "@/lib/types";
import { ProfileCard } from "./ProfileCard";

const NAV_ITEMS = [
  { href: "/chat", label: "AI Support", adminOnly: false },
  { href: "/history", label: "History", adminOnly: false },
  { href: "/admin/dashboard", label: "Admin", adminOnly: true },
  { href: "/help", label: "Help", adminOnly: false },
];

export function Sidebar() {
  const { user, token, logout } = useAuth();
  const { resetConversation, conversation } = useChat();
  const pathname = usePathname();
  const router = useRouter();
  const [recent, setRecent] = useState<ConversationSummary[]>([]);

  useEffect(() => {
    if (!token) return;
    api
      .listConversations(token)
      .then((all) => setRecent(all.slice(0, 5)))
      .catch(() => setRecent([]));
    // Re-fetch whenever the active conversation changes so a newly created
    // or updated conversation shows up here without a full page reload.
  }, [token, conversation?.id, conversation?.messages.length]);

  if (!user) return null;

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const handleNewQuestion = () => {
    resetConversation();
    router.push("/chat");
  };

  return (
    <aside className="flex h-screen w-sidebar shrink-0 flex-col border-r border-border bg-surface p-[18px_14px]">
      <div className="flex items-center gap-2.5 px-1 pb-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-sm bg-brand-gradient font-display text-md font-bold text-accent-ink">
          Q
        </div>
        <span className="font-display text-md font-semibold text-text">Qcells L1 Assistant</span>
      </div>

      <button
        type="button"
        onClick={handleNewQuestion}
        className="mb-5 flex items-center justify-center gap-2 rounded-pill bg-brand-gradient px-4 py-[10px] font-body text-md font-semibold text-accent-ink"
      >
        + New question
      </button>

      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.filter((item) => !item.adminOnly || user.role === "admin").map((item) => {
          const isActive = pathname.startsWith(item.href.split("?")[0]);
          return (
            <Link
              key={item.label}
              href={item.href}
              className={[
                "rounded-md px-3 py-2 font-body text-md transition-colors",
                isActive ? "bg-accent-soft font-medium text-accent" : "text-text-dim hover:bg-surface-2",
              ].join(" ")}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-5 flex-1 overflow-y-auto">
        <p className="px-3 pb-2 font-body text-xs font-semibold uppercase tracking-wide text-text-dim">
          Recent
        </p>
        {recent.length === 0 ? (
          <p className="px-3 font-body text-sm text-text-dim">Your recent conversations will appear here.</p>
        ) : (
          <div className="flex flex-col gap-0.5">
            {recent.map((c) => (
              <Link
                key={c.id}
                href={`/chat?conversationId=${c.id}`}
                className="truncate rounded-md px-3 py-1.5 font-body text-sm text-text-dim hover:bg-surface-2 hover:text-text"
                title={c.title}
              >
                {c.title}
              </Link>
            ))}
          </div>
        )}
      </div>

      <div className="mt-4 flex flex-col gap-2">
        <ProfileCard user={user} />
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-md px-3 py-2 text-left font-body text-sm font-medium text-text-dim hover:bg-surface-2"
        >
          Log out
        </button>
      </div>
    </aside>
  );
}
