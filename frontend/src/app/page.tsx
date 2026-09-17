"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/context/AuthContext";

export default function RootPage() {
  const { user, isLoading, hasOnboarded } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    if (!user) {
      router.replace("/login");
    } else if (!hasOnboarded) {
      router.replace("/onboarding");
    } else {
      router.replace("/chat");
    }
  }, [isLoading, user, hasOnboarded, router]);

  return null;
}
