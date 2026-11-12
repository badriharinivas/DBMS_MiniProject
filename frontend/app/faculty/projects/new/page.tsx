"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Info } from "lucide-react";
import { RoleGate } from "@/components/guards";
import { ProjectForm } from "@/components/project-form";
import type { Project } from "@/types/api";
export default function NewProjectPage(){return <RoleGate roles={["FACULTY"]}><Create/></RoleGate>}
function Create(){const router=useRouter();return <div className="container max-w-3xl py-10"><Link href="/faculty/projects" className="inline-flex items-center gap-1 text-xs font-bold text-muted"><ArrowLeft size={14}/> My projects</Link><div className="mt-5"><div className="eyebrow">Share your research</div><h1 className="mt-2 text-3xl font-bold">Create a project</h1><p className="mt-2 text-sm leading-6 text-muted">Describe the work clearly so students can understand the opportunity and decide if it fits.</p></div><div className="my-5 flex gap-3 rounded-xl border border-[#dce9df] bg-[#eef5ef] p-4 text-sm leading-6 text-[#46604e]"><Info className="mt-0.5 shrink-0" size={17}/><p>Publishing creates an open project. The API generates its semantic embedding and maintains its keyword-search index.</p></div><ProjectForm onSaved={(p:Project)=>router.replace(`/faculty/projects/${p.id}`)}/></div>;}
