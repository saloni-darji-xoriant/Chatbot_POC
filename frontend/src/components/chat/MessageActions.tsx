"use client";

import { useState } from "react";

import type { VoteValue } from "@/lib/types";

interface MessageActionsProps {
  vote: VoteValue | null;
  voteReason?: string | null;
  onVote: (vote: VoteValue | null, reason?: string) => void;
  // Trace option is commented out for now (kept for future use) - these props are
  // therefore optional and currently unused. Restore with the button below.
  hasTrace?: boolean;
  traceActive?: boolean;
  onToggleTrace?: () => void;
}

export function MessageActions({
  vote,
  voteReason,
  onVote,
  // hasTrace,
  // traceActive,
  // onToggleTrace,
}: MessageActionsProps) {
  const [showReasonInput, setShowReasonInput] = useState(false);
  const [reason, setReason] = useState(voteReason ?? "");

  const handleUp = () => {
    setShowReasonInput(false);
    onVote(vote === "up" ? null : "up");
  };

  const handleDown = () => {
    if (vote === "down") {
      setShowReasonInput(false);
      onVote(null);
      return;
    }
    onVote("down");
    setShowReasonInput(true);
  };

  const handleSaveReason = () => {
    onVote("down", reason.trim() || undefined);
    setShowReasonInput(false);
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-1.5">
        <button
          type="button"
          aria-label="Thumbs up"
          aria-pressed={vote === "up"}
          onClick={handleUp}
          className={[
            "flex h-[26px] w-[26px] items-center justify-center rounded-sm transition-colors",
            vote === "up" ? "bg-accent-2-soft text-accent-2" : "text-text-dim hover:bg-surface-2",
          ].join(" ")}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M7 10v12M15 5.88L14 10h6.31a2 2 0 011.94 2.5l-2.36 9A2 2 0 0117.94 23H7a2 2 0 01-2-2V10a2 2 0 012-2h1.62a2 2 0 001.78-1.06L14 2v0a2.5 2.5 0 011 3.88z" />
          </svg>
        </button>
        <button
          type="button"
          aria-label="Thumbs down"
          aria-pressed={vote === "down"}
          onClick={handleDown}
          className={[
            "flex h-[26px] w-[26px] items-center justify-center rounded-sm transition-colors",
            vote === "down" ? "bg-danger-soft text-danger" : "text-text-dim hover:bg-surface-2",
          ].join(" ")}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M17 14V2M9 18.12L10 14H3.69a2 2 0 01-1.94-2.5l2.36-9A2 2 0 016.06 1H17a2 2 0 012 2v11a2 2 0 01-2 2h-1.62a2 2 0 00-1.78 1.06L10 22v0a2.5 2.5 0 01-1-3.88z" />
          </svg>
        </button>

        {/* Trace option - commented out for now; uncomment (and the props above) to bring it back.
        {hasTrace && (
          <button
            type="button"
            aria-label="View developer trace"
            aria-pressed={traceActive}
            onClick={onToggleTrace}
            className={[
              "flex h-[26px] items-center gap-1 rounded-sm px-2 font-body text-xs font-medium transition-colors",
              traceActive ? "bg-accent-soft text-accent" : "text-text-dim hover:bg-surface-2",
            ].join(" ")}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 3h6M10 3v3.5a4 4 0 01-.8 2.4L5.6 13.8A4 4 0 005 16v0a4 4 0 004 4h6a4 4 0 004-4v0a4 4 0 00-.6-2.2l-3.6-4.9A4 4 0 0114 6.5V3M8.5 14.5h7" />
            </svg>
            Trace
          </button>
        )}
        */}
      </div>

      {showReasonInput && (
        <div className="flex max-w-[360px] items-center gap-2">
          <input
            autoFocus
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSaveReason()}
            placeholder="What was wrong? (optional)"
            aria-label="Reason for thumbs down"
            className="flex-1 rounded-md border border-border bg-surface px-2.5 py-1.5 font-body text-sm text-text placeholder:text-text-dim outline-none focus:border-accent"
          />
          <button
            type="button"
            onClick={handleSaveReason}
            className="rounded-md bg-surface-2 px-2.5 py-1.5 font-body text-sm font-medium text-text-dim hover:text-text"
          >
            Save
          </button>
        </div>
      )}

      {!showReasonInput && vote === "down" && voteReason && (
        <p className="max-w-[360px] font-body text-sm italic text-text-dim">&ldquo;{voteReason}&rdquo;</p>
      )}
    </div>
  );
}
