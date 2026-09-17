import type { AttachmentSummary } from "@/lib/types";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

interface AttachmentChipProps {
  attachment: AttachmentSummary;
  onRemove?: () => void;
}

export function AttachmentChip({ attachment, onRemove }: AttachmentChipProps) {
  return (
    <span
      title={attachment.extraction_note ?? attachment.preview ?? attachment.filename}
      className="inline-flex max-w-full items-center gap-1.5 rounded-md border border-border bg-surface-2 py-1.5 pl-2 pr-2.5 font-body text-sm text-text-dim"
    >
      {attachment.kind === "image" ? (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <path d="M21 15l-5-5L5 21" />
        </svg>
      ) : (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
          <path d="M14 2v6h6" />
        </svg>
      )}
      <span className="max-w-[160px] truncate text-text">{attachment.filename}</span>
      <span className="font-mono text-xs text-text-dim">{formatSize(attachment.size_bytes)}</span>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Remove ${attachment.filename}`}
          className="ml-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-text-dim hover:bg-danger-soft hover:text-danger"
        >
          ×
        </button>
      )}
    </span>
  );
}
