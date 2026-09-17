import { Card } from "@/components/ui";
import type { HandoffContact } from "@/lib/types";

const ICONS: Record<string, string> = {
  phone: "M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.362 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.338 1.85.573 2.81.7A2 2 0 0122 16.92z",
  "alert-triangle": "M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM12 9v4M12 17h.01",
  mail: "M4 4h16a2 2 0 012 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6a2 2 0 012-2zM22 6l-10 7L2 6",
  "shield-check": "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10zM9 12l2 2 4-4",
};

export function ContactCards({ contacts }: { contacts: HandoffContact[] }) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {contacts.map((contact) => (
        <Card key={contact.label} className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-sm bg-accent-soft text-accent">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d={ICONS[contact.icon] ?? ICONS.mail} />
            </svg>
          </div>
          <div>
            <p className="font-body text-md font-semibold text-text">{contact.label}</p>
            <p className="font-mono text-sm text-text-dim">{contact.value}</p>
          </div>
        </Card>
      ))}
    </div>
  );
}
