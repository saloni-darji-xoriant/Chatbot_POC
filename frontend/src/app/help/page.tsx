"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ContactCards } from "@/components/chat/ContactCards";
import { SuggestionChip } from "@/components/chat/SuggestionChip";
import { AppShell } from "@/components/layout/AppShell";
import { Avatar } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { SUGGESTED_QUESTIONS } from "@/lib/constants";
import type { HandoffContact } from "@/lib/types";

export default function HelpPage() {
  const { user, token, isLoading } = useAuth();
  const router = useRouter();
  const [contacts, setContacts] = useState<HandoffContact[]>([]);

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!token) return;
    api.helpContacts(token).then(setContacts).catch(() => setContacts([]));
  }, [token]);

  if (!user) return null;

  return (
    <AppShell>
      <div className="flex flex-1 flex-col overflow-y-auto px-4 py-6 sm:px-6 sm:py-8">
        <div className="mx-auto flex w-full max-w-chat flex-col gap-6">
          <div className="flex items-center gap-3">
            <Avatar initial="Q" size={30} />
            <div>
              <h1 className="font-display text-2xl font-semibold text-text">Help Center</h1>
              <p className="font-body text-sm text-text-dim">
                Ask the assistant, or reach a human directly using the options below.
              </p>
            </div>
          </div>

          <div>
            <p className="mb-3 font-body text-sm font-semibold text-text-dim">Popular questions</p>
            <div className="flex flex-wrap gap-2.5">
              {SUGGESTED_QUESTIONS.map((q) => (
                <SuggestionChip key={q} label={q} onClick={() => router.push("/chat")} />
              ))}
            </div>
          </div>

          <div>
            <p className="mb-3 font-body text-sm font-semibold text-text-dim">Contact support</p>
            <ContactCards contacts={contacts} />
          </div>

          <p className="font-body text-sm text-text-dim">
            Trouble signing in or something not covered here? Contact your site administrator.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
