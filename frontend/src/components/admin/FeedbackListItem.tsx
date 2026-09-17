"use client";

import { useState } from "react";

import { ProcessTracePanel } from "@/components/chat/ProcessTrace";
import { Badge, Button, Textarea } from "@/components/ui";
import { api } from "@/lib/api";
import type { Conversation, FeedbackItem, Message } from "@/lib/types";
import { KnowledgeGraphView } from "./KnowledgeGraphView";

interface FeedbackListItemProps {
  item: FeedbackItem;
  token: string;
  onCorrectionSaved: (updated: FeedbackItem) => void;
}

export function FeedbackListItem({ item, token, onCorrectionSaved }: FeedbackListItemProps) {
  const isPositive = item.sentiment === "up";
  const [expanded, setExpanded] = useState(false);
  const [loadingConversation, setLoadingConversation] = useState(false);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [showCorrectionForm, setShowCorrectionForm] = useState(false);
  const [correctionText, setCorrectionText] = useState("");
  const [documentFilename, setDocumentFilename] = useState("");
  const [addAsDocument, setAddAsDocument] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const relatedMessage: Message | undefined =
    conversation?.messages.find((m) => m.id === item.message_id) ??
    [...(conversation?.messages ?? [])].reverse().find((m) => m.sender === "assistant");

  const handleToggleExpand = async () => {
    const next = !expanded;
    setExpanded(next);
    if (next && !conversation) {
      setLoadingConversation(true);
      try {
        const full = await api.getAdminConversation(token, item.conversation_id);
        setConversation(full);
      } catch {
        setConversation(null);
      } finally {
        setLoadingConversation(false);
      }
    }
  };

  const handleSubmitCorrection = async () => {
    if (!correctionText.trim()) return;
    setSubmitting(true);
    try {
      const updated = await api.submitCorrection(token, item.id, {
        text: correctionText.trim(),
        document_filename: documentFilename.trim() || undefined,
        add_as_document: addAsDocument,
      });
      onCorrectionSaved(updated);
      setShowCorrectionForm(false);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className={[
        "rounded-md border border-border bg-surface p-3.5",
        "border-l-4",
        isPositive ? "border-l-accent-2" : "border-l-danger",
      ].join(" ")}
    >
      <div className="mb-1.5 flex items-center justify-between gap-2">
        <Badge tone={isPositive ? "positive" : "negative"}>{isPositive ? "Positive" : "Negative"}</Badge>
        <span className="font-mono text-xs text-text-dim">
          {new Date(item.created_at).toLocaleString()}
        </span>
      </div>
      <p className="font-body text-md text-text">&ldquo;{item.query}&rdquo;</p>
      {item.comment && <p className="mt-1 font-body text-sm text-text-dim">{item.comment}</p>}
      <p className="mt-2 font-body text-xs text-text-dim">
        {item.user_name}
        {item.stars ? ` · ${item.stars}★` : ""}
      </p>

      {item.correction && (
        <div className="mt-3 rounded-md bg-accent-2-soft p-2.5">
          <p className="font-body text-xs font-semibold text-accent-2">Correction applied</p>
          <p className="mt-0.5 font-body text-sm text-text">{item.correction.text}</p>
          {item.correction.document_filename && (
            <p className="mt-0.5 font-mono text-xs text-text-dim">{item.correction.document_filename}</p>
          )}
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-4">
        <button
          type="button"
          onClick={handleToggleExpand}
          className="font-body text-sm font-medium text-accent underline"
        >
          {expanded ? "Hide trace & knowledge graph" : "View trace & knowledge graph"}
        </button>
        {!isPositive && !item.correction && (
          <button
            type="button"
            onClick={() => setShowCorrectionForm((v) => !v)}
            className="font-body text-sm font-medium text-accent underline"
          >
            Add correction
          </button>
        )}
      </div>

      {expanded && (
        <div className="mt-3 flex flex-col gap-3">
          {loadingConversation ? (
            <p className="font-body text-sm text-text-dim">Loading...</p>
          ) : relatedMessage ? (
            <>
              <ProcessTracePanel steps={relatedMessage.process_trace} isGrounded={relatedMessage.is_grounded} />
              {relatedMessage.knowledge_graph && <KnowledgeGraphView graph={relatedMessage.knowledge_graph} />}
            </>
          ) : (
            <p className="font-body text-sm text-text-dim">No trace available for this conversation.</p>
          )}
        </div>
      )}

      {showCorrectionForm && (
        <div className="mt-3 flex flex-col gap-2.5 rounded-md border border-border bg-surface-2 p-3">
          <Textarea
            label="Correct answer"
            placeholder="What should the assistant have said?"
            value={correctionText}
            onChange={(e) => setCorrectionText(e.target.value)}
          />
          <input
            value={documentFilename}
            onChange={(e) => setDocumentFilename(e.target.value)}
            placeholder="Optional source filename (e.g. storm-damage-addendum.md)"
            aria-label="Optional source document filename"
            className="rounded-md border border-border bg-surface px-3 py-2 font-body text-sm text-text placeholder:text-text-dim outline-none focus:border-accent"
          />
          <label className="flex items-center gap-2 font-body text-sm text-text-dim">
            <input
              type="checkbox"
              checked={addAsDocument}
              disabled={!documentFilename.trim()}
              onChange={(e) => setAddAsDocument(e.target.checked)}
            />
            Also register as a knowledge-base document
          </label>
          <Button
            variant="solid"
            disabled={!correctionText.trim() || submitting}
            onClick={handleSubmitCorrection}
          >
            {submitting ? "Saving..." : "Save correction"}
          </Button>
        </div>
      )}
    </div>
  );
}
