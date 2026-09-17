"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/admin/dashboard", label: "Dashboard" },
  { href: "/admin/feedback", label: "Feedback" },
  { href: "/admin/documents", label: "Documents" },
];

export function AdminTopbar({ onRefresh }: { onRefresh?: () => void }) {
  const pathname = usePathname();

  return (
    <div className="flex items-center justify-between border-b border-border px-6 py-4">
      <div className="flex gap-1 rounded-pill bg-surface-2 p-1">
        {TABS.map((tab) => {
          const isActive = pathname.startsWith(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={[
                "rounded-pill px-4 py-2 font-body text-md font-medium transition-colors",
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
          className="flex h-9 w-9 items-center justify-center rounded-full border border-border text-text-dim hover:border-accent hover:text-accent"
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
