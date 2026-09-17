interface ProgressRingProps {
  value: number; // 0-100
  color: string; // CSS color
  size?: number;
  label: string;
}

export function ProgressRing({ value, color, size = 88, label }: ProgressRingProps) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className="relative flex items-center justify-center rounded-full"
        style={{
          width: size,
          height: size,
          background: `conic-gradient(${color} ${clamped * 3.6}deg, var(--surface-2) 0deg)`,
        }}
      >
        <div
          className="flex items-center justify-center rounded-full bg-surface font-display text-lg font-semibold"
          style={{ width: size - 16, height: size - 16 }}
        >
          {clamped.toFixed(0)}%
        </div>
      </div>
      <span className="font-body text-sm text-text-dim">{label}</span>
    </div>
  );
}
