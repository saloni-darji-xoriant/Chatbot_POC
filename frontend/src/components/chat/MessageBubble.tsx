"use client";

import { Avatar } from "@/components/ui";
import { assetUrl } from "@/lib/api";
import type { Message, VoteValue } from "@/lib/types";
// import { AttachmentChip } from "./AttachmentChip"; // unused while the attachment chip UI below is commented out
import { CitationChip } from "./CitationChip";
import { MessageActions } from "./MessageActions";
// import { ProcessTracePanel } from "./ProcessTrace"; // unused while the Trace option is commented out
import { QuickReplyChip } from "./QuickReplyChip";

interface MessageBubbleProps {
  message: Message;
  onVote?: (vote: VoteValue | null, reason?: string) => void;
  onQuickReply?: (text: string) => void;
  /** Follow-up suggestions are only useful on the latest assistant message. */
  showFollowUps?: boolean;
}

export function MessageBubble({ message, onVote, onQuickReply, showFollowUps = true }: MessageBubbleProps) {
  // Trace option is commented out for now (kept for future use):
  // const [showTrace, setShowTrace] = useState(false);

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

        {message.images && message.images.length > 0 && (
          <div className="flex flex-col gap-3">
            {message.images.map((img) => (
              <figure key={img.url} className="m-0 max-w-[560px] overflow-hidden rounded-md border border-border bg-surface">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={assetUrl(img.url)} alt={img.alt} loading="lazy" className="block h-auto w-full" />
                {img.caption && (
                  <figcaption className="border-t border-border px-3 py-1.5 font-body text-xs text-text-dim">
                    {img.caption}
                  </figcaption>
                )}
              </figure>
            ))}
          </div>
        )}

        {message.citations.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.citations.map((c) => (
              <CitationChip key={c.id} citation={c} />
            ))}
          </div>
        )}

        {showFollowUps && message.quick_replies.length > 0 && onQuickReply && (
          <div className="flex flex-col gap-2" role="group" aria-label="Suggested follow-ups">
            <p className="font-body text-xs font-medium uppercase tracking-wide text-text-dim">Suggested follow-ups</p>
            <div className="flex flex-wrap gap-2">
              {message.quick_replies.map((qr) => (
                <QuickReplyChip key={qr} label={qr} onClick={() => onQuickReply(qr)} />
              ))}
            </div>
          </div>
        )}

        {onVote && (
          <MessageActions
            vote={message.vote}
            voteReason={message.vote_reason}
            onVote={onVote}
            // Trace option commented out for now (kept for future use):
            // hasTrace={message.process_trace.length > 0}
            // traceActive={showTrace}
            // onToggleTrace={() => setShowTrace((v) => !v)}
          />
        )}

        {/* {showTrace && <ProcessTracePanel steps={message.process_trace} isGrounded={message.is_grounded} />} */}
      </div>
    </div>
  );
}
