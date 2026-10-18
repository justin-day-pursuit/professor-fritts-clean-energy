/* eslint-disable @next/next/no-img-element -- the pieces are small, already-compressed pictures placed by percentage, which next/image cannot do. */
/**
 * Draws the layered poses from the animation sheet: a body picture with cut-out pieces on top (hands, a pen, a book, the
 * head with blinking eyelids), plus the chalkboard film. Which pieces each pose has comes from ./rigs.ts, and how they
 * move comes from fritts.css (each pose has a class named "frg-p-<id>").
 *
 * Both figures take an "acting" flag. While it is true the pose plays its short action (a big wave, a flourish, tapping
 * the chart) and then calls onActEnd, so the guide can ask for the action again later.
 */
"use client";

import { useEffect, useRef, type CSSProperties } from "react";
import { BOARD, type Layer, type Rig } from "./rigs";

/** Turns a placed rectangle into inline style, with every number as a percentage of the pose's picture. */
function place(box: { left: number; top: number; width: number; height?: number }): CSSProperties {
  return {
    left: `${box.left}%`,
    top: `${box.top}%`,
    width: `${box.width}%`,
    ...(box.height === undefined ? {} : { height: `${box.height}%` }),
  };
}

/** One piece of a pose, drawn according to its kind. */
function LayerView({ layer }: { layer: Layer }) {
  switch (layer.kind) {
    case "part":
      return <img className={`frg-lr-part frg-lr-${layer.name}`} src={layer.src} alt="" style={{ ...place(layer.box), transformOrigin: layer.origin }} />;
    case "head":
      return (
        <div className="frg-lr-head" style={{ ...place(layer.box), transformOrigin: layer.origin }}>
          <img src={layer.src} alt="" />
          {layer.lids.map((lid, i) => (
            <span key={i} className="frg-lr-lid" style={place(lid)} />
          ))}
        </div>
      );
    case "ring":
      return <span className="frg-lr-ring" style={place(layer.box)} />;
    case "check":
      return (
        <svg className="frg-lr-check" viewBox="0 0 60 44" style={place(layer.box)} aria-hidden="true">
          <path d="M6 24 L22 38 L54 6" fill="none" stroke="#e9b21c" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" pathLength="1" />
        </svg>
      );
    case "glass":
      return (
        <div className="frg-lr-glass" style={{ ...place(layer.box), transformOrigin: layer.origin }}>
          <img src={layer.src} alt="" />
          <span className="frg-lr-glint" style={place(layer.glint)} />
        </div>
      );
  }
}

/** The pose's feet sink a little below the picture's edge so they land on the floor line: a share of its own height. A lift raises him again, and a shift moves him sideways. */
function sink(gap: number, lift = 0, flip = false, shift = 0): CSSProperties {
  return { transform: `translate(${shift}%, ${((gap - lift) * 100).toFixed(3)}%)${flip ? " scaleX(-1)" : ""}` };
}

/** The chalkboard film, fetched once and kept in memory so it can start the moment its scene begins and be replayed without downloading it again. */
let boardFilm: Promise<Blob> | null = null;

/** Starts loading the chalkboard film (only the first call does anything). The guide calls this a scene early. */
export function preloadBoardFilm(): Promise<Blob> {
  boardFilm ??= fetch(BOARD.film).then((response) => {
    if (!response.ok) throw new Error(`The chalkboard film did not load (${response.status})`);
    return response.blob();
  });
  boardFilm.catch(() => {
    boardFilm = null;
  });
  return boardFilm;
}

interface FigureProps {
  /** True while the pose should play its short action. */
  acting: boolean;
  /** Called when that action is over. */
  onActEnd: () => void;
}

/** A layered pose: body, moving pieces, head and blinking eyes. */
export function LayeredFigure({ rig, acting, onActEnd, flip = false }: FigureProps & { rig: Rig; flip?: boolean }) {
  // The action lasts a fixed time, so the guide hears about its end after that time (a little extra lets the last frame finish).
  useEffect(() => {
    if (!acting) return;
    const timer = setTimeout(onActEnd, rig.dur + 400);
    return () => clearTimeout(timer);
  }, [acting, rig.dur, onActEnd]);

  return (
    <div
      className={`frg-lr frg-p-${rig.id} ${acting ? "frg-act" : ""}`}
      style={
        {
          aspectRatio: String(rig.w * rig.k),
          "--lid": rig.lid,
          // A larger pose is drawn taller than the guide and pulled back up so its feet stay on the floor line.
          ...(rig.scale ? { height: `${rig.scale * 100}%`, top: `${(1 - rig.scale) * 100}%` } : {}),
          ...sink(rig.gap * rig.k, rig.lift, flip, rig.shift)
        } as CSSProperties
      }
      role="img"
      aria-label={rig.alt}
    >
      <div className="frg-lr-body" style={{ transformOrigin: `50% ${rig.floor}%` }}>
        <img className="frg-lr-base" src={rig.base} alt="" />
        {rig.layers.map((layer, i) => (
          <LayerView key={i} layer={layer} />
        ))}
      </div>
    </div>
  );
}

/**
 * The chalkboard pose: one animated picture that plays once and stops on the finished board. He holds that for a moment, the
 * picture fades out, and it starts over. Being asked to act (clicked) plays it again from the start. With reduced motion (or if
 * the film cannot be loaded) it shows the finished board only.
 */
export function BoardFigure({ acting, onActEnd }: FigureProps) {
  const picture = useRef<HTMLImageElement>(null);
  const restart = useRef<() => void>(() => {});

  useEffect(() => {
    const el = picture.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.src = BOARD.still;
      return;
    }

    let alive = true;
    let film: Blob | null = null;
    let address: string | null = null;
    let timer: ReturnType<typeof setTimeout> | undefined;

    // Giving the picture a fresh address makes its animation start again from the first frame.
    const play = () => {
      if (!film) return;
      clearTimeout(timer);
      if (address) URL.revokeObjectURL(address);
      address = URL.createObjectURL(film);
      el.classList.remove("frg-fade");
      el.src = address;
      // Once it has played and held on the finished board, fade it out and begin again.
      timer = setTimeout(() => {
        el.classList.add("frg-fade");
        timer = setTimeout(play, BOARD.fadeMs);
      }, BOARD.filmMs + BOARD.holdMs);
    };
    restart.current = play;

    preloadBoardFilm()
      .then((blob) => {
        if (!alive) return;
        film = blob;
        play();
      })
      .catch(() => {
        if (alive) el.src = BOARD.still;
      });

    return () => {
      alive = false;
      clearTimeout(timer);
      if (address) URL.revokeObjectURL(address);
      restart.current = () => {};
    };
  }, []);

  // Being asked to act plays the film again; it has no separate action, so the request is finished at once.
  useEffect(() => {
    if (!acting) return;
    restart.current();
    onActEnd();
  }, [acting, onActEnd]);

  return (
    <img
      ref={picture}
      className="frg-lr-film"
      alt=""
      aria-label={BOARD.alt}
      role="img"
      style={{ aspectRatio: `${BOARD.width} / ${BOARD.height}`, height: `${BOARD.scale * 100}%`, top: `${(1 - BOARD.scale) * 100}%`, ...sink(BOARD.gap) }}
    />
  );
}
