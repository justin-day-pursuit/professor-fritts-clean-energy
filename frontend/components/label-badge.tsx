/**
 * Small colored tag for roadmap claims — FACT, ESTIMATE, ASSUMPTION, or RECOMMENDATION.
 * Confidence (high/medium/low) appears beside the label so readers know how sure Fritts is.
 */
import { Badge } from "@/components/ui/badge";
import type { ClaimConfidence, ClaimLabel } from "@/lib/types";
import { cn } from "@/lib/utils";

const LABEL_STYLES: Record<ClaimLabel, string> = {
  FACT: "bg-emerald-100 text-emerald-900 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-100",
  ESTIMATE:
    "bg-sky-100 text-sky-900 border-sky-300 dark:bg-sky-950 dark:text-sky-100",
  ASSUMPTION:
    "bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-950 dark:text-amber-100",
  RECOMMENDATION:
    "bg-violet-100 text-violet-900 border-violet-300 dark:bg-violet-950 dark:text-violet-100",
};

export function LabelBadge({
  label,
  confidence,
  className,
}: {
  label: ClaimLabel;
  confidence: ClaimConfidence;
  className?: string;
}) {
  return (
    <Badge
      variant="outline"
      className={cn("font-mono text-[0.65rem] uppercase tracking-wide", LABEL_STYLES[label], className)}
    >
      {label} · {confidence}
    </Badge>
  );
}
