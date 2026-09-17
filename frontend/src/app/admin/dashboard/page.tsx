"use client";

import { useEffect, useState } from "react";

import { ActivityChart } from "@/components/admin/ActivityChart";
import { FeedbackBreakdownBar } from "@/components/admin/FeedbackBreakdownBar";
import { KpiCard } from "@/components/admin/KpiCard";
import { Card, ProgressRing } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { DashboardResponse } from "@/lib/types";

const ICONS = {
  conversations: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />
    </svg>
  ),
  messages: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
  ),
  users: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zM23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
    </svg>
  ),
  today: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 8v4l3 3M12 22a10 10 0 100-20 10 10 0 000 20z" />
    </svg>
  ),
};

export default function AdminDashboardPage() {
  const { token } = useAuth();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    api
      .getDashboard(token)
      .then(setData)
      .finally(() => setLoading(false));
  }, [token]);

  if (loading || !data) {
    return <p className="font-body text-md text-text-dim">Loading dashboard...</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard icon={ICONS.conversations} value={data.kpis.conversations} label="Conversations" />
        <KpiCard icon={ICONS.messages} value={data.kpis.total_messages} label="Total messages" />
        <KpiCard icon={ICONS.users} value={data.kpis.unique_users} label="Unique users" />
        <KpiCard icon={ICONS.today} value={data.kpis.messages_today} label="Messages today" />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card size="lg" className="flex flex-col items-center justify-center gap-4 sm:flex-row lg:col-span-1">
          <ProgressRing value={data.quality.grounding_rate} color="var(--accent-2)" label="Grounding rate" />
          <ProgressRing value={data.quality.satisfaction} color="var(--accent)" label="Satisfaction" />
        </Card>

        <Card size="lg" className="lg:col-span-1">
          <p className="mb-4 font-display text-md font-semibold text-text">Feedback breakdown</p>
          <FeedbackBreakdownBar breakdown={data.feedback_breakdown} />
        </Card>

        <Card size="lg" className="lg:col-span-1">
          <p className="mb-4 font-display text-md font-semibold text-text">Last 7 days</p>
          <ActivityChart activity={data.activity} />
        </Card>
      </div>
    </div>
  );
}
