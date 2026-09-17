"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { Button, Card } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";

const INSTALLER_CAPABILITIES = [
  { title: "Ask L1 support questions", desc: "Inverter faults, panel output, warranty, firmware, and more — answered from the official Qcells knowledge base." },
  { title: "See exactly where answers come from", desc: "Every grounded answer includes citation chips linking back to the source document." },
  { title: "Get escalated when needed", desc: "If the assistant can't find a grounded answer, you're automatically handed off to a live L2 specialist." },
];

const ADMIN_CAPABILITIES = [
  { title: "Everything installers get", desc: "Full access to the L1 assistant for your own queries." },
  { title: "Monitor quality in real time", desc: "Track grounding rate, satisfaction, and conversation volume from the Admin dashboard." },
  { title: "Manage feedback & documents", desc: "Review installer feedback and keep the knowledge base sources up to date." },
];

export default function OnboardingPage() {
  const { user, isLoading, completeOnboarding } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  if (!user) return null;

  const capabilities = user.role === "admin" ? ADMIN_CAPABILITIES : INSTALLER_CAPABILITIES;

  const handleGetStarted = () => {
    completeOnboarding();
    router.push("/chat");
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface-2 px-4 py-10">
      <div className="w-full max-w-[560px]">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-md bg-brand-gradient font-display text-2xl font-bold text-accent-ink">
            Q
          </div>
          <h1 className="font-display text-3xl font-semibold text-text">
            Welcome, <span className="brand-gradient-text">{user.name.split(" ")[0]}</span>
          </h1>
          <p className="mt-2 font-body text-md text-text-dim">
            Here&apos;s what the Qcells L1 Assistant can do for you as {user.role === "admin" ? "an admin" : "an installer"}.
          </p>
        </div>

        <div className="flex flex-col gap-3">
          {capabilities.map((cap) => (
            <Card key={cap.title} size="lg" className="flex items-start gap-3">
              <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent-2-soft text-accent-2">
                ✓
              </div>
              <div>
                <p className="font-body text-md font-semibold text-text">{cap.title}</p>
                <p className="mt-0.5 font-body text-sm text-text-dim">{cap.desc}</p>
              </div>
            </Card>
          ))}
        </div>

        <Button variant="gradient" fullWidth className="mt-8" onClick={handleGetStarted}>
          Get started
        </Button>
      </div>
    </main>
  );
}
