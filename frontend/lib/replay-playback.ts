/**
 * Timing for playing a saved run back in the planner, so it looks like a run happening now.
 *
 * The server returns the whole saved run at once. The page then shows its steps one at a time, waiting
 * longer after the steps that take real time in a live run (tool calls, tool results, the final check)
 * and barely at all after bookkeeping steps. The waits are scaled down so a long run still finishes in
 * about PLAYBACK_TARGET_MS. Nothing here calls the server or Claude.
 */
import type { RunEventResponse } from "@/lib/types";

/** Rough wait, in milliseconds, after each kind of step before the next one appears. */
export const EVENT_DELAY_MS: Record<string, number> = {
  check1: 400,
  check2: 250,
  check3: 250,
  check4: 800,
  think: 900,
  tool_call: 700,
  tool_result: 1000,
  note_update: 120,
  usage: 100,
  final: 600,
  error: 700,
};

/** A whole replay should take about this long, however many steps the saved run has. */
export const PLAYBACK_TARGET_MS = 26000;

/** The shortest pause between two steps, so nothing flashes past unseen. */
export const MIN_DELAY_MS = 40;

/**
 * Milliseconds to wait before showing each step, one number per event in the same order.
 *
 * Steps of a kind not in EVENT_DELAY_MS wait 300 ms. If the waits add up to more than
 * PLAYBACK_TARGET_MS they are all scaled down by the same factor; short runs are not slowed down.
 */
export function playbackDelays(events: Pick<RunEventResponse, "kind">[]): number[] {
  const raw = events.map((event) => EVENT_DELAY_MS[event.kind] ?? 300);
  const total = raw.reduce((sum, ms) => sum + ms, 0);
  const scale = total > PLAYBACK_TARGET_MS ? PLAYBACK_TARGET_MS / total : 1;
  return raw.map((ms) => Math.max(MIN_DELAY_MS, Math.round(ms * scale)));
}
