import { Avatar } from "@/components/ui";
import type { HandoffInfo } from "@/lib/types";
import { ContactCards } from "./ContactCards";

interface HandoffScreenProps {
  handoff: HandoffInfo;
  onBackToChat: () => void;
}

export function HandoffScreen({ handoff, onBackToChat }: HandoffScreenProps) {
  return (
    <div className="mx-auto flex w-full max-w-chat flex-col gap-5 py-8">
      <div className="flex items-center gap-3">
        <Avatar initial="Q" size={30} />
        <div>
          <p className="font-display text-lg font-semibold text-text">Connecting you to a specialist</p>
          <p className="font-body text-sm text-text-dim">This conversation has been escalated from L1 to L2 support.</p>
        </div>
      </div>

      <div className="rounded-md bg-accent-2-soft px-[15px] py-[11px] font-body text-md text-accent-2">
        {handoff.message}
        {typeof handoff.queue_position === "number" && (
          <span className="ml-1 font-semibold">(Queue position: {handoff.queue_position})</span>
        )}
      </div>

      <div>
        <p className="mb-3 font-body text-sm font-semibold text-text-dim">
          While you wait, here are other ways to reach us:
        </p>
        <ContactCards contacts={handoff.contacts} />
      </div>

      <button
        type="button"
        onClick={onBackToChat}
        className="self-start font-body text-sm font-semibold text-accent underline"
      >
        Back to conversation
      </button>
    </div>
  );
}
