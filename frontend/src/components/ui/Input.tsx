"use client";

import { forwardRef, type InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, id, className = "", ...rest }, ref) => {
    const inputId = id ?? rest.name;
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="font-body text-sm font-medium text-text-dim">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={[
            "rounded-md border bg-surface px-4 py-[10px] font-body text-md text-text",
            "placeholder:text-text-dim outline-none transition-colors",
            "focus:border-accent focus:ring-2 focus:ring-accent-soft",
            error ? "border-danger" : "border-border",
            className,
          ].join(" ")}
          {...rest}
        />
        {error && <span className="font-body text-sm text-danger">{error}</span>}
      </div>
    );
  }
);

Input.displayName = "Input";
