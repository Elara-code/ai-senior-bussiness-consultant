export type ProjectStage = "discovery" | "requirements" | "solution" | "proposal" | "delivery" | "closed";

export type Project = {
  id: string;
  name: string;
  description: string;
  stage: ProjectStage;
  updated_at: string;
};

const API_URL = process.env.CONSULTANT_API_URL ?? "http://localhost:8000";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = process.env.CONSULTANT_DEV_TOKEN;
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json() as Promise<T>;
}

export const listProjects = () => apiFetch<Project[]>("/api/v1/projects");
