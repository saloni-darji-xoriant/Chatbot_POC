import type { Citation } from "@/lib/types";

export function CitationChip({ citation }: { citation: Citation }) {
  return (
    <span
      title={citation.section ?? citation.document}
      className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface-2 px-2.5 py-1.5 font-mono text-xs text-text-dim"
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
        <path d="M14 2v6h6" />
      </svg>
      {citation.document}
    </span>
  );
}
