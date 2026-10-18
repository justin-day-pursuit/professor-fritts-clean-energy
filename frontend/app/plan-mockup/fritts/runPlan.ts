/**
 * The order and timing of Professor Fritts's scenes while the plan is worked out.
 *
 * He moves through five scenes, always in the same order: thinking over his clipboard (the opening), researching, reading,
 * the chalkboard, then writing his notes.
 * Each scene stays on screen for exactly one full pass of its animation, so no animation is ever cut off. The steps on the
 * working list are sorted into the scene that fits them and spread evenly across it, so the list and the progress bar fill
 * up at the pace of the animation.
 *
 * Note: sorting means the list can read in a slightly different order than the tools were first used. This is the replay
 * mockup; a live run would show its steps as they really happen.
 */

import { poseForStep, type PoseName } from "./poses";
import { BOARD } from "./rigs";

/** One scene: which pose he takes and how long it lasts (milliseconds). */
export interface Scene {
  pose: PoseName;
  ms: number;
}

/** The chalkboard scene lasts exactly as long as the film: it plays once from start to finish, with no pause on the finished board. */
const BOARD_SCENE_MS = BOARD.filmMs;

/**
 * The scenes, in order. The opening one is a still picture, so its length is only a pause long enough to read the first step. Researching and reading are about one cycle of their slow movement (the magnifying glass roaming
 * and the book rising and settling); writing notes is three cycles of the pen, which are not stretched to fill the time (about 3 s per step).
 */
export const SCENES: readonly Scene[] = [
  { pose: "studying", ms: 3000 },
  { pose: "researching", ms: 6000 },
  { pose: "reading", ms: 6000 },
  { pose: "calculating", ms: BOARD_SCENE_MS },
  { pose: "analyze", ms: 6000 },
  { pose: "writing", ms: 3000 },
];

/** The working list laid out in time. */
export interface RunPlan {
  /** The steps in scene order. */
  lines: string[];
  /** When each step starts, in milliseconds from the beginning of the run. */
  starts: number[];
  /** When the last scene ends. */
  total: number;
}

/** Sorts the steps into scenes and spreads them evenly across each scene. A scene with no steps is skipped. */
export function planRun(steps: string[]): RunPlan {
  const lines: string[] = [];
  const starts: number[] = [];
  let clock = 0;
  for (const scene of SCENES) {
    const mine = steps.filter((s) => poseForStep(s) === scene.pose);
    if (mine.length === 0) continue;
    const each = scene.ms / mine.length;
    mine.forEach((step, i) => {
      lines.push(step);
      starts.push(clock + i * each);
    });
    clock += scene.ms;
  }
  return { lines, starts, total: clock };
}
