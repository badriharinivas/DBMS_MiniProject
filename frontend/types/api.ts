export type Role = "STUDENT" | "FACULTY";
export type ProjectStatus = "OPEN" | "CLOSED";
export type ApplicationStatus = "PENDING" | "ACCEPTED" | "REJECTED";
export interface User { id: string; name: string; email: string; role: Role; department_id: string; created_at: string }
export interface Department { id: string; name: string; description: string | null }
export interface Project { id: string; faculty_id: string; title: string; description: string; required_skills: string[]; status: ProjectStatus; created_at: string; updated_at: string }
export interface ProjectPage { items: Project[]; total: number; limit: number; offset: number }
export interface Recommendation extends Omit<Project, "faculty_id" | "created_at" | "updated_at"> { faculty_id: string; faculty_name: string; department_id: string; department_name: string; similarity: number }
export interface RecommendationPage { items: Recommendation[]; limit: number }
export interface Interest { id: string; student_id: string; description: string; skills: string[]; updated_at: string }
export interface Application { id: string; student_id: string; project_id: string; message: string; status: ApplicationStatus; created_at: string; updated_at: string }
export interface TokenResponse { access_token: string; token_type: "bearer"; expires_in: number; user: User }
export interface SearchPage extends ProjectPage { query: string }
