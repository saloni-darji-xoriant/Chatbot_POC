"use client";

import { useState } from "react";

import { Avatar } from "@/components/ui";
import type { Message, VoteValue } from "@/lib/types";
// import { AttachmentChip } from "./AttachmentChip"; // unused while the attachment chip UI below is commented out
import { CitationChip } from "./CitationChip";
import { MessageActions } from "./MessageActions";
import { ProcessTracePanel } from "./ProcessTrace";
import { QuickReplyChip } from "./QuickReplyChip";

interface MessageBubbleProps {
  message: Message;
  onVote?: (vote: VoteValue | null, reason?: string) => void;
  onQuickReply?: (text: string) => void;
}

export function MessageBubble({ message, onVote, onQuickReply }: MessageBubbleProps) {
  const [showTrace, setShowTrace] = useState(false);

  if (message.sender === "user") {
    return (
      <div className="flex flex-col items-end gap-1.5">
        {/* Attachment chips on the sent message — temporarily disabled along
           with the composer's attach control. Uncomment to bring back.
        {message.attachments.length > 0 && (
          <div className="flex flex-wrap justify-end gap-1.5">
            {message.attachments.map((a) => (
              <AttachmentChip key={a.id} attachment={a} />
            ))}
          </div>
        )}
        */}
        <div className="max-w-[420px] rounded-md bg-surface-2 px-3.5 py-2.5 font-body text-md text-text">
          {message.text}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <Avatar initial="Q" size={26} />
      <div className="flex max-w-[calc(100%-38px)] flex-col gap-2.5">
        <p className="whitespace-pre-wrap font-body text-md leading-relaxed text-text">{message.text}</p>

        {message.citations.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.citations.map((c) => (
              <CitationChip key={c.id} citation={c} />
            ))}
          </div>
        )}

        {message.quick_replies.length > 0 && onQuickReply && (
          <div className="flex flex-wrap gap-2">
            {message.quick_replies.map((qr) => (
              <QuickReplyChip key={qr} label={qr} onClick={() => onQuickReply(qr)} />
            ))}
          </div>
        )}

        {onVote && (
          <MessageActions
            vote={message.vote}
            voteReason={message.vote_reason}
            onVote={onVote}
            hasTrace={message.process_trace.length > 0}
            traceActive={showTrace}
            onToggleTrace={() => setShowTrace((v) => !v)}
          />
        )}

        {showTrace && <ProcessTracePanel steps={message.process_trace} isGrounded={message.is_grounded} />}
      </div>
    </div>
  );
}
