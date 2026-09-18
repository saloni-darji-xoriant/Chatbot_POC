"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { AdminTopbar } from "@/components/layout/AdminTopbar";
import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/context/AuthContext";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    if (!user) {
      router.replace("/login");
    } else if (user.role !== "admin") {
      router.replace("/chat");
    }
  }, [isLoading, user, router]);

  if (!user || user.role !== "admin") return null;

  return (
    <AppShell>
      <AdminTopbar />
      <div className="flex-1 overflow-y-auto p-4 sm:p-6">{children}</div>
    </AppShell>
  );
}
