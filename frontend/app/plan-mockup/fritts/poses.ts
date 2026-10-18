/**
 * The list of poses Professor Fritts can take, and which picture, animation or video shows each one.
 *
 * To swap in a new pose: put the file in frontend/public/fritts/poses/ and change that pose's entry below. Nothing else
 * needs to change. A pose can be:
 *  - "rig":   the layered, animated Gentleman Host (body, head, hands and blinking eyes moved by the page),
 *  - "layers": one of the layered poses from the animation sheet (waving, explaining, reading and so on), described in ./rigs.ts,
 *  - "board": the chalkboard film, played frame by frame,
 *  - "image": a still picture or an animated GIF with a see-through background (PNG, WebP or GIF),
 *  - "video": a short looping clip (a WebM with transparency works best; MP4 has a solid background).
 * Any pose left as "rig" shows the Gentleman Host, so a missing picture never leaves the screen empty.
 */

import type { RigId } from "./rigs";

/** Every pose the script can ask for. */
export type PoseName =
  | "welcome"
  | "explaining"
  | "listening"
  | "thinking"
  | "reassuring"
  | "delighted"
  | "analyze"
  | "present"
  | "reading"
  | "researching"
  | "calculating"
  | "studying"
  | "presenting";

/** How one pose is drawn. */
export type PoseAsset =
  | { kind: "rig" }
  | { kind: "layers"; rig: RigId }
  | { kind: "board" }
  | { kind: "image"; src: string; alt: string; flip?: boolean; grow?: number }
  | { kind: "video"; src: string; poster?: string; alt: string };

/** The current picture for each pose. The poses the animation sheet has no match for (listening, reassuring) keep the layered Gentleman Host. */
export const POSES: Record<PoseName, PoseAsset> = {
  welcome: { kind: "layers", rig: "greet" },
  explaining: { kind: "layers", rig: "explain" },
  listening: { kind: "rig" },
  thinking: { kind: "layers", rig: "research" },
  reassuring: { kind: "rig" },
  delighted: { kind: "layers", rig: "hello" },
  analyze: { kind: "layers", rig: "analyze" },
  present: { kind: "layers", rig: "report" },
  reading: { kind: "layers", rig: "read" },
  researching: { kind: "layers", rig: "research" },
  calculating: { kind: "board" },
  // The two still pictures cut from the character sheet: him thinking over a clipboard, and him presenting the report.
  studying: { kind: "image", src: "/fritts/poses/fritts-analyze.png", alt: "Professor Fritts thinking over a clipboard" },
  // Beside the report: mirrored, and drawn a little bigger (the bubble keeps its place).
  presenting: { kind: "image", src: "/fritts/poses/fritts-present.png", alt: "Professor Fritts presenting a report", flip: true, grow: 1.05 },
};

/**
 * Picks the pose that matches what he is doing while the plan is worked out, from the sentence on the working list.
 * The first step, reading the building details, shows him thinking over his clipboard. Looking things up (the roof and sun, prices, risk) shows him with the magnifying glass; city records and
 * rules show him reading; the numbers and the battery sizing go on the chalkboard; everything else (costing the scenarios,
 * checking sources, writing) is note-taking.
 * ./runPlan.ts uses this to sort the steps into scenes.
 */
export function poseForStep(step: string): PoseName {
  const text = step.toLowerCase();
  if (/building details/.test(text)) return "studying";
  if (/records|incentive|rules/.test(text)) return "reading";
  if (/solar|flood|heat|electricity|tariff|prices/.test(text)) return "researching";
  if (/numbers|sizing|battery/.test(text)) return "calculating";
  return "analyze";
}

/** Where Fritts stands on screen: big in the middle, big at the left beside the work, larger at the edge beside the form, or small at the edge beside the report. */
export type Placement = "center" | "stage" | "form" | "side";

/** Which edge he stands at while you fill in the form or read the report (the "form" and "side" spots). Change to "left" to move him. */
export const SIDE_OF_SCREEN: "left" | "right" = "right";
