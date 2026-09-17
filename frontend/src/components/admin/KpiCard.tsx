import { Card } from "@/components/ui";
import type { ReactNode } from "react";

export function KpiCard({ icon, value, label }: { icon: ReactNode; value: number | string; label: string }) {
  return (
    <Card className="flex items-center gap-3.5">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-sm bg-accent-soft text-accent">
        {icon}
      </div>
      <div>
        <p className="font-display text-2xl font-bold text-text">{value}</p>
        <p className="font-body text-sm text-text-dim">{label}</p>
      </div>
    </Card>
  );
}
