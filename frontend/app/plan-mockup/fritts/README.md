# Professor Fritts guide

Professor Fritts stays on screen through the whole visit on the home page (`/`). He greets in the middle, steps to the side while you fill in the form, stands at the left while the work runs, announces the report in the middle, then steps to the side again.

## Files

| File | What it does |
| --- | --- |
| `FrittsGuide.tsx` | The character, where he stands, and his speech bubble with buttons |
| `poses.ts` | Which picture, layered pose, GIF or video shows each pose, which pose fits each working step, and which edge he stands at |
| `rigs.ts`, `LayeredFigure.tsx` | The layered poses and the chalkboard film from the animation sheet |
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
| `welcome` | The greeting | Greeting (waves) |
| `explaining` | What to bring, the last form step, explaining a section | Explaining (marks points) |
| `listening` | The form | Layered Gentleman Host |
| `reassuring` | "I don't know" and "not sure yet" answers | Layered Gentleman Host |
| `delighted` | After "I have everything" | Hello (offers a hand in welcome) |
| `thinking` | While the city's records are looked up | Researching (magnifying glass) |
| `reading` | Working list: city records, incentives and rules | Reading a book |
| `researching` | Working list: building details, solar, flood and heat, electricity prices and tariff | Researching (magnifying glass) |
| `calculating` | Working list: the numbers, costing, sizing the battery | Chalkboard film |
| `analyze` | Working list: costing and checking sources | Writing on a clipboard (slow pen) |
| `writing` | Working list: the last step, "writing your plan" | The same clipboard with his pen going fast, nodding, and the check mark drawing itself (the state he has when clicked) |
| `present` | Report ready (the "I have your report" moment, center) | Taps the chart on the report (animated) |
| `studying` | Opening scene of the working list (reading the building details) | Still picture: thinking over his clipboard, hand on chin |
| `presenting` | Beside the finished report (his menu) | Still picture: presenting the report with an open hand |

While the plan is worked out he plays six scenes in a fixed order: thinking over the clipboard (still picture), researching, reading, chalkboard, taking notes, then writing the plan (pen going fast). `runPlan.ts` sorts the working-list steps into those scenes (so the list can read in a slightly different order than the tools were used) and spreads them evenly across each scene. Each scene lasts one full pass of its animation (about 3 s, 6 s, 6 s, 4.8 s, 6 s and 3 s), so nothing is cut off, and the list and progress bar fill at that pace (about 29 s in all). `poseForStep` in `poses.ts` decides which scene a step belongs to. To change a scene's length, edit `SCENES` in `runPlan.ts`. Clicking him (or the cue on the greeting and the finished report) plays that pose's short action: a big wave, a flourish, tapping the chart, a check mark, and so on.

## Layered poses from the animation sheet

Each is a body picture with cut-out pieces on top. `rigs.ts` lists the pieces of each pose and where they sit; `LayeredFigure.tsx` draws them; `fritts.css` (the `frg-p-<pose>` rules) moves them. The pictures are in `frontend/public/fritts/rigs/`, and the chalkboard film is one animated picture, `rigs/board.webp` (115 pictures at 24 per second; it plays once and stops on the finished board), plus a still of the finished board, `rigs/board-still.webp`, shown when someone asks for reduced motion. To add one, copy its pieces into `rigs/`, add an entry to `RIGS` in `rigs.ts`, add its movement to `fritts.css`, and point a pose at it in `POSES` (`{ kind: "layers", rig: "<id>" }`). With reduced motion the poses stand still and the chalkboard shows its finished board.

## Where he stands

`center` is large and in the middle (greeting, report ready). `stage` is large at the left, beside the working list. `side` is small at the edge (form and report). Change `SIDE_OF_SCREEN` in `poses.ts` to put the `side` spot on the left.

## Layered character

The Gentleman Host is made of separate pictures in `frontend/public/fritts/host/`: the body, the head, and two hands. CSS moves them (breathing, head sway, blinking, a gesturing hand, and a welcome flourish when he greets or is clicked). Adding another layered pose means supplying the same four pieces for it.
