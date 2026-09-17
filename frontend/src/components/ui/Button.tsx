"use client";

import { forwardRef, type ButtonHTMLAttributes } from "react";

export type ButtonVariant = "gradient" | "solid" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  fullWidth?: boolean;
}

const variantClasses: Record<ButtonVariant, string> = {
  gradient: "bg-brand-gradient text-accent-ink hover:opacity-90",
  solid: "bg-accent text-accent-ink hover:opacity-90",
  ghost: "bg-surface-2 text-text border border-border hover:border-accent",
  danger: "bg-danger-soft text-danger hover:opacity-80",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "solid", fullWidth, className = "", children, ...rest }, ref) => {
    return (
      <button
        ref={ref}
        className={[
          "inline-flex items-center justify-center gap-2 rounded-pill px-5 py-[10px]",
          "font-body text-md font-semibold transition-all duration-150",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          variantClasses[variant],
          fullWidth ? "w-full" : "",
          className,
        ].join(" ")}
        {...rest}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
