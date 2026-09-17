"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { AdminTopbar } from "@/components/layout/AdminTopbar";
import { Sidebar } from "@/components/layout/Sidebar";
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
    <div className="flex min-h-screen bg-bg">
      <Sidebar />
      <main className="flex flex-1 flex-col">
        <AdminTopbar />
        <div className="flex-1 overflow-y-auto p-6">{children}</div>
      </main>
    </div>
  );
}
