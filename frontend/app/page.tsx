/**
 * Landing page at /.
 * Lists mock situations, runs the one you pick, and shows the agent trace.
 * The full intake form lives at /planner. This page does not choose Claude;
 * GET /api/health reports whether the server will call Claude or replay the script.
 */
"use client";

import { useEffect, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { RunLogPanel } from "@/components/run-log-panel";
import { ApiError, getHealth, listFixtures, runFixture } from "@/lib/api";
import type { FixtureSummary, HealthResponse, RunResponse } from "@/lib/types";

/**
 * Turns an API or network failure into one sentence for the red alert.
 */
function errorText(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

/**
 * Downloads the run JSON in the browser. The filename includes the case and
 * run id so two saves do not overwrite each other.
 */
function saveTrace(caseId: string, run: RunResponse) {
  const body = {
    case: caseId,
    status: run.status,
    events: run.events,
    output: run.output,
  };
  const blob = new Blob([JSON.stringify(body, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `trace-${caseId}-run-${run.id}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

/**
 * Short label for the health badge. anthropic means a live Claude call;
 * scripted means the saved transcript. Anything else is shown as-is.
 */
function providerLabel(provider: string): string {
  if (provider === "anthropic") return "Live Claude";
  if (provider === "scripted") return "Scripted transcript (not Claude)";
  return provider;
}

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [fixtures, setFixtures] = useState<FixtureSummary[]>([]);
  const [caseId, setCaseId] = useState<string | null>(null);
  const [run, setRun] = useState<RunResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    /**
     * Loads the server mode and the fixture cards together. A health failure
     * still leaves the page usable if the fixture list comes back.
     */
    async function load() {
      try {
        const [healthBody, fixtureBody] = await Promise.all([getHealth(), listFixtures()]);
        if (cancelled) return;
        setHealth(healthBody);
        setFixtures(fixtureBody.fixtures);
      } catch (err) {
        if (!cancelled) setError(errorText(err));
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  /**
   * Starts the selected situation and swaps the card list for the trace.
   * The run can take a while when the server is calling Claude.
   */
  async function startCase(fixture: FixtureSummary) {
    setBusy(true);
    setError(null);
    setCaseId(fixture.id);
    try {
      const result = await runFixture(fixture.id);
      setRun(result.run);
    } catch (err) {
      setError(errorText(err));
      setCaseId(null);
    } finally {
      setBusy(false);
    }
  }

  const ended = run != null && run.status !== "running";
  const finalEvent = run?.events.find((event) => event.kind === "final");

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="border-b px-4 py-3 flex items-center gap-3 shrink-0">
        {/* Plain img and anchor avoid a Next image/link hydration mismatch on this dev page. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/fritts-logo.png" alt="Professor Fritts" width={40} height={40} className="rounded" />
        <div className="flex-1">
          <h1 className="text-lg font-semibold leading-tight">Professor Fritts</h1>
          <p className="text-sm text-muted-foreground">building renewable energy planner</p>
        </div>
        <a href="/planner" className="text-sm underline text-muted-foreground">
          Full planner
        </a>
      </header>

      <main className="flex-1 p-4 max-w-4xl w-full mx-auto flex flex-col gap-4">
        {health ? (
          <div className="flex flex-wrap gap-2 text-sm">
            <Badge variant="outline">{providerLabel(health.llm_provider)}</Badge>
            <Badge variant="secondary">Tools: {health.tool_mode}</Badge>
          </div>
        ) : null}

        {health?.llm_provider === "scripted" ? (
          <p className="text-sm text-muted-foreground">
            This run replays the saved script. Set LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY in
            the root .env, then restart the backend, for a live Claude call. Tools stay on mock data.
          </p>
        ) : null}

        {error ? (
          <Alert variant="destructive">
            <AlertTitle>Something went wrong</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        {run && caseId ? (
          <div className="flex flex-col gap-3 min-h-[70vh]">
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setRun(null);
                  setCaseId(null);
                }}
              >
                Back to situations
              </Button>
              <Button onClick={() => saveTrace(caseId, run)}>Save trace</Button>
            </div>
            <RunLogPanel runs={[run]} selectedRunId={run.id} onSelectRun={() => undefined} />
            {ended ? (
              <div className="rounded-md border p-3 text-sm">
                <p className="font-medium">Thought ended</p>
                <p className="text-muted-foreground">
                  Status: {run.status}
                  {finalEvent ? " · the model finished its thought" : ""}
                  {run.tool_call_count != null ? ` · ${run.tool_call_count} tool calls` : ""}
                </p>
              </div>
            ) : null}
          </div>
        ) : (
          <div className="grid gap-3">
            {fixtures.length === 0 && !error ? (
              <p className="text-sm text-muted-foreground">Loading situations…</p>
            ) : null}
            {fixtures.map((fixture) => (
              <Card key={fixture.id}>
                <CardHeader>
                  <CardTitle>{fixture.building_name}</CardTitle>
                  <CardDescription>{fixture.goal}</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col gap-3">
                  <p className="text-sm">{fixture.question}</p>
                  <Button disabled={busy} onClick={() => void startCase(fixture)}>
                    {busy && caseId === fixture.id ? "Running…" : "Run this situation"}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {busy && !run ? (
          <p className="text-sm text-muted-foreground">Running the situation. This can take a minute.</p>
        ) : null}
      </main>
    </div>
  );
}
