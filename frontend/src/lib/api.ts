/**
 * Thin fetch wrapper around the FastAPI backend. Base URL is read from
 * NEXT_PUBLIC_API_URL so the deployment topology (local vs Docker vs cloud)
 * never requires code changes.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Provider = "ollama" | "anthropic";

export interface SourceCitation {
  episode: string;
  guest?: string;
  timestamp?: string;
  score: number;
}

export interface ChatResponse {
  session_id: string;
  message_id: string;
  content: string;
  sources: SourceCitation[];
  provider_used: string;
  artifact_id?: string | null;
}

export interface ArtifactResponse {
  id: string;
  artifact_type: "markdown" | "html";
  title: string;
  content: string;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export const api = {
  createSession: (provider: Provider) =>
    request<{ id: string }>("/api/sessions", {
      method: "POST",
      body: JSON.stringify({ provider }),
    }),

  sendChat: (sessionId: string, message: string, mode: "default" | "ship30", provider: Provider) =>
    request<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, message, mode, provider }),
    }),

  getArtifact: (artifactId: string) => request<ArtifactResponse>(`/api/artifacts/${artifactId}`),

  health: () => request<{ status: string; database: boolean; ollama: boolean }>("/api/health"),
};
