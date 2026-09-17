"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { Button, Input } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const { login, loginWithSso, error, clearError, hasOnboarded } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const afterLogin = () => {
    router.push(hasOnboarded ? "/chat" : "/onboarding");
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    clearError();
    setSubmitting(true);
    try {
      await login(email, password);
      afterLogin();
    } catch {
      // error surfaced via context
    } finally {
      setSubmitting(false);
    }
  };

  const handleSso = async () => {
    clearError();
    if (!email) {
      return;
    }
    setSubmitting(true);
    try {
      await loginWithSso(email);
      afterLogin();
    } catch {
      // error surfaced via context
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface-2 px-4">
      <div className="w-full max-w-[360px] rounded-lg border border-border bg-surface p-[30px_28px] shadow-default">
        <div className="mb-6 flex flex-col items-center gap-3 text-center">
          <div className="flex h-[38px] w-[38px] items-center justify-center rounded-sm bg-brand-gradient font-display text-xl font-bold text-accent-ink">
            Q
          </div>
          <div>
            <h1 className="font-display text-xl font-semibold text-text">Qcells L1 Assistant</h1>
            <p className="mt-1 font-body text-sm text-text-dim">Sign in to get help with L1 support queries</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            label="Work email"
            type="email"
            name="email"
            autoComplete="username"
            placeholder="you@qcells.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            label="Password"
            type="password"
            name="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && <p className="font-body text-sm text-danger">{error}</p>}

          <Button type="submit" variant="solid" fullWidth disabled={submitting}>
            {submitting ? "Signing in..." : "Continue"}
          </Button>
        </form>

        <div className="my-5 flex items-center gap-3">
          <div className="h-px flex-1 bg-border" />
          <span className="font-body text-sm text-text-dim">or</span>
          <div className="h-px flex-1 bg-border" />
        </div>

        <button
          type="button"
          onClick={handleSso}
          disabled={submitting}
          className="flex w-full items-center justify-center gap-2 rounded-md border border-border bg-surface-2 px-5 py-[10px] font-body text-md font-medium text-text transition-colors hover:border-accent disabled:opacity-50"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10zM9 12l2 2 4-4" />
          </svg>
          Continue with Company SSO
        </button>

        <p className="mt-6 text-center font-body text-sm text-text-dim">
          Trouble signing in? Contact your site administrator.
        </p>

        <div className="mt-4 rounded-md bg-surface-2 p-3 font-body text-xs text-text-dim">
          <p className="font-semibold">Demo accounts</p>
          <p>Installer: jordan.reyes@installer.qcells.com / installer123</p>
          <p>Admin: casey.kim@qcells.com / admin123</p>
        </div>
      </div>
    </main>
  );
}
