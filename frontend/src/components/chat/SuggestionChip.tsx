import { Chip } from "@/components/ui";

export function SuggestionChip({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <Chip variant="default" onClick={onClick}>
      {label}
    </Chip>
  );
}
