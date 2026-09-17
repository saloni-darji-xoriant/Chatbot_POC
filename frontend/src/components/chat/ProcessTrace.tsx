import { Badge } from "@/components/ui";
import type { ProcessStep } from "@/lib/types";

const STEP_ICONS: Record<ProcessStep["status"], string> = {
  pending: "○",
  active: "◐",
  done: "✓",
};

/** Per-message developer trace: shows which agent ran, what it did, and the
 * final grounded/not-grounded verdict. Toggled by the "Trace" button in
 * MessageActions so a developer can verify a specific answer. */
export function ProcessTracePanel({ steps, isGrounded }: { steps: ProcessStep[]; isGrounded: boolean }) {
  if (steps.length === 0) return null;

  return (
    <div className="max-w-[420px] rounded-md border border-border bg-surface p-3.5">
      <div className="mb-2.5 flex items-center justify-between">
        <span className="font-mono text-xs font-semibold uppercase tracking-wide text-text-dim">
          Developer trace
        </span>
        <Badge tone={isGrounded ? "positive" : "negative"}>{isGrounded ? "Grounded" : "Not grounded"}</Badge>
      </div>
      <ul className="flex flex-col gap-2">
        {steps.map((step) => (
          <li key={step.label} className="flex items-start gap-2">
            <span className={step.status === "done" ? "text-accent-2" : "text-text-dim"} aria-hidden>
              {STEP_ICONS[step.status]}
            </span>
            <div>
              {step.agent && (
                <p className="font-mono text-xs font-semibold text-accent">{step.agent}</p>
              )}
              <p className="font-body text-sm text-text-dim">{step.label}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Live, backend-driven "thinking" indicator shown while an SSE response is
 * streaming in — reflects the actual multi-agent pipeline steps as the
 * server emits them, rather than a client-side fake timer. */
export function LiveProcessTrace({ steps }: { steps: ProcessStep[] | null }) {
  const activeStep = steps?.find((s) => s.status === "active");
  const label = activeStep?.label ?? steps?.[steps.length - 1]?.label ?? "Thinking";
  const agent = activeStep?.agent ?? steps?.[steps.length - 1]?.agent;

  return (
    <div className="flex max-w-[420px] items-center gap-2.5 rounded-md border border-border bg-surface px-3.5 py-2.5">
      <span className="h-3.5 w-3.5 shrink-0 animate-spin rounded-full border-2 border-accent-soft border-t-accent" />
      <span className="font-body text-sm text-text-dim">
        {agent && <span className="font-mono text-xs font-semibold text-accent">{agent}: </span>}
        {label}...
      </span>
    </div>
  );
}
