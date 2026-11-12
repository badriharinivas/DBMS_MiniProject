"use client";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Building2, Check, Clock3, UserRound } from "lucide-react";
import { useParams } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import { api, ApiError } from "@/lib/api";
import type { Application, Project } from "@/types/api";
import { EmptyState, ErrorNotice, PageLoading, SubmitButton, Toast } from "@/components/ui";

export default function ProjectDetailsPage() {
  return <Details />;
}

function Details() {
  const { id } = useParams<{ id: string }>();
  const { user, token } = useAuth();
  const [project, setProject] = useState<Project | null>(null);
  const [application, setApplication] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let alive = true;
    api.project(id, token || undefined)
      .then(value => { if (alive) setProject(value); })
      .catch(cause => { if (alive) setError(cause instanceof ApiError ? cause.message : "Could not load this project."); })
      .finally(() => { if (alive) setLoading(false); });
    if (user?.role === "STUDENT" && token) {
      api.myApplications(token)
        .then(items => { if (alive) setApplication(items.find(item => item.project_id === id) || null); })
        .catch(() => { /* Submission still relies on the backend's duplicate check. */ });
    }
    return () => { alive = false; };
  }, [id, user, token]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !user) return;
    setBusy(true);
    setError("");
    try {
      const saved = await api.apply(id, message, token);
      setApplication(saved);
      setNotice("Your application was submitted.");
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not submit your application.");
    } finally { setBusy(false); }
  }

  if (loading) return <PageLoading label="Loading project details…" />;
  if (!project) return <div className="container max-w-3xl py-12">{error ? <ErrorNotice message={error} /> : <EmptyState title="Project unavailable" body="This project could not be found." />}<Link href="/projects" className="mt-5 inline-flex items-center gap-2 text-sm font-bold text-forest"><ArrowLeft size={15} /> Browse projects</Link></div>;

  return <div className="container max-w-4xl py-10">
    <Link href="/projects" className="inline-flex items-center gap-1 text-xs font-bold text-muted hover:text-forest"><ArrowLeft size={14} /> All projects</Link>
    {error && <div className="mt-5"><ErrorNotice message={error} /></div>}
    <div className="mt-5 grid gap-6 lg:grid-cols-[1fr_310px]">
      <article className="card p-6 sm:p-9">
        <div className="flex flex-wrap items-center gap-3"><span className={`status ${project.status === "OPEN" ? "status-open" : "status-closed"}`}>{project.status}</span><span className="flex items-center gap-1 text-xs text-muted"><Clock3 size={13} /> Posted {new Date(project.created_at).toLocaleDateString()}</span></div>
        <h1 className="mt-5 text-3xl font-bold leading-tight tracking-tight">{project.title}</h1>
        <div className="mt-8"><div className="eyebrow">About this research</div><p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-[#49584f]">{project.description}</p></div>
        <div className="mt-8 border-t border-line pt-6"><div className="eyebrow">Skills and experience</div>{project.required_skills.length ? <div className="mt-3 flex flex-wrap gap-2">{project.required_skills.map(skill => <span key={skill} className="rounded-full bg-paper px-3 py-1.5 text-xs font-semibold">{skill}</span>)}</div> : <p className="mt-3 text-sm text-muted">No specific skills listed.</p>}</div>
        <div className="mt-8 border-t border-line pt-6"><div className="eyebrow">Project contact</div><div className="mt-3 flex items-center gap-3 rounded-xl bg-paper p-3"><span className="grid h-10 w-10 place-items-center rounded-full bg-mint text-forest"><UserRound size={18} /></span><div><div className="text-sm font-bold">Faculty-led research</div><div className="mt-0.5 text-xs text-muted">Project owner ID: {project.faculty_id}</div></div><Building2 size={17} className="ml-auto text-muted" /></div><p className="mt-2 text-xs leading-5 text-muted">The project detail API does not include the faculty name or department, so this page only shows the owner ID returned by the backend.</p></div>
      </article>
      <aside className="h-fit">
        {user?.role === "STUDENT" ? <div className="card p-5"><div className="eyebrow">Interested?</div>{application ? <div className="mt-4"><div className="flex items-center gap-2 text-sm font-bold text-forest"><Check size={17} /> Application submitted</div><div className={`status status-${application.status.toLowerCase()} mt-3`}>{application.status}</div><p className="mt-3 text-xs leading-5 text-muted">Track your application and status from your applications page.</p><Link href="/applications" className="mt-4 flex items-center gap-1 text-sm font-bold text-forest">View applications <ArrowRight size={14} /></Link></div> : project.status === "OPEN" ? <form onSubmit={submit} className="mt-4"><div className="field"><label htmlFor="message">Message to the faculty <span className="font-normal text-muted">(20–4,000 characters)</span></label><textarea id="message" className="input !min-h-[150px] text-sm" minLength={20} maxLength={4000} required value={message} onChange={event => setMessage(event.target.value)} placeholder="Share why this project interests you and what you’d bring…" /></div><SubmitButton busy={busy} className="w-full">Apply to project <ArrowRight size={15} /></SubmitButton></form> : <p className="mt-3 text-sm text-muted">This project is closed and isn’t accepting applications.</p>}{error && <div className="mt-3"><ErrorNotice message={error} /></div>}</div> : user?.role === "FACULTY" && user.id === project.faculty_id ? <div className="card p-5"><div className="eyebrow">Project management</div><Link href={`/faculty/projects/${id}`} className="btn btn-primary mt-4 w-full">Manage applicants <ArrowRight size={15} /></Link></div> : <div className="card p-5"><div className="eyebrow">Ready to take a closer look?</div><p className="mt-2 text-sm leading-6 text-muted">Sign in as a student to apply to open projects.</p><Link href="/login" className="btn btn-primary mt-4 w-full">Log in to apply</Link></div>}
      </aside>
    </div>
    {notice && <Toast message={notice} onClose={() => setNotice("")} />}
  </div>;
}
