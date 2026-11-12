import type { Application, Department, Interest, Project, ProjectPage, RecommendationPage, SearchPage, TokenResponse, User } from "@/types/api";

const BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");
export class ApiError extends Error { constructor(message: string, public status: number, public details?: unknown) { super(message); this.name = "ApiError"; } }
let unauthorizedHandler: (() => void) | undefined;
export function setUnauthorizedHandler(handler: () => void) { unauthorizedHandler = handler; }
export async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  let response: Response;
  try { response = await fetch(`${BASE}${path}`, { ...options, headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers }, cache: "no-store" }); }
  catch { throw new ApiError("Unable to reach MentorMatch. Check that the API is running and try again.", 0); }
  if (response.status === 204) return undefined as T;
  const data: unknown = await response.json().catch(() => undefined);
  if (!response.ok) {
    if (response.status === 401) unauthorizedHandler?.();
    const body = data as { detail?: unknown } | undefined;
    const detail = body?.detail;
    const message = typeof detail === "string" ? detail : Array.isArray(detail) ? detail.map((item) => typeof item === "object" && item && "msg" in item ? String(item.msg) : "Invalid input").join("; ") : `Request failed (${response.status})`;
    throw new ApiError(message, response.status, data);
  }
  return data as T;
}
const json = (method: string, body: unknown): RequestInit => ({ method, body: JSON.stringify(body) });
export const api = {
  departments: () => request<Department[]>("/departments?limit=200"),
  register: (body: { name: string; email: string; password: string; role: string; department_id: string }) => request<User>("/auth/register", json("POST", body)),
  login: (body: { email: string; password: string }) => request<TokenResponse>("/auth/login", json("POST", body)),
  me: (token: string) => request<User>("/auth/me", {}, token),
  projects: (params = "") => request<ProjectPage>(`/projects?limit=100${params}`, {}, getToken()),
  search: (q: string) => request<SearchPage>(`/projects/search?q=${encodeURIComponent(q)}&limit=100`),
  project: (id: string, token?: string) => request<Project>(`/projects/${id}`, {}, token),
  createProject: (body: { title: string; description: string; required_skills: string[] }, token: string) => request<Project>("/projects", json("POST", body), token),
  updateProject: (id: string, body: Partial<Pick<Project, "title" | "description" | "required_skills" | "status">>, token: string) => request<Project>(`/projects/${id}`, json("PATCH", body), token),
  interest: (token: string) => request<Interest>("/students/me/interests", {}, token),
  saveInterest: (body: { description: string; skills: string[] }, token: string, create: boolean) => request<Interest>("/students/me/interests", json(create ? "POST" : "PUT", body), token),
  recommendations: (token: string) => request<RecommendationPage>("/recommendations?limit=50", {}, token),
  apply: (id: string, message: string, token: string) => request<Application>(`/projects/${id}/applications`, json("POST", { message }), token),
  myApplications: (token: string) => request<Application[]>("/applications/me?limit=100", {}, token),
  projectApplications: (id: string, token: string) => request<Application[]>(`/projects/${id}/applications?limit=100`, {}, token),
  updateApplication: (id: string, status: "ACCEPTED" | "REJECTED", token: string) => request<Application>(`/applications/${id}/status`, json("PATCH", { status }), token),
};
export function getToken() { return typeof window === "undefined" ? undefined : sessionStorage.getItem("mm_token") || undefined; }
