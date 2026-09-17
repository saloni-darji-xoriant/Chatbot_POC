import type { ReactNode } from "react";

type BadgeTone = "positive" | "negative" | "neutral" | "accent";

const toneClasses: Record<BadgeTone, string> = {
  positive: "bg-accent-2-soft text-accent-2",
  negative: "bg-danger-soft text-danger",
  neutral: "bg-surface-2 text-text-dim",
  accent: "bg-accent-soft text-accent",
};

export function Badge({ tone = "neutral", children }: { tone?: BadgeTone; children: ReactNode }) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-pill px-2.5 py-1 font-body text-xs font-semibold",
        toneClasses[tone],
      ].join(" ")}
    >
      {children}
    </span>
  );
}
