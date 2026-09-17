import { Badge, Card } from "@/components/ui";
import type { DocumentItem } from "@/lib/types";

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (days < 1) return "today";
  if (days === 1) return "1 day ago";
  if (days < 30) return `${days} days ago`;
  const months = Math.floor(days / 30);
  return `${months} month${months > 1 ? "s" : ""} ago`;
}

export function DocumentListItem({ doc }: { doc: DocumentItem }) {
  return (
    <Card className="flex items-center gap-3.5">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-sm bg-accent-soft text-accent">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
          <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" />
        </svg>
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate font-body text-md font-semibold text-text">{doc.filename}</p>
        <p className="font-body text-sm text-text-dim">
          Updated {timeAgo(doc.updated_at)} · {doc.category}
        </p>
      </div>
      <Badge tone="neutral">{doc.file_type}</Badge>
    </Card>
  );
}
