"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import type { Role } from "@/types/api";
import { useAuth } from "@/components/auth-provider";
import { PageLoading } from "@/components/ui";
export function RoleGate({ roles, children }: { roles?: Role[]; children: React.ReactNode }) { const { user, ready }=useAuth(); const router=useRouter(); useEffect(()=>{if(ready&&!user)router.replace(`/login?next=${encodeURIComponent(location.pathname)}`);else if(ready&&user&&roles&&!roles.includes(user.role))router.replace("/unauthorized");},[ready,user,roles,router]); if(!ready||!user|| (roles&&!roles.includes(user.role)))return <PageLoading label="Checking your access…"/>; return <>{children}</>; }
