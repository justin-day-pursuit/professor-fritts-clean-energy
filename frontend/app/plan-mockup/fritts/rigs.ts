/**
 * The layered poses of Professor Fritts, described as plain data.
 *
 * Each pose is a body picture with a few cut-out pieces on top (a hand, a pen, a book, the head with blinking eyelids).
 * This file says which pieces a pose has, where each one sits, and which point it turns around. The look of the movement
 * (waving, tapping, scribbling) lives in fritts.css under the pose's own class, "frg-p-<id>".
 *
 * Every position is a percentage of the pose's own picture, so the pieces stay lined up at any size. The numbers come from
 * the animation sheet Mara supplied (kept on her computer, not in the repo; a copy is in reference/artifacts/fritts-animations/).
 */

/** The poses that are built from layers. */
export type RigId = "hello" | "greet" | "explain" | "good" | "report" | "analyze" | "read" | "research";

/** A rectangle placed on the pose's picture, as percentages. Height is left out when the picture's own shape sets it. */
interface Box {
  left: number;
  top: number;
  width: number;
  height?: number;
}

/** One piece drawn on top of the body, in the order they are listed (later pieces are drawn in front). */
export type Layer =
  /** A cut-out piece that turns around one point, such as a hand, a pen or a book. */
  | { kind: "part"; name: string; src: string; box: Box; origin: string }
  /** The head, with the two eyelids that blink over the eyes. */
  | { kind: "head"; src: string; box: Box; origin: string; lids: [Box, Box] }
  /** A gold outline that pulses around the chart he taps. */
  | { kind: "ring"; box: Box }
  /** A gold check mark that draws itself when he finishes his notes. */
  | { kind: "check"; box: Box }
  /** The magnifying glass, with a glint that crosses the lens. */
  | { kind: "glass"; src: string; box: Box; origin: string; glint: Box };

/** Everything needed to draw and animate one layered pose. */
export interface Rig {
  id: RigId;
  /** Read aloud for screen readers. */
  alt: string;
  /** The picture of the whole figure without the moving pieces. */
  base: string;
  /** Width and height of the picture, as multiples of the figure's standing height (so every pose stands equally tall). */
  w: number;
  k: number;
  /** How far the feet sit above the bottom of the picture, so his feet land on the floor line. */
  gap: number;
  /** Where on the picture's height the body breathes from, in percent. */
  floor: number;
  /** The skin tone of the eyelids, so they match the face. */
  lid: string;
  /** How long his action lasts when he is clicked or cued, in milliseconds. */
  dur: number;
  /** Optional: draw him larger than the others (1.15 is 15% taller), growing upward from the floor line. */
  scale?: number;
  /** Optional: raise him by this share of his own height (0.04 is 4%). */
  lift?: number;
  /** Optional: move only his figure (not his bubble) right by this many percent of his own width. */
  shift?: number;
  /** Optional: when he stands in the middle of the screen, move him (and his bubble) right by this many percent of his own width. */
  nudge?: number;
  /** Optional: when he stands in the middle of the screen, raise his speech bubble by this many percent of his height. */
  bubbleUp?: number;
  /** Optional: when he stands in the middle of the screen, where his bubble starts across his picture (100 is at his right edge; less is further left). */
  bubbleLeft?: number;
  layers: Layer[];
}

/** Folder the pieces are served from. */
const DIR = "/fritts/rigs/";

export const RIGS: Record<RigId, Rig> = {
  hello: {
    id: "hello",
    alt: "Professor Fritts in a navy tailcoat and teal waistcoat, one hand held out in welcome",
    base: `${DIR}L_base.webp`,
    w: 0.7535,
    k: 0.8848,
    gap: 0.0957,
    floor: 91.536,
    lid: "#f6d6ab",
    dur: 1600,
    // Shown after "I have everything", where he is drawn a little bigger than the others, with his head clear of the page title.
    scale: 1.12,
    lift: 0.02,
    bubbleLeft: 78,
    layers: [
      { kind: "part", name: "hand2", src: `${DIR}L_hand2.webp`, box: { left: 68.848, top: 48.763, width: 9.375, height: 9.57 }, origin: "47% 2%" },
      { kind: "part", name: "hand", src: `${DIR}L_hand.webp`, box: { left: 11.523, top: 30.859, width: 12.598, height: 8.529 }, origin: "91.5% 59.5%" },
      {
        kind: "head",
        src: `${DIR}L_head.webp`,
        box: { left: 37.109, top: 1.302, width: 25.391, height: 15.755 },
        origin: "48% 95%",
        lids: [
          { left: 31.9, top: 41.2, width: 12, height: 7 },
          { left: 53.6, top: 38, width: 12.4, height: 7.3 },
        ],
      },
    ],
  },
  greet: {
    id: "greet",
    alt: "Professor Fritts smiling and waving with his right hand raised",
    base: `${DIR}greet_base.webp`,
    w: 0.5595,
    k: 0.9844,
    gap: 0.0102,
    floor: 98.997,
    lid: "#fcdbb0",
    dur: 1800,
    // The welcome screen: raised a little so he stands higher on the page.
    lift: 0.04,
    layers: [
      { kind: "part", name: "hand", src: `${DIR}greet_hand.webp`, box: { left: 2.632, top: 8.919, width: 25.911, height: 15.162 }, origin: "45.703% 98.897%" },
      { kind: "part", name: "hand2", src: `${DIR}greet_hand2.webp`, box: { left: 81.579, top: 53.846, width: 13.36, height: 12.152 }, origin: "49.242% 4.128%" },
      {
        kind: "head",
        src: `${DIR}greet_head.webp`,
        box: { left: 35.425, top: 0, width: 37.045, height: 17.837 },
        origin: "50% 86.938%",
        lids: [
          { left: 30.601, top: 40, width: 16.94, height: 8.125 },
          { left: 58.47, top: 36.25, width: 13.115, height: 10.625 },
        ],
      },
    ],
  },
  explain: {
    id: "explain",
    alt: "Professor Fritts gesturing to the side with an open palm, his other hand resting at his waistcoat",
    base: `${DIR}E_base.webp`,
    w: 0.7556,
    k: 0.9625,
    gap: 0.0177,
    floor: 98.295,
    lid: "#fbdcb8",
    dur: 2000,
    // The "What to bring" screen: raised a little so he stands higher on the page, and moved a bit to the right.
    lift: 0.05,
    nudge: 10,
    bubbleUp: 3,
    layers: [
      { kind: "part", name: "hand", src: `${DIR}E_hand.webp`, box: { left: 77.188, top: 27.273, width: 19.844, height: 11.25 }, origin: "3.937% 69.697%" },
      {
        kind: "head",
        src: `${DIR}E_head.webp`,
        box: { left: 18.75, top: 0, width: 36.094, height: 18.182 },
        origin: "47.619% 87.5%",
        lids: [
          { left: 51.948, top: 36.875, width: 7.792, height: 7.5 },
          { left: 65.801, top: 32.5, width: 7.359, height: 8.75 },
        ],
      },
    ],
  },
  good: {
    id: "good",
    alt: "Professor Fritts holding a report to his chest and gesturing outward with a smile",
    base: `${DIR}good_base.webp`,
    w: 0.6467,
    k: 0.973,
    gap: 0.0081,
    floor: 99.213,
    lid: "#fbe7c0",
    dur: 1600,
    layers: [
      { kind: "part", name: "hand", src: `${DIR}good_hand.webp`, box: { left: 2.857, top: 27.865, width: 22.321, height: 12.247 }, origin: "89.6% 73.394%" },
      {
        kind: "head",
        src: `${DIR}good_head.webp`,
        box: { left: 35.714, top: 0, width: 37.679, height: 20.337 },
        origin: "49.763% 88.398%",
        lids: [
          { left: 46.445, top: 33.149, width: 13.27, height: 7.182 },
          { left: 69.668, top: 28.177, width: 8.531, height: 9.392 },
        ],
      },
    ],
  },
  report: {
    id: "report",
    alt: "Professor Fritts pointing at a bar chart on a report he is holding",
    base: `${DIR}report_base.webp`,
    w: 0.6713,
    k: 0.9708,
    gap: 0.0081,
    floor: 99.213,
    lid: "#fedeaf",
    dur: 1800,
    // The "I have your report" screen: his figure sits a little higher and to the right, with the bubble left where it is.
    lift: 0.04,
    shift: 3,
    layers: [
      { kind: "ring", box: { left: 65.862, top: 19.326, width: 24.138, height: 12.584 } },
      { kind: "part", name: "hand", src: `${DIR}report_hand.webp`, box: { left: 44.828, top: 27.865, width: 22.241, height: 10.899 }, origin: "1.55% 70.103%" },
      {
        kind: "head",
        src: `${DIR}report_head.webp`,
        box: { left: 14.483, top: 0, width: 35.69, height: 18.989 },
        origin: "49.758% 87.574%",
        lids: [
          { left: 49.275, top: 36.686, width: 14.493, height: 8.284 },
          { left: 73.43, top: 31.953, width: 6.763, height: 9.467 },
        ],
      },
    ],
  },
  analyze: {
    id: "analyze",
    alt: "Professor Fritts writing notes on a teal clipboard",
    base: `${DIR}analyze_base.webp`,
    w: 0.5794,
    k: 0.9697,
    gap: 0.0104,
    floor: 98.989,
    lid: "#fed9ab",
    dur: 2000,
    layers: [
      { kind: "check", box: { left: 66, top: 26.517, width: 18.8, height: 7.865 } },
      { kind: "part", name: "pen", src: `${DIR}analyze_pen.webp`, box: { left: 38.4, top: 22.472, width: 20.2, height: 14.944 }, origin: "23.762% 93.233%" },
      {
        kind: "head",
        src: `${DIR}analyze_head.webp`,
        box: { left: 20, top: 0, width: 36.2, height: 18.539 },
        origin: "49.724% 87.273%",
        lids: [
          { left: 58.564, top: 59.394, width: 16.575, height: 7.273 },
          { left: 81.215, top: 58.788, width: 13.812, height: 7.879 },
        ],
      },
    ],
  },
  read: {
    id: "read",
    alt: "Professor Fritts reading a leather-bound book",
    base: `${DIR}read_base.webp`,
    w: 0.5023,
    k: 0.981,
    gap: 0.0091,
    floor: 99.108,
    lid: "#ffdda8",
    dur: 2000,
    layers: [
      { kind: "part", name: "book", src: `${DIR}read_book.webp`, box: { left: 26.923, top: 25.418, width: 78.507, height: 21.293 }, origin: "50% 84.817%" },
      {
        kind: "head",
        src: `${DIR}read_head.webp`,
        box: { left: 29.412, top: 0, width: 42.76, height: 18.283 },
        origin: "49.868% 88.78%",
        lids: [
          { left: 32.804, top: 51.829, width: 15.873, height: 7.927 },
          { left: 59.788, top: 54.878, width: 15.344, height: 9.146 },
        ],
      },
    ],
  },
  research: {
    id: "research",
    alt: "Professor Fritts studying a sheet of paper through a magnifying glass",
    base: `${DIR}research_base.webp`,
    w: 0.5466,
    k: 0.981,
    gap: 0.0102,
    floor: 98.997,
    lid: "#feddad",
    dur: 1800,
    layers: [
      {
        kind: "head",
        src: `${DIR}research_head.webp`,
        box: { left: 32.432, top: 0, width: 35.343, height: 17.503 },
        origin: "49.706% 87.771%",
        lids: [
          { left: 38.824, top: 50.318, width: 17.647, height: 8.917 },
          { left: 70.588, top: 54.777, width: 15.294, height: 9.554 },
        ],
      },
      {
        kind: "glass",
        src: `${DIR}research_glass.webp`,
        box: { left: 37.838, top: 12.375, width: 34.096, height: 18.395 },
        origin: "31.707% 90.303%",
        glint: { left: 60.244, top: 6, width: 34.085, height: 33.879 },
      },
    ],
  },
};

/**
 * The chalkboard pose is a short film instead of layers: one animated picture (board.webp, 115 pictures at 24 per second,
 * which plays once and stops on the finished board) and a still of that finished board for people who ask for less motion.
 * Its picture is 373 x 409, which is 0.912 as wide as it is tall.
 */
export const BOARD = {
  alt: "Professor Fritts writing a solar panel output calculation on a chalkboard",
  film: `${DIR}board.webp`,
  still: `${DIR}board-still.webp`,
  fps: 24,
  /** How many pictures the film has. */
  playCount: 115,
  /** How long the film takes to play once (milliseconds). */
  filmMs: Math.round((115 / 24) * 1000),
  width: 373,
  height: 409,
  /** Feet sit this much above the bottom of the picture, as a share of the picture's height. */
  gap: 0.0108 * 0.9022,
  /**
   * The picture has empty easel space above him, so he fills only about 88% of its height while the other poses fill all of
   * theirs. Drawing it at exactly the guide's height keeps the whole figure, easel included, no taller than the others.
   */
  scale: 1.0,
  /** Pause on the finished board before it fades and starts over, and how long the fade takes (milliseconds). */
  holdMs: 2600,
  fadeMs: 450,
} as const;
