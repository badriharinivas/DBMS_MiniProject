"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowRight, BookOpenCheck, Compass, GraduationCap, LayoutDashboard, LogOut, Menu, Search, Sparkles, UserRound, X } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/components/auth-provider";
const studentLinks = [{ href: "/dashboard", label: "Overview", icon: LayoutDashboard }, { href: "/projects", label: "Discover projects", icon: Search }, { href: "/recommendations", label: "For you", icon: Sparkles }, { href: "/applications", label: "My applications", icon: BookOpenCheck }, { href: "/interests", label: "Research profile", icon: Compass }];
const facultyLinks = [{ href: "/dashboard", label: "Overview", icon: LayoutDashboard }, { href: "/faculty/projects", label: "My projects", icon: BookOpenCheck }, { href: "/faculty/projects/new", label: "Create project", icon: Sparkles }, { href: "/profile", label: "My profile", icon: UserRound }];
export function AppShell({ children }: { children: React.ReactNode }) {
 const { user, ready, logout } = useAuth(); const path = usePathname(); const [open, setOpen] = useState(false); const authPage = ["/login", "/register"].includes(path);
 const links = user?.role === "FACULTY" ? facultyLinks : studentLinks;
 if (authPage) return <>{children}</>;
 return <>
  <header className="sticky top-0 z-30 border-b border-line bg-white/95 backdrop-blur"><div className="container flex h-[70px] items-center justify-between">
   <Link href="/" className="flex items-center gap-2.5 font-bold tracking-tight"><span className="grid h-9 w-9 place-items-center rounded-xl bg-forest text-white"><GraduationCap size={21}/></span><span className="text-[17px]">Mentor<span className="text-forest">Match</span></span></Link>
   <nav className="hidden items-center gap-7 md:flex">{user && links.slice(0, 3).map(({ href, label }) => <Link key={href} href={href} className={`text-sm font-semibold ${path === href ? "text-forest" : "text-muted hover:text-ink"}`}>{label}</Link>)}</nav>
   <div className="hidden items-center gap-3 md:flex">{user ? <><Link href="/profile" className="flex items-center gap-2 rounded-full border border-line py-1.5 pl-1.5 pr-3 text-sm font-semibold"><span className="grid h-7 w-7 place-items-center rounded-full bg-mint text-forest">{user.name.slice(0,1).toUpperCase()}</span>{user.name.split(" ")[0]}</Link><button aria-label="Log out" onClick={logout} className="rounded-lg p-2 text-muted hover:bg-paper"><LogOut size={17}/></button></> : ready ? <><Link className="text-sm font-bold text-muted" href="/login">Log in</Link><Link className="btn btn-primary" href="/register">Create account <ArrowRight size={15}/></Link></> : <span className="spinner"/>}</div>
   <button className="rounded-lg p-2 md:hidden" aria-label={open ? "Close menu" : "Open menu"} onClick={() => setOpen(!open)}>{open ? <X/> : <Menu/>}</button>
  </div>{open && <div className="border-t border-line bg-white p-4 md:hidden">{user ? <div className="grid gap-2">{links.map(({ href,label,icon:Icon }) => <Link key={href} onClick={() => setOpen(false)} href={href} className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold hover:bg-paper"><Icon size={17}/>{label}</Link>)}<button onClick={logout} className="flex items-center gap-3 px-3 py-2.5 text-left text-sm font-semibold text-muted"><LogOut size={17}/> Log out</button></div> : <div className="flex gap-4"><Link href="/login">Log in</Link><Link href="/register">Create account</Link></div>}</div>}</header>
  <main>{children}</main><footer className="mt-20 border-t border-line bg-white"><div className="container flex flex-col justify-between gap-4 py-7 text-xs text-muted sm:flex-row"><span>© 2026 MentorMatch · Connecting curiosity with research</span><span>Built for student–faculty collaboration</span></div></footer>
 </>;
}
