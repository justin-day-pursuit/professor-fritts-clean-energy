/**
 * The list of poses Professor Fritts can take, and which picture, animation or video shows each one.
 *
 * To swap in a new pose: put the file in frontend/public/fritts/poses/ and change that pose's entry below. Nothing else
 * needs to change. A pose can be:
 *  - "rig":   the layered, animated Gentleman Host (body, head, hands and blinking eyes moved by the page),
 *  - "image": a still picture or an animated GIF with a see-through background (PNG, WebP or GIF),
 *  - "video": a short looping clip (a WebM with transparency works best; MP4 has a solid background).
 * Any pose left as "rig" shows the Gentleman Host, so a missing picture never leaves the screen empty.
 */

/** Every pose the script can ask for. */
export type PoseName = "welcome" | "explaining" | "listening" | "thinking" | "reassuring" | "delighted" | "analyze" | "present";

/** How one pose is drawn. */
export type PoseAsset =
  | { kind: "rig" }
  | { kind: "image"; src: string; alt: string }
  | { kind: "video"; src: string; poster?: string; alt: string };

/** The current picture for each pose. The two image poses are placeholders cut from the character sheet. */
export const POSES: Record<PoseName, PoseAsset> = {
  welcome: { kind: "rig" },
  explaining: { kind: "rig" },
  listening: { kind: "rig" },
  thinking: { kind: "rig" },
  reassuring: { kind: "rig" },
  delighted: { kind: "rig" },
  analyze: { kind: "image", src: "/fritts/poses/fritts-analyze.png", alt: "Professor Fritts studying a clipboard" },
  present: { kind: "image", src: "/fritts/poses/fritts-present.png", alt: "Professor Fritts presenting a report" },
};

/** Where Fritts stands on screen: big in the middle, big at the left beside the work, larger at the edge beside the form, or small at the edge beside the report. */
export type Placement = "center" | "stage" | "form" | "side";

/** Which edge he stands at while you fill in the form or read the report (the "form" and "side" spots). Change to "left" to move him. */
export const SIDE_OF_SCREEN: "left" | "right" = "right";
