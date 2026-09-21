"use client";

import { useRef, useState, type ChangeEvent, type FormEvent, type KeyboardEvent } from "react";

import type { AttachmentSummary } from "@/lib/types";
import { AttachmentChip } from "./AttachmentChip";

interface ComposerProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
  attachments: AttachmentSummary[];
  isUploadingAttachment: boolean;
  attachmentError: string | null;
  onAttach: (file: File) => void;
  onRemoveAttachment: (id: string) => void;
}

export function Composer({
  onSend,
  disabled,
  placeholder = "Ask a question...",
  attachments,
  isUploadingAttachment,
  attachmentError,
  onAttach,
  onRemoveAttachment,
}: ComposerProps) {
  const [value, setValue] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      submit();
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      Array.from(files).forEach((file) => onAttach(file));
    }
    e.target.value = "";
  };

  return (
    <div className="flex flex-col gap-2">
      {(attachments.length > 0 || isUploadingAttachment || attachmentError) && (
        <div className="flex flex-wrap items-center gap-2">
          {attachments.map((a) => (
            <AttachmentChip key={a.id} attachment={a} onRemove={() => onRemoveAttachment(a.id)} />
          ))}
          {isUploadingAttachment && (
            <span className="flex items-center gap-1.5 rounded-md border border-border bg-surface-2 px-2.5 py-1.5 font-body text-sm text-text-dim">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-accent-soft border-t-accent" />
              Attaching...
            </span>
          )}
          {attachmentError && (
            <span className="font-body text-sm text-danger">{attachmentError}</span>
          )}
        </div>
      )}

      <form
        onSubmit={submit}
        className="flex items-center gap-2 rounded-pill border border-border bg-surface py-1.5 pl-[18px] pr-1.5 shadow-composerFloat"
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".txt,.md,.csv,.json,.log,.pdf,.docx,.png,.jpg,.jpeg,.gif,.webp,.bmp"
          onChange={handleFileChange}
          className="hidden"
        />
        <button
          type="button"
          aria-label="Attach a file"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-text-dim hover:bg-surface-2 disabled:opacity-40"
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
          </svg>
        </button>
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          aria-label="Message"
          className="flex-1 bg-transparent font-body text-md text-text placeholder:text-text-dim outline-none disabled:opacity-60"
        />
        <button
          type="submit"
          aria-label="Send message"
          disabled={disabled || !value.trim()}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-gradient text-accent-ink transition-opacity disabled:opacity-40"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
          </svg>
        </button>
      </form>
    </div>
  );
}
