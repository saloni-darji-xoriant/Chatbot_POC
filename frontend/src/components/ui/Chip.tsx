import type { ButtonHTMLAttributes } from "react";

type ChipVariant = "default" | "quickReply" | "mono";

interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ChipVariant;
}

const variantClasses: Record<ChipVariant, string> = {
  default: "border border-border bg-surface text-text hover:border-accent",
  quickReply: "border border-accent bg-accent-soft text-accent font-medium",
  mono: "border border-border bg-surface-2 font-mono text-xs text-text-dim",
};

export function Chip({ variant = "default", className = "", children, ...rest }: ChipProps) {
  return (
    <button
      type="button"
      className={[
        "rounded-pill px-3.5 py-2 text-base transition-colors",
        variantClasses[variant],
        rest.onClick ? "cursor-pointer" : "cursor-default",
        className,
      ].join(" ")}
      {...rest}
    >
      {children}
    </button>
  );
}
