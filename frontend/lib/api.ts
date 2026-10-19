/**
 * Typed HTTP client for the Professor Fritts harness API.
 * Base URL comes from NEXT_PUBLIC_API_BASE_URL (see root .env.example).
 */

import type {
  BuildingPrefill,
  DocumentResponse,
  FixtureListResponse,
  FixtureRunResponse,
  HealthResponse,
  LiveRunStartResponse,
  MessageCreateRequest,
  MessageRunResponse,
  ProfileUpdateRequest,
  ReplayCaseListResponse,
  ReplayResponse,
  RoofSuggestion,
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

/**
 * Lists mock situations for the landing page. A new folder under
 * backend/mocks/fixtures appears here without a frontend change.
 */
export async function listFixtures(): Promise<FixtureListResponse> {
  return requestJson<FixtureListResponse>("/api/dev/fixtures");
}

/**
 * Runs one fixture through the harness. The server chooses Claude vs the
 * scripted transcript; this call does not send an LLM provider.
 */
export async function runFixture(caseId: string): Promise<FixtureRunResponse> {
  return requestJson<FixtureRunResponse>(`/api/dev/fixtures/${encodeURIComponent(caseId)}/run`, {
    method: "POST",
    body: "{}",
  });
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

/**
 * Starts a run in the background and returns at once. A real analysis takes about two minutes, so the page then asks
 * getLatestRun every couple of seconds. A 429 means the day's limit on real runs is used up (the message says so), and
 * a 409 means this session already has a run going.
 */
export async function startRun(sessionId: string, body: MessageCreateRequest): Promise<LiveRunStartResponse> {
  return requestJson<LiveRunStartResponse>(`/api/sessions/${sessionId}/runs`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** The newest run for a session with the steps it has taken so far. A 404 just means the run has not been created yet. */
export async function getLatestRun(sessionId: string): Promise<RunResponse> {
  return requestJson<RunResponse>(`/api/sessions/${sessionId}/latest-run`);
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

/**
 * Asks the backend for a suggested roof area: the ground area of the building outlines on the tax
 * lot at this address, from NYC building footprints. The answer is a suggestion for the user to
 * confirm, never a measured roof. A 404 means the address or its outlines were not found.
 */
export async function getRoofSuggestion(address: string, borough: string): Promise<RoofSuggestion> {
  const params = new URLSearchParams({ address, borough });
  return requestJson<RoofSuggestion>(`/api/records/roof-suggestion?${params.toString()}`);
}

/**
 * Asks the backend what the city's free records already say about a building (yearly electricity, the roof assessment,
 * solar already installed, a roof-area suggestion), so the design page can fill in the form. It uses no Claude. Every value
 * is a suggestion for the visitor to confirm. Parts the city has no record for are simply left out and listed in `missing`.
 */
export async function getBuildingPrefill(bbl: string, address: string, borough: string): Promise<BuildingPrefill> {
  const params = new URLSearchParams({ bbl, address, borough });
  return requestJson<BuildingPrefill>(`/api/records/building-prefill?${params.toString()}`);
}

/**
 * The saved demos the planner can replay. Replays never call Claude: the server plays a saved run back through
 * its own checks, so they cost nothing and are safe on the public site.
 */
export async function listReplayCases(): Promise<ReplayCaseListResponse> {
  return requestJson<ReplayCaseListResponse>("/api/replay/cases");
}

/**
 * Replays one saved demo. The whole run comes back at once (about a second); the planner page then plays the
 * run log back step by step so it looks like a live run.
 */
export async function replayCase(caseId: string): Promise<ReplayResponse> {
  return requestJson<ReplayResponse>(`/api/replay/${encodeURIComponent(caseId)}`, { method: "POST", body: "{}" });
}

export interface PlanChatRequest {
  plan_summary: Record<string, unknown>;
  question: string;
  history?: { role: string; content: string }[];
}

export interface PlanChatResponse {
  reply: string;
}

/**
 * Ask a follow-up question or brainstorm with Claude in the context of the generated plan.
 */
export async function askPlanQuestion(
  planSummary: Record<string, unknown>,
  question: string,
  history: { role: string; content: string }[] = []
): Promise<string> {
  const res = await requestJson<PlanChatResponse>("/api/plans/chat", {
    method: "POST",
    body: JSON.stringify({ plan_summary: planSummary, question, history }),
  });
  return res.reply;
}
