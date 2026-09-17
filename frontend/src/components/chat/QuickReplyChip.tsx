import { Chip } from "@/components/ui";

export function QuickReplyChip({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <Chip variant="quickReply" onClick={onClick}>
      {label}
    </Chip>
  );
}
