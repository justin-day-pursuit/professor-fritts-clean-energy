# Professor Fritts guide

Professor Fritts stays on screen through the whole visit on the design page (`/plan-mockup`). He greets in the middle, steps to the side while you fill in the form, stands at the left while the work runs, announces the report in the middle, then steps to the side again.

## Files

| File | What it does |
| --- | --- |
| `FrittsGuide.tsx` | The character, where he stands, and his speech bubble with buttons |
| `poses.ts` | Which picture, GIF or video shows each pose, and which edge he stands at |
| `script.ts` | Everything he says. All of it is written ahead of time, so the guide uses no API and no credits |
| `fritts.css` | His position, the animation of the layered character, and the bubble |
| `../page.tsx` | Decides, for each screen, where he stands, which pose he takes, what he says and which buttons he offers |

## Adding a new pose (picture, GIF or video)

1. Put the file in `frontend/public/fritts/poses/`.
2. Open `poses.ts` and change that pose's entry, for example:
   - a picture or GIF: `analyze: { kind: "image", src: "/fritts/poses/my-analyze.png", alt: "Professor Fritts studying a clipboard" }`
   - a clip: `thinking: { kind: "video", src: "/fritts/poses/thinking.webm", alt: "Professor Fritts thinking" }`
3. That is all. A pose left as `{ kind: "rig" }` shows the layered Gentleman Host.

Tips for a good swap:
- Use a see-through background (PNG, WebP or GIF). A WebM clip with transparency works best for video; an MP4 has a solid background.
- Frame the whole figure the same way as the other poses, standing on the bottom edge, so he does not jump when the pose changes.
- Around 1000 pixels tall or more looks sharp when he is big.

## Poses and where the script uses them

| Pose | Used when | Now shows |
| --- | --- | --- |
| `welcome` | The greeting | Layered Gentleman Host |
| `explaining` | What to bring, the last form step, explaining a section | Layered Gentleman Host |
| `listening` | The form | Layered Gentleman Host |
| `reassuring` | "I don't know" and "not sure yet" answers | Layered Gentleman Host |
| `delighted` | After "I have everything" | Layered Gentleman Host |
| `thinking` | Not used yet | Layered Gentleman Host |
| `analyze` | While the plan is being worked out | Placeholder cut from the character sheet |
| `present` | Report ready, and beside the report | Placeholder cut from the character sheet |

## Where he stands

`center` is large and in the middle (greeting, report ready). `stage` is large at the left, beside the working list. `side` is small at the edge (form and report). Change `SIDE_OF_SCREEN` in `poses.ts` to put the `side` spot on the left.

## Layered character

The Gentleman Host is made of separate pictures in `frontend/public/fritts/host/`: the body, the head, and two hands. CSS moves them (breathing, head sway, blinking, a gesturing hand, and a welcome flourish when he greets or is clicked). Adding another layered pose means supplying the same four pieces for it.
