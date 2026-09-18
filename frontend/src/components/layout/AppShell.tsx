"use client";

import { useState, type ReactNode } from "react";

import { Sidebar } from "./Sidebar";

interface AppShellProps {
  children: ReactNode;
}

/**
 * Shared responsive frame for every signed-in page (chat/history/help/admin):
 * a static sidebar from the `nav` breakpoint (900px, matching the tablet
 * breakpoint in qcells-l1-assistant-mockups.html) up, collapsing to a
 * hamburger-triggered off-canvas drawer below it. Centralizing this here
 * means the mobile-nav behavior is implemented once instead of once per page.
 */
export function AppShell({ children }: AppShellProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-bg">
      <Sidebar isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />

      {drawerOpen && (
        <div
          aria-hidden="true"
          onClick={() => setDrawerOpen(false)}
          className="fixed inset-0 z-30 bg-black/40 nav:hidden"
        />
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-3 border-b border-border bg-surface px-4 py-3 nav:hidden">
          <button
            type="button"
            aria-label="Open menu"
            onClick={() => setDrawerOpen(true)}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-text-dim hover:bg-surface-2"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18M3 12h18M3 18h18" />
            </svg>
          </button>
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-sm bg-brand-gradient font-display text-sm font-bold text-accent-ink">
            Q
          </div>
          <span className="truncate font-display text-md font-semibold text-text">Qcells L1 Assistant</span>
        </div>

        <main className="flex min-h-0 flex-1 flex-col">{children}</main>
      </div>
    </div>
  );
}
