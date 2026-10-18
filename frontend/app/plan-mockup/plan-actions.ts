/**
 * The two things a visitor does with a finished report: download it as a PDF, and share a link to it.
 *
 * The PDF is made by the backend (POST /api/plans/pdf), which draws the plain report only, never the developer view. It
 * uses no Claude credits. The share link is a demo link for now: plans are not saved anywhere yet, so the link opens the
 * saved sample report it was made from.
 */
import type { PlanSummary } from "./plan-types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

/** How a PDF request ended. */
export type PdfResult = "done" | "unreachable" | "failed";

/** The file name the backend suggests, or a plain default. */
function fileNameFrom(header: string | null): string {
  const match = header?.match(/filename="?([^";]+)"?/i);
  return match?.[1] ?? "professor-fritts-plan.pdf";
}

/** Asks the backend for the plan as a PDF and hands it to the browser as a download. */
export async function downloadPlanPdf(plan: PlanSummary): Promise<PdfResult> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/plans/pdf`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plan_summary: plan }),
    });
  } catch {
    return "unreachable";
  }
  if (!response.ok) return "failed";
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileNameFrom(response.headers.get("Content-Disposition"));
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  return "done";
}

/** The demo link for a saved sample report. */
export function shareLinkFor(sampleId: string): string {
  return `${window.location.origin}/plan-mockup?view=results&sample=${encodeURIComponent(sampleId)}`;
}

/** A link cut short with "..." so it fits in a small space, like "http://localhost:3000/plan-mockup?vie...". */
export function shortLink(url: string, max = 38): string {
  return url.length > max ? `${url.slice(0, max)}...` : url;
}

/** Puts the share link on the clipboard. The link is returned either way so it can be shown if copying is blocked. */
export async function copyShareLink(sampleId: string): Promise<{ url: string; copied: boolean }> {
  const url = shareLinkFor(sampleId);
  try {
    await navigator.clipboard.writeText(url);
    return { url, copied: true };
  } catch {
    return { url, copied: false };
  }
}
