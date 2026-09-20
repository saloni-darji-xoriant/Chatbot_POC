import type { ConversationSummary } from "./types";

export type HistorySort = "newest" | "oldest";

export const HISTORY_SORT_LABELS: Record<HistorySort, string> = {
  newest: "Newest first",
  oldest: "Oldest first",
};

const activityTime = (c: ConversationSummary) => new Date(c.updated_at ?? c.created_at).getTime();

/** Sorts by last activity (date + time). Returns a new array. */
export function sortConversations(list: ConversationSummary[], sort: HistorySort): ConversationSummary[] {
  const direction = sort === "newest" ? -1 : 1;
  return [...list].sort((a, b) => direction * (activityTime(a) - activityTime(b)));
}

const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();

/** "Today" / "Yesterday" / a locale date — all in the viewer's own timezone. */
export function dayLabel(iso: string, now: Date = new Date()): string {
  const moment = new Date(iso);
  const diffDays = Math.round((startOfDay(now) - startOfDay(moment)) / 86_400_000);
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  return moment.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short", year: "numeric" });
}

/** Date and time in the viewer's locale and timezone. */
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  });
}

/** Groups an already-sorted list into consecutive day buckets. */
export function groupByDay(
  list: ConversationSummary[],
  now: Date = new Date()
): { label: string; items: ConversationSummary[] }[] {
  const groups: { label: string; items: ConversationSummary[] }[] = [];
  for (const item of list) {
    const label = dayLabel(item.updated_at ?? item.created_at, now);
    const last = groups[groups.length - 1];
    if (last && last.label === label) last.items.push(item);
    else groups.push({ label, items: [item] });
  }
  return groups;
}
