import type { ActivityPoint } from "@/lib/types";

export function ActivityChart({ activity }: { activity: ActivityPoint[] }) {
  const max = Math.max(...activity.map((p) => p.value), 1);

  return (
    <div className="flex h-40 items-end gap-3">
      {activity.map((point) => (
        <div key={point.day} className="flex flex-1 flex-col items-center gap-2">
          <span className="font-body text-xs font-semibold text-text-dim">{point.value}</span>
          <div
            className="w-full rounded-t-sm bg-brand-gradient"
            style={{ height: `${Math.max(6, (point.value / max) * 100)}px` }}
          />
          <span className="font-body text-xs text-text-dim">{point.day}</span>
        </div>
      ))}
    </div>
  );
}
