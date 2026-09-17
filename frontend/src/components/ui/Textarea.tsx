"use client";

import { forwardRef, type TextareaHTMLAttributes } from "react";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, id, className = "", ...rest }, ref) => {
    const areaId = id ?? rest.name;
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={areaId} className="font-body text-sm font-medium text-text-dim">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={areaId}
          className={[
            "min-h-[88px] resize-none rounded-md border border-border bg-surface px-4 py-3",
            "font-body text-md text-text placeholder:text-text-dim outline-none transition-colors",
            "focus:border-accent focus:ring-2 focus:ring-accent-soft",
            className,
          ].join(" ")}
          {...rest}
        />
      </div>
    );
  }
);

Textarea.displayName = "Textarea";
