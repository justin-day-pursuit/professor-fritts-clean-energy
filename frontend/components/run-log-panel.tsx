/**
 * Run log tab — ordered RunEvents from the harness (checks, think, tools, errors).
 * Check rows use orange styling; tool results show mock badge and freshness fields.
 */
"use client";

import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useEffect, useRef } from "react";
import type { RunEventResponse, RunResponse, ToolResultPayload } from "@/lib/types";

export interface RunLogPanelProps {
  runs: RunResponse[];
  selectedRunId: number | null;
  onSelectRun: (runId: number) => void;
}

function isCheckKind(kind: string): boolean {
  return kind.startsWith("check");
}

function CheckBlock({ event }: { event: RunEventResponse }) {
  const passed = event.payload.passed === true;
  const message = String(event.payload.message ?? "");
  const details = event.payload.details as Record<string, unknown> | undefined;
  return (
    <div className="rounded-md border border-orange-300 bg-orange-50 dark:bg-orange-950/40 dark:border-orange-700 p-2 text-sm">
      <div className="flex items-center gap-2 font-medium text-orange-900 dark:text-orange-100">
        <span className="uppercase text-xs">{event.kind}</span>
        <Badge variant="outline" className="text-[0.65rem]">
          {passed ? "pass" : "fail"}
        </Badge>
      </div>
      <p className="mt-1 text-xs">{message}</p>
      {event.kind === "check4" && Array.isArray(details?.issues) ? (
        <ul className="mt-2 list-disc pl-4 text-xs text-destructive">
          {(details.issues as string[]).map((issue) => (
            <li key={issue}>{issue}</li>
          ))}
        </ul>
      ) : null}
      {event.payload.code != null && (
        <p className="text-[0.65rem] text-muted-foreground mt-1">code: {String(event.payload.code)}</p>
      )}
    </div>
  );
}

function ToolCallBlock({ event }: { event: RunEventResponse }) {
  return (
    <div className="rounded-md border p-2 text-sm space-y-1">
      <div className="font-medium text-xs uppercase text-muted-foreground">Tool call</div>
      <div className="font-mono text-xs">{String(event.payload.tool ?? "")}</div>
      <pre className="text-[0.65rem] bg-muted/50 rounded p-2 overflow-x-auto">
        {JSON.stringify(event.payload.input ?? {}, null, 2)}
      </pre>
    </div>
  );
}

function ToolResultBlock({ event }: { event: RunEventResponse }) {
  const p = event.payload as ToolResultPayload;
  return (
    <div className="rounded-md border p-2 text-sm space-y-1">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium text-xs uppercase text-muted-foreground">Tool result</span>
        {p.mock ? (
          <Badge variant="secondary" className="text-[0.65rem]">
            mock
          </Badge>
        ) : null}
        {p.stale ? (
          <Badge variant="destructive" className="text-[0.65rem]">
            stale
          </Badge>
        ) : null}
      </div>
      <div className="text-xs space-y-0.5">
        {p.source_url ? (
          <div>
            <span className="text-muted-foreground">source_url:</span> {p.source_url}
          </div>
        ) : null}
        {p.retrieved_at ? (
          <div>
            <span className="text-muted-foreground">retrieved_at:</span> {p.retrieved_at}
          </div>
        ) : null}
      </div>
      <pre className="text-[0.65rem] bg-muted/50 rounded p-2 overflow-x-auto max-h-40">
        {JSON.stringify(p.data ?? event.payload, null, 2)}
      </pre>
    </div>
  );
}

function EventRow({ event }: { event: RunEventResponse }) {
  if (isCheckKind(event.kind)) return <CheckBlock event={event} />;
  if (event.kind === "think") {
    return (
      <div className="rounded-md border border-dashed p-2 text-sm italic text-muted-foreground">
        <span className="text-xs font-medium not-italic uppercase">Think</span>
        <p className="mt-1">{String(event.payload.message ?? "")}</p>
      </div>
    );
  }
  if (event.kind === "tool_call") return <ToolCallBlock event={event} />;
  if (event.kind === "tool_result") return <ToolResultBlock event={event} />;
  if (event.kind === "error") {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 p-2 text-sm text-destructive">
        <span className="text-xs font-medium uppercase">Error</span>
        <p className="mt-1">{String(event.payload.message ?? JSON.stringify(event.payload))}</p>
      </div>
    );
  }
  return (
    <div className="rounded-md border p-2 text-xs font-mono">
      {event.kind}: {JSON.stringify(event.payload)}
    </div>
  );
}

export function RunLogPanel({ runs, selectedRunId, onSelectRun }: RunLogPanelProps) {
  const run = runs.find((r) => r.id === selectedRunId) ?? runs[runs.length - 1];
  const events = [...(run?.events ?? [])].sort((a, b) => a.seq - b.seq);
  // While a run is still going (a live run, or a saved replay playing back), keep the newest step in view.
  const endRef = useRef<HTMLDivElement | null>(null);
  const running = run?.status === "running";
  useEffect(() => {
    if (running) endRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [running, events.length]);

  return (
    <div className="flex flex-col h-full min-h-0 gap-2">
      {runs.length > 1 && (
        <div className="flex flex-wrap gap-2 text-xs">
          {runs.map((r) => (
            <button
              key={r.id}
              type="button"
              className={`rounded border px-2 py-1 ${
                r.id === run?.id ? "bg-primary text-primary-foreground" : "bg-muted"
              }`}
              onClick={() => onSelectRun(r.id)}
            >
              Run #{r.id} · {r.status}
            </button>
          ))}
        </div>
      )}
      {run ? (
        <p className="text-xs text-muted-foreground">
          Run {run.id} · {run.status} · {run.tool_call_count} tool calls
          {run.elapsed_seconds != null ? ` · ${run.elapsed_seconds.toFixed(1)}s` : ""}
        </p>
      ) : (
        <p className="text-sm text-muted-foreground">No runs yet — send a chat message to start.</p>
      )}
      <ScrollArea className="flex-1 min-h-[280px]">
        <div className="space-y-2 pr-3 pb-4">
          {events.map((ev) => (
            <EventRow key={ev.id} event={ev} />
          ))}
          <div ref={endRef} />
        </div>
      </ScrollArea>
    </div>
  );
}
