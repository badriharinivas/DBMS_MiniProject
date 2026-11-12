import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/auth-provider";
import { AppShell } from "@/components/app-shell";
export const metadata: Metadata = { title: "MentorMatch — Research starts with a match", description: "Discover faculty research projects that fit your interests." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body><AuthProvider><AppShell>{children}</AppShell></AuthProvider></body></html>; }
