import { shortLink } from "../plan-actions";

/**
 * What Professor Fritts says. Every line here is written ahead of time, so the guide costs nothing to run and never
 * says anything unexpected. The plan itself still comes from the real agent; these lines only walk the visitor through.
 */

/** The first thing he says, centered on screen. */
export const HELLO = "Hello, I'm Professor Fritts. I can work out what you can save, generate, and what it would cost.";

/** The list of what to have ready. */
export const BRING =
  "Before we start, it helps to have a few things ready: the building's address, a rough budget, your goal, and a recent electric bill if you have one.";

/** His reply to each answer about what the visitor has ready. */
export const BRING_REPLY = {
  all: "Wonderful. Then we can go straight through.",
  some: "That's fine. I'll ask for what's missing as we go.",
  unsure: "No problem. Where I have to, I'll use stand-in numbers, and the plan will say so plainly.",
} as const;

/** His reply to each answer about whether the building details he found are right. */
export const CONFIRM_REPLY = {
  yes: "Thank you. Now your energy use and goals.",
  edit: "Go ahead and change anything in the boxes, then press Continue.",
  unsure: "That's fine. I'll leave it blank, and the plan will say what it assumed. Press Continue when you're ready.",
} as const;

/** What he says at the energy and building steps when the city's records filled something in for the visitor to check. */
export const PREFILL_STEP: Record<number, string> = {
  2: "I've filled in what the city's records show about your electricity use. Please check it against a recent bill.",
  3: "I've added the city's own roof assessment below. A roofer should confirm it before any design.",
};

/** What he says when the visitor asks to share a plan from their own run: links only work for the saved sample plans for now. */
export const SHARE_LIVE = "Links work for the sample plans for now. To share your own plan, download the PDF and send that.";

/** What he says at each step of the form. Step 1 depends on the building, so it is built in the page. */
export const INTAKE_STEP: Record<number, string> = {
  2: "Now your energy and goals. If you have a recent Con Edison bill, you can attach it below.",
  3: "Next, what the building already has, so the plan builds on it. Write none if there's nothing to list.",
  4: "I have everything I need. When you press Run, I'll start work.",
};

/** Turns a step of the working list into something he says out loud, like "I'm checking the city's records." */
export function workingLine(step: string): string {
  const lower = step.charAt(0).toLowerCase() + step.slice(1);
  return `I'm ${lower}.`;
}

/** What he says when the report is ready, using the plan's own short answer. */
export function readyLine(outcomeLabel: string): string {
  return `I have your report. The short answer: ${outcomeLabel.charAt(0).toLowerCase() + outcomeLabel.slice(1)}.`;
}

/** The question he asks beside the finished report. */
export const REPORT_MENU = "Would you like to download this, share it, or have a section explained?";

/** What he says while the PDF is made, and how it ended. */
export const PDF_SAYS = {
  making: "One moment, I'm putting your report into a PDF.",
  done: "Your PDF is ready. Check your downloads.",
  unreachable: "I couldn't reach the planner to make the PDF just now. You can print this page from your browser instead.",
  failed: "The PDF didn't come out right this time. You can print this page from your browser instead.",
} as const;

/** What he says after copying the share link. */
export function shareLine(url: string, copied: boolean): string {
  return `${copied ? "Link copied." : "Here is the link."} ${shortLink(url)}`;
}

// ---------------------------------------------------------------------------------- the address step

/** Before anything is typed. */
export const ADDRESS_START = "Start typing your building's address and pick it from the list. I only cover New York City.";

/** While the city's records are being read. */
export const ADDRESS_LOOKING = "Let me look that up in the city's records.";

/** When the address search finds nothing, which is also how an address outside New York City shows up. */
export const ADDRESS_NOT_FOUND =
  "I couldn't find that in New York City. I only cover the five boroughs, so check the street and borough, or try a sample building.";

/** When the city's address service cannot be reached. */
export const ADDRESS_ERROR = "I couldn't reach the city's records just now. Please try again in a moment, or try a sample building.";

/** A public building was found: read it back and ask the visitor to confirm. */
export function foundLine(label: string, ownerName?: string): string {
  const owner = ownerName ? ` The city lists the owner as ${ownerName}.` : "";
  return `Found it: ${label}.${owner} This is what the records say about the building. Is that right?`;
}

/** The lot looks private: say what this planner is for, and let the visitor decide. */
export const PRIVATE_BUILDING =
  "This looks like a privately owned building. I'm built for New York City's public buildings, such as schools, libraries and city offices, so some incentives and rules may not fit. Would you like to go on anyway?";

/** The owner on the record does not settle whether the building is public. */
export function unclearOwner(ownerName?: string): string {
  return ownerName
    ? `The city lists this lot as owned by ${ownerName}, and I can't tell from that whether it's a public building. Is it?`
    : "The city's record doesn't say who owns this lot, so I can't tell whether it's a public building. Is it?";
}
