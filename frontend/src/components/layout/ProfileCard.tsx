import { Avatar } from "@/components/ui";
import type { User } from "@/lib/types";

export function ProfileCard({ user }: { user: User }) {
  return (
    <div className="flex items-center gap-2.5 rounded-md border border-border bg-surface-2 px-2 py-[9px]">
      <Avatar initial={user.name.charAt(0)} size={30} rounded="full" />
      <div className="min-w-0 flex-1">
        <p className="truncate font-body text-sm font-semibold text-text">{user.name}</p>
        <p className="truncate font-body text-xs text-text-dim">{user.region ?? user.role}</p>
      </div>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0 text-text-dim">
        <path d="M9 18l6-6-6-6" />
      </svg>
    </div>
  );
}
