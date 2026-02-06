const API_BASE = "/api";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(
      error.detail || response.statusText,
      response.status,
      error.code
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Auth API
export const authApi = {
  me: () => request<User | null>("/auth/me"),
  register: (data: { email: string; password: string; name: string }) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  login: (data: { email: string; password: string }) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  logout: () =>
    request<void>("/auth/logout", {
      method: "POST",
    }),
};

// Projects API
export const projectsApi = {
  list: () => request<Project[]>("/projects"),
  get: (projectId: number) => request<Project>(`/projects/${projectId}`),
  create: (data: { title: string; description?: string; scriptContent: string }) =>
    request<{ projectId: number }>("/projects", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getScenes: (projectId: number) =>
    request<Scene[]>(`/projects/${projectId}/scenes`),
  getCharacters: (projectId: number) =>
    request<Character[]>(`/projects/${projectId}/characters`),
  getSettings: (projectId: number) =>
    request<Setting[]>(`/projects/${projectId}/settings`),
  getStoryboards: (projectId: number) =>
    request<StoryboardImage[]>(`/projects/${projectId}/storyboards`),
  getFinalMovie: (projectId: number) =>
    request<FinalMovie | null>(`/projects/${projectId}/movie`),
};

// Workflow API
export const workflowApi = {
  start: (projectId: number, workflowType: string) =>
    request<{ success: boolean }>(`/workflow/${projectId}/start`, {
      method: "POST",
      body: JSON.stringify({ workflowType }),
    }),
  getStatus: (projectId: number) =>
    request<WorkflowStatus>(`/workflow/${projectId}/status`),
  pause: (projectId: number) =>
    request<void>(`/workflow/${projectId}/pause`, { method: "POST" }),
  resume: (projectId: number) =>
    request<void>(`/workflow/${projectId}/resume`, { method: "POST" }),
};

// Types
export interface User {
  id: number;
  openId: string;
  email: string;
  name: string | null;
  role: string;
  createdAt: string;
}

export interface AuthResponse {
  user: User;
  message: string;
}

export interface Project {
  id: number;
  userId: number;
  title: string;
  description: string | null;
  scriptContent: string;
  status: string;
  progress: number;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface Scene {
  id: number;
  projectId: number;
  sceneNumber: number;
  title: string;
  description: string;
  setting: string | null;
  characters: string | null;
  duration: number | null;
  order: number;
  createdAt: string;
  updatedAt: string;
}

export interface Character {
  id: number;
  projectId: number;
  name: string;
  description: string;
  visualDescription: string | null;
  imageUrl: string | null;
  imageKey: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface Setting {
  id: number;
  projectId: number;
  name: string;
  description: string;
  visualDescription: string | null;
  imageUrl: string | null;
  imageKey: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface StoryboardImage {
  id: number;
  sceneId: number;
  projectId: number;
  imageUrl: string;
  imageKey: string;
  prompt: string | null;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface FinalMovie {
  id: number;
  projectId: number;
  movieUrl: string | null;
  movieKey: string | null;
  duration: number | null;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowStatus {
  projectId: number;
  status: string;
  progress: number;
  currentStep: string | null;
  error: string | null;
}

export { ApiError };
