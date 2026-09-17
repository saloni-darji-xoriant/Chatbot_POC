"use client";

import { useState } from "react";

interface StarRatingProps {
  value: number;
  onChange: (value: number) => void;
}

export function StarRating({ value, onChange }: StarRatingProps) {
  const [hovered, setHovered] = useState<number | null>(null);
  const active = hovered ?? value;

  return (
    <div role="radiogroup" aria-label="Star rating" className="flex gap-1.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          role="radio"
          aria-checked={value === star}
          aria-label={`${star} star${star > 1 ? "s" : ""}`}
          onMouseEnter={() => setHovered(star)}
          onMouseLeave={() => setHovered(null)}
          onClick={() => onChange(star)}
          className="p-0.5"
        >
          <svg
            width="26"
            height="26"
            viewBox="0 0 24 24"
            fill={star <= active ? "var(--accent-2)" : "none"}
            stroke={star <= active ? "var(--accent-2)" : "var(--border)"}
            strokeWidth="1.5"
          >
            <path d="M12 2.5l2.9 6.34 6.98.65-5.27 4.73 1.58 6.88L12 17.77l-6.19 3.33 1.58-6.88L2.12 9.49l6.98-.65L12 2.5z" />
          </svg>
        </button>
      ))}
    </div>
  );
}
