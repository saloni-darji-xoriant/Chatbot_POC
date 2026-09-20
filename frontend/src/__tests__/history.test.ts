import { dayLabel, groupByDay, sortConversations } from "@/lib/history";
import type { ConversationSummary } from "@/lib/types";

const conv = (id: string, updated_at: string): ConversationSummary => ({
  id,
  title: id,
  status: "active",
  created_at: updated_at,
  updated_at,
});

describe("history helpers", () => {
  const list = [
    conv("old", "2026-01-01T08:00:00+00:00"),
    conv("new", "2026-03-01T09:30:00+00:00"),
    conv("same-day-later", "2026-03-01T18:45:00+00:00"),
  ];

  it("sorts newest first by date AND time", () => {
    expect(sortConversations(list, "newest").map((c) => c.id)).toEqual(["same-day-later", "new", "old"]);
  });

  it("sorts oldest first and does not mutate the input", () => {
    const copy = [...list];
    expect(sortConversations(list, "oldest").map((c) => c.id)).toEqual(["old", "new", "same-day-later"]);
    expect(list).toEqual(copy);
  });

  it("labels Today and Yesterday relative to the viewer's local day", () => {
    const now = new Date(2026, 5, 15, 14, 0);
    expect(dayLabel(new Date(2026, 5, 15, 1, 0).toISOString(), now)).toBe("Today");
    expect(dayLabel(new Date(2026, 5, 14, 23, 0).toISOString(), now)).toBe("Yesterday");
    expect(dayLabel(new Date(2026, 5, 1, 12, 0).toISOString(), now)).not.toMatch(/Today|Yesterday/);
  });

  it("groups consecutive conversations by day", () => {
    const now = new Date(2026, 5, 15, 14, 0);
    const items = [
      conv("a", new Date(2026, 5, 15, 12, 0).toISOString()),
      conv("b", new Date(2026, 5, 15, 9, 0).toISOString()),
      conv("c", new Date(2026, 5, 14, 9, 0).toISOString()),
    ];
    const groups = groupByDay(items, now);
    expect(groups.map((g) => [g.label, g.items.length])).toEqual([
      ["Today", 2],
      ["Yesterday", 1],
    ]);
  });
});
