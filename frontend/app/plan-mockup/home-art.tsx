/**
 * Small drawings for the home page: one for each "How it works" step, and one icon for each of the four labels in
 * "What makes it different". They are plain line art in the page's own colours (deep blue, teal, gold on cream), with no
 * characters, and they scale with their box. Purely decorative, so they are hidden from screen readers.
 */

const ink = "var(--fr-ink)";
const teal = "var(--fr-teal)";
const gold = "var(--fr-gold)";
const line = "var(--fr-line)";

/** The picture at the top of a "How it works" card: 1 a building with a pin, 2 a solar panel under the sun, 3 a plan with a route. */
export function HowArt({ n }: { n: string }) {
  return (
    <svg viewBox="0 0 160 96" aria-hidden="true" className="block h-auto w-full" fill="none" strokeLinecap="round" strokeLinejoin="round">
      {n === "1" && (
        <g>
          <line x1="18" y1="80" x2="142" y2="80" stroke={line} strokeWidth="2" />
          <circle cx="30" cy="68" r="10" fill={teal} opacity="0.35" />
          <circle cx="40" cy="72" r="7" fill={teal} opacity="0.5" />
          <rect x="52" y="40" width="56" height="40" rx="2" fill="#fff" stroke={ink} strokeWidth="2" />
          <path d="M47 42 L80 21 L113 42 Z" fill={gold} fillOpacity="0.3" stroke={ink} strokeWidth="2" />
          <line x1="62" y1="47" x2="62" y2="80" stroke={teal} strokeWidth="3.5" />
          <line x1="72" y1="47" x2="72" y2="80" stroke={teal} strokeWidth="3.5" />
          <line x1="88" y1="47" x2="88" y2="80" stroke={teal} strokeWidth="3.5" />
          <line x1="98" y1="47" x2="98" y2="80" stroke={teal} strokeWidth="3.5" />
          <rect x="76" y="62" width="8" height="18" rx="1.5" fill={teal} />
          <path d="M126 12a12 12 0 0 1 12 12c0 9-12 23-12 23s-12-14-12-23a12 12 0 0 1 12-12z" fill={gold} stroke={ink} strokeWidth="2" />
          <circle cx="126" cy="24" r="4" fill="#fff" />
        </g>
      )}
      {n === "2" && (
        <g>
          <circle cx="126" cy="26" r="11" fill={gold} stroke={ink} strokeWidth="2" />
          <g stroke={gold} strokeWidth="2.5">
            <line x1="126" y1="8" x2="126" y2="12" />
            <line x1="126" y1="40" x2="126" y2="44" />
            <line x1="108" y1="26" x2="112" y2="26" />
            <line x1="140" y1="26" x2="144" y2="26" />
            <line x1="113" y1="13" x2="116" y2="16" />
            <line x1="136" y1="36" x2="139" y2="39" />
            <line x1="139" y1="13" x2="136" y2="16" />
            <line x1="116" y1="36" x2="113" y2="39" />
          </g>
          <path d="M34 66 L52 36 H100 L82 66 Z" fill={teal} stroke={ink} strokeWidth="2" />
          <g stroke="#fff" strokeWidth="1.5" opacity="0.8">
            <line x1="63" y1="36" x2="45" y2="66" />
            <line x1="76" y1="36" x2="58" y2="66" />
            <line x1="89" y1="36" x2="71" y2="66" />
            <line x1="43" y1="51" x2="91" y2="51" />
          </g>
          <line x1="58" y1="66" x2="54" y2="80" stroke={ink} strokeWidth="2.5" />
          <line x1="76" y1="66" x2="80" y2="80" stroke={ink} strokeWidth="2.5" />
          <line x1="44" y1="80" x2="92" y2="80" stroke={line} strokeWidth="2" />
          <circle cx="118" cy="68" r="11" fill="#fff" stroke={ink} strokeWidth="3" />
          <line x1="126" y1="76" x2="136" y2="86" stroke={ink} strokeWidth="4" />
          <line x1="113" y1="73" x2="113" y2="66" stroke={teal} strokeWidth="3" />
          <line x1="118" y1="73" x2="118" y2="62" stroke={teal} strokeWidth="3" />
          <line x1="123" y1="73" x2="123" y2="69" stroke={teal} strokeWidth="3" />
        </g>
      )}
      {n === "3" && (
        <g>
          <rect x="40" y="10" width="68" height="76" rx="6" fill="#fff" stroke={ink} strokeWidth="2" />
          <rect x="49" y="19" width="30" height="6" rx="3" fill={teal} />
          {[38, 53, 68].map((y) => (
            <g key={y}>
              <circle cx="55" cy={y} r="5.5" fill={teal} fillOpacity="0.18" />
              <polyline points={`52,${y} 54.5,${y + 2.5} 58.5,${y - 3}`} stroke={teal} strokeWidth="2" />
              <rect x="66" y={y - 2.5} width="34" height="5" rx="2.5" fill={line} />
            </g>
          ))}
          <path d="M114 76 Q134 70 130 52" stroke={gold} strokeWidth="2.5" strokeDasharray="4 5" />
          <line x1="130" y1="52" x2="130" y2="28" stroke={ink} strokeWidth="2" />
          <path d="M130 28 L148 34 L130 40 Z" fill={gold} stroke={ink} strokeWidth="2" />
        </g>
      )}
    </svg>
  );
}

/** The icon for one of the four labels (FACT, ESTIMATE, ASSUMPTION, RECOMMENDATION), drawn in that label's own colour. */
export function LabelArt({ name, color }: { name: string; color: string }) {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true" className="h-8 w-8" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      {name === "FACT" && (
        <g>
          <rect x="12" y="8" width="24" height="32" rx="3.5" />
          <polyline points="18,24 22,28 30,19" strokeWidth="3" />
          <line x1="18" y1="34" x2="30" y2="34" opacity="0.5" />
        </g>
      )}
      {name === "ESTIMATE" && (
        <g>
          <line x1="8" y1="32" x2="40" y2="32" opacity="0.3" />
          <line x1="8" y1="27" x2="8" y2="37" />
          <line x1="40" y1="27" x2="40" y2="37" />
          <line x1="16" y1="32" x2="33" y2="32" strokeWidth="6" />
          <circle cx="24.5" cy="19" r="4.5" fill={color} stroke="none" />
          <line x1="24.5" y1="24" x2="24.5" y2="28" />
        </g>
      )}
      {name === "ASSUMPTION" && (
        <g>
          <line x1="9" y1="14" x2="39" y2="14" opacity="0.4" />
          <circle cx="30" cy="14" r="4.5" fill="#fff" />
          <line x1="9" y1="24" x2="39" y2="24" opacity="0.4" />
          <circle cx="17" cy="24" r="4.5" fill="#fff" />
          <line x1="9" y1="34" x2="39" y2="34" opacity="0.4" />
          <circle cx="26" cy="34" r="4.5" fill="#fff" />
        </g>
      )}
      {name === "RECOMMENDATION" && (
        <g>
          <line x1="22" y1="7" x2="22" y2="42" />
          <polygon points="22,11 37,11 41,16 37,21 22,21" fill={color} fillOpacity="0.2" />
          <polygon points="22,25 11,25 7,30 11,35 22,35" fill={color} fillOpacity="0.2" />
        </g>
      )}
    </svg>
  );
}
