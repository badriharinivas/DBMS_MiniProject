"use client";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getToken, setUnauthorizedHandler } from "@/lib/api";
import type { User } from "@/types/api";
type AuthState = { user: User | null; token: string | null; ready: boolean; login: (token: string, user: User) => void; logout: () => void; refresh: () => Promise<void> };
const AuthContext = createContext<AuthState | null>(null);
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null); const [token, setToken] = useState<string | null>(null); const [ready, setReady] = useState(false); const router = useRouter();
  const logout = useCallback(() => { if (typeof window !== "undefined") sessionStorage.removeItem("mm_token"); setToken(null); setUser(null); setReady(true); router.replace("/login"); }, [router]);
  const refresh = useCallback(async () => { const current = getToken(); if (!current) { setReady(true); return; } setToken(current); try { setUser(await api.me(current)); } catch { sessionStorage.removeItem("mm_token"); setUser(null); setToken(null); } finally { setReady(true); } }, []);
  const login = useCallback((value: string, profile: User) => { sessionStorage.setItem("mm_token", value); setToken(value); setUser(profile); setReady(true); }, []);
  useEffect(() => { setUnauthorizedHandler(logout); void refresh(); }, [logout, refresh]);
  const value = useMemo(() => ({ user, token, ready, login, logout, refresh }), [user, token, ready, login, logout, refresh]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error("useAuth must be used within AuthProvider"); return value; }
