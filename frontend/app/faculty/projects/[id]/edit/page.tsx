"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { RoleGate } from "@/components/guards";
import { useAuth } from "@/components/auth-provider";
import { api, ApiError } from "@/lib/api";
import type { Project } from "@/types/api";
import { ErrorNotice, PageLoading } from "@/components/ui";
import { ProjectForm } from "@/components/project-form";
export default function EditProjectPage(){return <RoleGate roles={["FACULTY"]}><Editor/></RoleGate>}
function Editor(){const {id}=useParams<{id:string}>();const {user,token}=useAuth();const router=useRouter();const [project,setProject]=useState<Project|null>(null);const [error,setError]=useState("");const [loading,setLoading]=useState(true);useEffect(()=>{if(!token)return;api.project(id,token).then(p=>{if(p.faculty_id!==user?.id)throw new ApiError("You can only edit your own projects.",403);setProject(p);}).catch(e=>setError(e instanceof ApiError?e.message:"Could not load this project.")).finally(()=>setLoading(false));},[id,token,user]);if(loading)return <PageLoading label="Loading project editor…"/>;return <div className="container max-w-3xl py-10"><Link href={`/faculty/projects/${id}`} className="inline-flex items-center gap-1 text-xs font-bold text-muted"><ArrowLeft size={14}/> Project details</Link><div className="mt-5"><div className="eyebrow">Project management</div><h1 className="mt-2 text-3xl font-bold">Edit research project</h1></div>{project?<div className="mt-6"><ProjectForm project={project} onSaved={()=>router.replace(`/faculty/projects/${id}`)}/></div>:<div className="mt-5"><ErrorNotice message={error||"Project unavailable."}/></div>}</div>;}
