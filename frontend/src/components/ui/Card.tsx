import type { HTMLAttributes } from "react";

type CardSize = "sm" | "lg";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  size?: CardSize;
  elevated?: boolean;
}

export function Card({ size = "sm", elevated = false, className = "", children, ...rest }: CardProps) {
  return (
    <div
      className={[
        "rounded-md border border-border bg-surface",
        size === "lg" ? "rounded-lg p-5" : "p-3.5",
        elevated ? "shadow-default" : "",
        className,
      ].join(" ")}
      {...rest}
    >
      {children}
    </div>
  );
}
