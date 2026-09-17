"use client";

import { useState } from "react";

import { Button, Card, StarRating, Textarea } from "@/components/ui";
import type { VoteValue } from "@/lib/types";

interface EndOfConversationRatingProps {
  onSubmit: (stars: number, thumbs: VoteValue | null, comment: string) => Promise<void>;
  onDismiss: () => void;
}

export function EndOfConversationRating({ onSubmit, onDismiss }: EndOfConversationRatingProps) {
  const [stars, setStars] = useState(0);
  const [thumbs, setThumbs] = useState<VoteValue | null>(null);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (stars === 0) return;
    setSubmitting(true);
    try {
      await onSubmit(stars, thumbs, comment);
      setSubmitted(true);
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <Card size="lg" className="mx-auto w-full max-w-[420px] text-center">
        <p className="font-display text-lg font-semibold text-text">Thanks for the feedback!</p>
        <p className="mt-1 font-body text-md text-text-dim">It helps us improve the assistant for every installer.</p>
        <Button variant="ghost" className="mt-4" onClick={onDismiss}>
          Start a new question
        </Button>
      </Card>
    );
  }

  return (
    <Card size="lg" className="mx-auto w-full max-w-[420px]">
      <p className="font-display text-lg font-semibold text-text">How did we do?</p>
      <p className="mt-1 font-body text-sm text-text-dim">Rate this conversation before you go.</p>

      <div className="mt-4">
        <StarRating value={stars} onChange={setStars} />
      </div>

      <div className="mt-4 flex gap-2">
        <button
          type="button"
          onClick={() => setThumbs(thumbs === "up" ? null : "up")}
          className={[
            "rounded-pill border px-4 py-2 font-body text-sm font-medium transition-colors",
            thumbs === "up"
              ? "border-accent-2 bg-accent-2-soft text-accent-2"
              : "border-border text-text-dim hover:border-accent-2",
          ].join(" ")}
        >
          Thumbs up
        </button>
        <button
          type="button"
          onClick={() => setThumbs(thumbs === "down" ? null : "down")}
          className={[
            "rounded-pill border px-4 py-2 font-body text-sm font-medium transition-colors",
            thumbs === "down"
              ? "border-danger bg-danger-soft text-danger"
              : "border-border text-text-dim hover:border-danger",
          ].join(" ")}
        >
          Thumbs down
        </button>
      </div>

      <div className="mt-4">
        <Textarea
          placeholder="Anything we should improve?"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
      </div>

      <Button
        variant="gradient"
        fullWidth
        className="mt-5"
        disabled={stars === 0 || submitting}
        onClick={handleSubmit}
      >
        {submitting ? "Submitting..." : "Submit feedback"}
      </Button>
    </Card>
  );
}
