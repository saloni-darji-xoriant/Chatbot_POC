interface AvatarProps {
  initial: string;
  size?: number;
  rounded?: "sm" | "full";
}

export function Avatar({ initial, size = 26, rounded = "sm" }: AvatarProps) {
  return (
    <div
      className={[
        "flex shrink-0 items-center justify-center bg-brand-gradient font-display font-semibold text-accent-ink",
        rounded === "full" ? "rounded-full" : "rounded-sm",
      ].join(" ")}
      style={{ width: size, height: size, fontSize: Math.max(10, size * 0.42) }}
    >
      {initial.toUpperCase()}
    </div>
  );
}
