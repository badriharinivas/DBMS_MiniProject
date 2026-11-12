"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, Check, ExternalLink, Pencil, X } from "lucide-react";
import { useParams } from "next/navigation";
import { RoleGate } from "@/components/guards";
import { useAuth } from "@/components/auth-provider";
import { api, ApiError } from "@/lib/api";
import type { Application, Project } from "@/types/api";
import { EmptyState, ErrorNotice, PageLoading, Toast } from "@/components/ui";

export default function FacultyProjectPage() {
  return <RoleGate roles={["FACULTY"]}><Manage /></RoleGate>;
}

function Manage() {
  const { id } = useParams<{ id: string }>();
  const { user, token } = useAuth();
  const [project, setProject] = useState<Project | null>(null);
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState("");

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const value = await api.project(id, token);
      if (value.faculty_id !== user?.id) throw new ApiError("You can only manage your own projects.", 403);
      setProject(value);
      setApps(await api.projectApplications(id, token));
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not load this project.");
    } finally { setLoading(false); }
  }, [id, token, user]);
  useEffect(() => { void load(); }, [load]);

  async function toggleStatus() {
    if (!project || !token) return;
    const status = project.status === "OPEN" ? "CLOSED" : "OPEN";
    if (status === "CLOSED" && !window.confirm("Close applications for this project? Existing applications remain available for review.")) return;
    setBusy("status"); setError("");
    try { setProject(await api.updateProject(id, { status }, token)); setNotice(status === "CLOSED" ? "Project closed to new applications." : "Project reopened for applications."); }
    catch (cause) { setError(cause instanceof ApiError ? cause.message : "Could not update the project."); }
    finally { setBusy(""); }
  }
  async function decide(application: Application, status: "ACCEPTED" | "REJECTED") {
    if (!token || !window.confirm(`${status === "ACCEPTED" ? "Accept" : "Reject"} this application? The decision cannot be changed.`)) return;
    setBusy(application.id); setError("");
    try { const updated = await api.updateApplication(application.id, status, token); setApps(current => current.map(item => item.id === application.id ? updated : item)); setNotice(`Application ${status.toLowerCase()}.`); }
    catch (cause) { setError(cause instanceof ApiError ? cause.message : "Could not update the application."); }
    finally { setBusy(""); }
  }
  if (loading) return <PageLoading label="Loading project and applicants…" />;
  if (!project) return <div className="container max-w-3xl py-12"><ErrorNotice message={error || "Project unavailable."} /><Link href="/faculty/projects" className="mt-5 inline-flex items-center gap-2 text-sm font-bold text-forest"><ArrowLeft size={15} /> My projects</Link></div>;

  return <div className="container max-w-4xl py-10">
    <Link href="/faculty/projects" className="inline-flex items-center gap-1 text-xs font-bold text-muted"><ArrowLeft size={14} /> My projects</Link>
    {error && <div className="mt-5"><ErrorNotice message={error} retry={() => void load()} /></div>}
    <div className="card mt-5 p-6 sm:p-8">
      <div className="flex flex-wrap items-center justify-between gap-4"><span className={`status ${project.status === "OPEN" ? "status-open" : "status-closed"}`}>{project.status}</span><div className="flex gap-2"><Link href={`/faculty/projects/${id}/edit`} className="btn btn-ghost"><Pencil size={15} /> Edit</Link><button disabled={Boolean(busy)} onClick={() => void toggleStatus()} className={`btn ${project.status === "OPEN" ? "btn-danger" : "btn-ghost"}`}>{busy === "status" ? "Saving…" : project.status === "OPEN" ? "Close project" : "Reopen project"}</button></div></div>
      <h1 className="mt-4 text-2xl font-bold">{project.title}</h1><p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-muted">{project.description}</p>
      <div className="mt-5 flex flex-wrap gap-2">{project.required_skills.map(skill => <span key={skill} className="rounded-full bg-paper px-3 py-1.5 text-xs font-semibold">{skill}</span>)}</div>
      <Link href={`/projects/${id}`} className="mt-5 inline-flex items-center gap-1 text-sm font-bold text-forest">Public project view <ExternalLink size={14} /></Link>
    </div>
    <div className="mt-9"><div className="eyebrow">Applications</div><h2 className="mt-1 text-xl font-bold">Student interest <span className="text-muted">· {apps.length}</span></h2></div>
    {apps.length === 0 ? <div className="mt-4"><EmptyState title="No applications yet" body="Applications will appear here when students apply to your project." /></div> : <div className="mt-4 grid gap-4">{apps.map((application, index) => <article key={application.id} className="card p-5">
      <div className="flex flex-wrap items-center justify-between gap-3"><div><div className="text-xs font-bold text-muted">Applicant {index + 1}</div><div className="mt-1 break-all font-mono text-xs text-muted">Student ID: {application.student_id}</div></div><span className={`status status-${application.status.toLowerCase()}`}>{application.status}</span></div>
      <div className="mt-4 rounded-xl bg-paper p-4"><div className="text-xs font-bold text-muted">Application message</div><p className="mt-2 whitespace-pre-wrap text-sm leading-6">{application.message}</p></div>
      {application.status === "PENDING" && <div className="mt-4 flex flex-wrap justify-end gap-2"><button disabled={Boolean(busy)} onClick={() => void decide(application, "REJECTED")} className="btn btn-ghost"><X size={15} /> Reject</button><button disabled={Boolean(busy)} onClick={() => void decide(application, "ACCEPTED")} className="btn btn-primary"><Check size={15} /> Accept</button></div>}
    </article>)}</div>}
    {notice && <Toast message={notice} onClose={() => setNotice("")} />}
  </div>;
}
