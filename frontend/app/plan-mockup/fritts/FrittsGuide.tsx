/* eslint-disable @next/next/no-img-element -- the character's layers are small, already-compressed pictures placed by percentage, which next/image cannot do. */
/**
 * Professor Fritts on screen: the character, where he stands, and his speech bubble with buttons.
 *
 * One guide stays on the page for the whole visit. The page tells it where to stand ("center" for the greeting and the
 * finished report, "stage" while he works, "side" while you fill in the form or read the report), which pose to take and
 * what to say. When the placement changes he glides to the new spot. Poses come from ./poses.ts, so a new picture,
 * animated GIF or video can be dropped in without touching this file.
 */
"use client";

import { useCallback, useEffect, useState, type AnimationEvent, type CSSProperties } from "react";
import "./fritts.css";
import { BoardFigure, LayeredFigure, preloadBoardFilm } from "./LayeredFigure";
import { RIGS } from "./rigs";
import { POSES, SIDE_OF_SCREEN, type Placement, type PoseAsset, type PoseName } from "./poses";

/** The class names in fritts.css. They all start with "frg-" so they cannot clash with anything else on the page. */
const styles = {
  above: "frg-above",
  action: "frg-action",
  actions: "frg-actions",
  appear: "frg-appear",
  big: "frg-big",
  base: "frg-base",
  body: "frg-body",
  bubble: "frg-bubble",
  center: "frg-center",
  close: "frg-close",
  figure: "frg-figure",
  flat: "frg-flat",
  flatFlip: "frg-flatFlip",
  grow: "frg-grow",
  flipped: "frg-flipped",
  greet: "frg-greet",
  guide: "frg-guide",
  hand: "frg-hand",
  hand2: "frg-hand2",
  head: "frg-head",
  lid: "frg-lid",
  lidLeft: "frg-lidLeft",
  lidRight: "frg-lidRight",
  line: "frg-line",
  primary: "frg-primary",
  reopen: "frg-reopen",
  rig: "frg-rig",
  sideLeft: "frg-sideLeft",
  sideRight: "frg-sideRight",
  stage: "frg-stage",
  wide: "frg-wide",
} as const;

/** One button in his speech bubble. */
export interface GuideAction {
  label: string;
  onClick: () => void;
  /** The main choice, drawn filled in. */
  primary?: boolean;
}

interface GuideProps {
  placement: Placement;
  pose: PoseName;
  line: string;
  actions?: GuideAction[];
  /** Makes the bubble wider and scrollable, for a long list of buttons. */
  wide?: boolean;
  /** Goes up by one each time he should give his welcome flourish (the greeting and the finished report). */
  cue: number;
}

/** The layered character: body, hands, head and blinking eyes, each moved a little so he seems alive. */
function Rig({ greeting, onGreetEnd }: { greeting: boolean; onGreetEnd: (e: AnimationEvent) => void }) {
  return (
    <div className={`${styles.rig} ${greeting ? styles.greet : ""}`} onAnimationEnd={onGreetEnd} role="img" aria-label="Professor Fritts, an elderly gentleman in a navy tailcoat, welcoming you">
      <div className={styles.body}>
        <img className={styles.base} src="/fritts/host/base.webp" alt="" />
        <img className={styles.hand2} src="/fritts/host/hand2.webp" alt="" />
        <img className={styles.hand} src="/fritts/host/hand.webp" alt="" />
        <div className={styles.head}>
          <img src="/fritts/host/head.webp" alt="" />
          <span className={`${styles.lid} ${styles.lidLeft}`} />
          <span className={`${styles.lid} ${styles.lidRight}`} />
        </div>
      </div>
    </div>
  );
}

/** Draws one pose: the layered Gentleman Host, a pose from the animation sheet, the chalkboard film, a picture or GIF, or a looping clip. */
function Figure({ asset, greeting, onGreetEnd, onActEnd, flip }: { asset: PoseAsset; greeting: boolean; onGreetEnd: (e: AnimationEvent) => void; onActEnd: () => void; flip: boolean }) {
  if (asset.kind === "layers") return <LayeredFigure rig={RIGS[asset.rig]} acting={greeting} onActEnd={onActEnd} flip={flip} />;
  if (asset.kind === "board") return <BoardFigure acting={greeting} onActEnd={onActEnd} />;
  if (asset.kind === "image") return <img className={`${styles.flat} ${asset.flip ? styles.flatFlip : ""}`} src={asset.src} alt={asset.alt} />;
  if (asset.kind === "video") {
    return <video className={styles.flat} src={asset.src} poster={asset.poster} aria-label={asset.alt} autoPlay loop muted playsInline />;
  }
  return <Rig greeting={greeting} onGreetEnd={onGreetEnd} />;
}

export function FrittsGuide({ placement, pose, line, actions = [], wide = false, cue }: GuideProps) {
  const [open, setOpen] = useState(true);
  const [shownLine, setShownLine] = useState(line);
  const [shownCue, setShownCue] = useState(cue);
  const [greeting, setGreeting] = useState(cue > 0);

  // A new line opens the bubble again, and a new cue plays the flourish once.
  if (line !== shownLine) {
    setShownLine(line);
    setOpen(true);
  }
  if (cue !== shownCue) {
    setShownCue(cue);
    setGreeting(true);
  }

  const asset = POSES[pose] ?? { kind: "rig" as const };
  // The chalkboard film is the heaviest pose, so it starts loading while he does his earlier scenes.
  useEffect(() => {
    if (placement === "stage") preloadBoardFilm();
  }, [placement]);
  // The flourish belongs to the layered poses only, so a picture or clip never leaves it waiting to play later.
  if (greeting && (asset.kind === "image" || asset.kind === "video")) setGreeting(false);
  // The figure is redrawn (and fades in) only when the picture itself changes, not between two poses that share the same layers.
  const figureKey = asset.kind === "rig" ? "rig" : asset.kind === "layers" ? `layers-${asset.rig}` : asset.kind === "board" ? "board" : asset.src;
  const atEdge = placement === "side" || placement === "form";
  const spot = atEdge ? (SIDE_OF_SCREEN === "right" ? styles.sideRight : styles.sideLeft) : styles[placement];
  const size = placement === "form" ? styles.big : "";
  // The chalkboard reaches above him, so his bubble goes over the board, not beside it.
  const bubbleSpot = asset.kind === "board" ? styles.above : "";
  // Some layered poses ask to stand a little to the right when they are in the middle of the screen.
  const centered = placement === "center" && asset.kind === "layers" ? RIGS[asset.rig] : undefined;
  const nudge = centered?.nudge ?? 0;
  const bubbleUp = centered?.bubbleUp ?? 0;
  const bubbleLeft = centered?.bubbleLeft ?? 100;
  // A still picture can ask to be drawn bigger; the guide grows with it and the bubble is pulled back down so it stays put.
  const grow = asset.kind === "image" ? asset.grow : undefined;
  // At the last step of the form he stands at the right edge gesturing toward the form, so the explaining pose is mirrored to face it.
  const flip = placement === "form" && asset.kind === "layers" && asset.rig === "explain";

  const endGreeting = (e: AnimationEvent) => {
    if (e.animationName.includes("flourish")) setGreeting(false);
  };
  // The sheet's poses time their own action, so they tell the guide when it is over.
  const endAct = useCallback(() => setGreeting(false), []);
  // Clicking him waves again and brings the bubble back.
  const wave = () => {
    setOpen(true);
    setGreeting(false);
    requestAnimationFrame(() => setGreeting(true));
  };

  return (
    // The bubble starts where the artwork ends: the layered Gentleman Host's art fills the middle 80% of its picture, a flat picture or sheet pose fills all of it, and the chalkboard film puts its bubble above the board (see frg-above).
    <div className={`${styles.guide} ${spot} ${size} ${bubbleSpot} ${flip ? styles.flipped : ""} ${grow ? styles.grow : ""}`} style={{ "--grow": grow ?? 1, "--bubble-left": asset.kind === "rig" ? "80%" : `${bubbleLeft}%`, "--nudge": `${nudge}%`, "--bubble-top": `${3 - bubbleUp}%` } as CSSProperties}>
      <button type="button" className={`${styles.figure} ${styles.appear}`} key={figureKey} onClick={wave} aria-label="Wave to Professor Fritts" style={{ background: "none", border: 0, padding: 0 }}>
        <Figure asset={asset} greeting={greeting} onGreetEnd={endGreeting} onActEnd={endAct} flip={flip} />
      </button>
      {open ? (
        <div className={`${styles.bubble} ${wide ? styles.wide : ""}`} role="status" aria-live="polite">
          <button type="button" className={styles.close} onClick={() => setOpen(false)} aria-label="Hide what Professor Fritts said">
            ×
          </button>
          <p className={styles.line}>{line}</p>
          {actions.length > 0 && (
            <div className={styles.actions}>
              {actions.map((a) => (
                <button key={a.label} type="button" className={`${styles.action} ${a.primary ? styles.primary : ""}`} onClick={a.onClick}>
                  {a.label}
                </button>
              ))}
            </div>
          )}
        </div>
      ) : (
        <button type="button" className={styles.reopen} onClick={() => setOpen(true)}>
          Show what Fritts said
        </button>
      )}
    </div>
  );
}
