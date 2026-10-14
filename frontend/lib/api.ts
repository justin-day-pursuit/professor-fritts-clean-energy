/**
 * Typed HTTP client for the Professor Fritts harness API.
 * Base URL comes from NEXT_PUBLIC_API_BASE_URL (see root .env.example).
 */

import type {
  DocumentResponse,
  HealthResponse,
  MessageCreateRequest,
  MessageRunResponse,
  ProfileUpdateRequest,
  RunResponse,
  SessionCreateRequest,
  SessionResponse,
} from "@/lib/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

/** Error shape FastAPI returns — surfaced in a plain alert in the UI. */
export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Turns a failed HTTP body into one sentence for the red alert on the planner.
 * FastAPI often sends { detail: string } or { detail: [{ msg }] }; Django may
 * send plain text. If the backend error JSON shape changes, update the detail
 * parsing here so every caller of requestJson stays correct.
 */
async function parseErrorMessage(res: Response): Promise<string> {
  const text = await res.text();
  try {
    const body = JSON.parse(text) as { detail?: string | { msg?: string }[] };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      return body.detail.map((d) => d.msg).join("; ");
    }
  } catch {
    /* use raw text */
  }
  return text || res.statusText || `Request failed (${res.status})`;
}

/**
 * Shared fetch wrapper for JSON API calls: sets Accept/Content-Type, throws
 * ApiError on non-OK, and parses the body. createSession, postMessage, and the
 * other helpers all go through this. If the app later needs auth headers or a
 * different base URL per request, add them here rather than in each helper.
 */
async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  });
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorMessage(res));
  }
  return res.json() as Promise<T>;
}

export function getApiBaseUrl(): string {
  return API_BASE;
}

export async function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/api/health");
}

export async function createSession(body: SessionCreateRequest): Promise<SessionResponse> {
  return requestJson<SessionResponse>("/api/sessions", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getSession(sessionId: string): Promise<SessionResponse> {
  return requestJson<SessionResponse>(`/api/sessions/${sessionId}`);
}

export async function updateProfile(
  sessionId: string,
  body: ProfileUpdateRequest
): Promise<SessionResponse> {
  return requestJson<SessionResponse>(`/api/sessions/${sessionId}/profile`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export async function uploadDocument(
  sessionId: string,
  file: File
): Promise<DocumentResponse> {
  const form = new FormData();
  form.append("file", file);
  return requestJson<DocumentResponse>(`/api/sessions/${sessionId}/documents`, {
    method: "POST",
    body: form,
  });
}

export async function postMessage(
  sessionId: string,
  body: MessageCreateRequest
): Promise<MessageRunResponse> {
  return requestJson<MessageRunResponse>(`/api/sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getRun(runId: number): Promise<RunResponse> {
  return requestJson<RunResponse>(`/api/runs/${runId}`);
}

export async function downloadRoadmapMarkdown(runId: number): Promise<string> {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/roadmap.md`);
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorMessage(res));
  }
  return res.text();
}

export async function downloadRoadmapJson(runId: number): Promise<string> {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/roadmap.json`);
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorMessage(res));
  }
  return res.text();
}
