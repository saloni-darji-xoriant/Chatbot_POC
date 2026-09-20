"use client";

import { useState } from "react";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { downloadBlob, viewerTimeZone } from "@/lib/download";

/** Downloads the current conversation as a PDF, with times in the viewer's timezone. */
export function ExportPdfButton({ conversationId }: { conversationId: string }) {
  const { token } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    if (!token || busy) return;
    setBusy(true);
    setError(null);
    try {
      const { blob, filename } = await api.exportConversationPdf(token, conversationId, viewerTimeZone());
      downloadBlob(blob, filename);
    } catch {
      setError("Couldn't export the chat. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      {error && (
        <span role="alert" className="font-body text-xs text-danger">
          {error}
        </span>
      )}
      <button
        type="button"
        onClick={handleExport}
        disabled={busy}
        aria-label="Export chat as PDF"
        className="flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-1.5 font-body text-sm font-medium text-text-dim transition-colors hover:border-accent hover:text-accent disabled:cursor-not-allowed disabled:opacity-60"
      >
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
        </svg>
        {busy ? "Preparing PDF..." : "Export PDF"}
      </button>
    </div>
  );
}
