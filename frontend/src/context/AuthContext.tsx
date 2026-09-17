"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { api, ApiError } from "@/lib/api";
import { ONBOARDING_STORAGE_KEY, TOKEN_STORAGE_KEY, USER_STORAGE_KEY } from "@/lib/constants";
import type { User } from "@/lib/types";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  hasOnboarded: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<User>;
  loginWithSso: (email: string) => Promise<User>;
  logout: () => void;
  completeOnboarding: () => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasOnboarded, setHasOnboarded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY);
      const storedUser = localStorage.getItem(USER_STORAGE_KEY);
      const onboarded = localStorage.getItem(ONBOARDING_STORAGE_KEY);
      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      }
      setHasOnboarded(onboarded === "true");
    } catch {
      // localStorage unavailable (SSR / privacy mode) — proceed logged out
    } finally {
      setIsLoading(false);
    }
  }, []);

  const persistSession = useCallback((nextToken: string, nextUser: User) => {
    setToken(nextToken);
    setUser(nextUser);
    try {
      localStorage.setItem(TOKEN_STORAGE_KEY, nextToken);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(nextUser));
    } catch {
      // ignore storage failures
    }
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      setError(null);
      try {
        const { token: newToken, user: newUser } = await api.login(email, password);
        persistSession(newToken, newUser);
        return newUser;
      } catch (err) {
        const message = err instanceof ApiError ? err.message : "Unable to sign in";
        setError(message);
        throw err;
      }
    },
    [persistSession]
  );

  const loginWithSso = useCallback(
    async (email: string) => {
      setError(null);
      try {
        const { token: newToken, user: newUser } = await api.ssoLogin(email);
        persistSession(newToken, newUser);
        return newUser;
      } catch (err) {
        const message = err instanceof ApiError ? err.message : "SSO sign-in failed";
        setError(message);
        throw err;
      }
    },
    [persistSession]
  );

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    try {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      localStorage.removeItem(USER_STORAGE_KEY);
    } catch {
      // ignore
    }
  }, []);

  const completeOnboarding = useCallback(() => {
    setHasOnboarded(true);
    try {
      localStorage.setItem(ONBOARDING_STORAGE_KEY, "true");
    } catch {
      // ignore
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const value = useMemo(
    () => ({
      user,
      token,
      isLoading,
      hasOnboarded,
      error,
      login,
      loginWithSso,
      logout,
      completeOnboarding,
      clearError,
    }),
    [user, token, isLoading, hasOnboarded, error, login, loginWithSso, logout, completeOnboarding, clearError]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
