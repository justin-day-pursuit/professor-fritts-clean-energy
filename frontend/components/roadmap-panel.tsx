/**
 * Roadmap tab — Markdown view, labeled claims, mandatory referrals, and file downloads.
 * Uses run.output from the API; section 10 referrals stay visible even when scrolling.
 */
"use client";

import { Button } from "@/components/ui/button";
import { LabelBadge } from "@/components/label-badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { downloadRoadmapJson, downloadRoadmapMarkdown } from "@/lib/api";
import type { Claim, RoadmapPayload, RunResponse } from "@/lib/types";
import ReactMarkdown from "react-markdown";
import { useMemo, useState } from "react";

function parseRoadmap(run: RunResponse | null): RoadmapPayload | null {
  if (!run?.output?.roadmap) return null;
  return run.output.roadmap as RoadmapPayload;
}

function allClaims(payload: RoadmapPayload | null): Claim[] {
  if (!payload?.sections) return [];
  return payload.sections.flatMap((s) => s.claims ?? []);
}

function referralSection(payload: RoadmapPayload | null) {
  return payload?.sections?.find((s) => s.section_id === "10" || /professional|referral|permit/i.test(s.title));
}

export interface RoadmapPanelProps {
  run: RunResponse | null;
}

export function RoadmapPanel({ run }: RoadmapPanelProps) {
  const payload = useMemo(() => parseRoadmap(run), [run]);
  const markdown = run?.output?.markdown ? String(run.output.markdown) : "";
  const referrals = referralSection(payload);
  const [downloadBusy, setDownloadBusy] = useState(false);

  const download = async (kind: "md" | "json") => {
    if (!run) return;
    setDownloadBusy(true);
    try {
      const text =
        kind === "md" ? await downloadRoadmapMarkdown(run.id) : await downloadRoadmapJson(run.id);
      const blob = new Blob([text], {
        type: kind === "md" ? "text/markdown" : "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = kind === "md" ? "roadmap.md" : "roadmap.json";
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloadBusy(false);
    }
  };

  if (!run) {
    return <p className="text-sm text-muted-foreground">Roadmap appears after a successful planning run.</p>;
  }

  const finalTool = run.output?.final_tool ? String(run.output.final_tool) : "write_roadmap";

  return (
    <div className="flex flex-col gap-3 min-h-0 h-full">
      <div className="flex flex-wrap gap-2 shrink-0">
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={downloadBusy || !markdown}
          onClick={() => void download("md")}
        >
          Download roadmap.md
        </Button>
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={downloadBusy || !payload}
          onClick={() => void download("json")}
        >
          Download roadmap.json
        </Button>
        <span className="text-xs text-muted-foreground self-center">
          Final tool: {finalTool} · status {run.status}
        </span>
      </div>

      {referrals && referrals.claims.length > 0 && (
        <div className="rounded-md border-2 border-violet-300 bg-violet-50/80 dark:bg-violet-950/30 p-3 shrink-0">
          <h3 className="text-sm font-semibold mb-2">Required professional reviews (always visible)</h3>
          <ul className="space-y-2">
            {referrals.claims.map((claim, i) => (
              <li key={`ref-${i}`} className="text-sm space-y-1">
                <LabelBadge label={claim.label} confidence={claim.confidence} />
                <p>{claim.text}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      <ScrollArea className="flex-1 min-h-[240px] rounded-md border p-3">
        {markdown ? (
          <article className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown>{markdown}</ReactMarkdown>
          </article>
        ) : (
          <p className="text-sm text-muted-foreground">No markdown on this run yet.</p>
        )}
      </ScrollArea>

      {allClaims(payload).length > 0 && (
        <div className="shrink-0 border-t pt-2">
          <h3 className="text-xs font-semibold uppercase text-muted-foreground mb-2">Labeled claims</h3>
          <ul className="max-h-36 overflow-y-auto space-y-2 text-xs">
            {allClaims(payload).map((claim, i) => (
              <li key={`claim-${i}`} className="flex flex-col gap-1">
                <LabelBadge label={claim.label} confidence={claim.confidence} />
                <span>{claim.text}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
