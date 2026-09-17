import type { FeedbackBreakdown } from "@/lib/types";

export function FeedbackBreakdownBar({ breakdown }: { breakdown: FeedbackBreakdown }) {
  const total = breakdown.positive + breakdown.negative || 1;
  const positivePct = (breakdown.positive / total) * 100;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex h-3 w-full overflow-hidden rounded-pill bg-surface-2">
        <div className="bg-accent-2" style={{ width: `${positivePct}%` }} />
        <div className="bg-danger" style={{ width: `${100 - positivePct}%` }} />
      </div>
      <div className="flex justify-between font-body text-sm text-text-dim">
        <span className="text-accent-2">{breakdown.positive} positive</span>
        <span className="text-danger">{breakdown.negative} negative</span>
      </div>
    </div>
  );
}
