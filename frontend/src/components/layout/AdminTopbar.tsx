"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/admin/dashboard", label: "Dashboard" },
  { href: "/admin/feedback", label: "Feedback" },
  // Documents tab temporarily hidden from admin nav — the /admin/documents
  // route, its page, and the backend endpoint are all still fully working;
  // uncomment this entry to relink it.
  // { href: "/admin/documents", label: "Documents" },
];

export function AdminTopbar({ onRefresh }: { onRefresh?: () => void }) {
  const pathname = usePathname();

  return (
    <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3 sm:px-6 sm:py-4">
      <div className="flex gap-1 overflow-x-auto rounded-pill bg-surface-2 p-1">
        {TABS.map((tab) => {
          const isActive = pathname.startsWith(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={[
                "shrink-0 rounded-pill px-3 py-2 font-body text-md font-medium transition-colors sm:px-4",
                isActive ? "bg-surface text-accent shadow-sm" : "text-text-dim hover:text-text",
              ].join(" ")}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>
      {onRefresh && (
        <button
          type="button"
          onClick={onRefresh}
          aria-label="Refresh"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border text-text-dim hover:border-accent hover:text-accent"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M23 4v6h-6M1 20v-6h6" />
            <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
          </svg>
        </button>
      )}
    </div>
  );
}
