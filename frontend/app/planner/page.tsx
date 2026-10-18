/**
 * Full planner at /planner — intake, chat, and run/roadmap panels.
 * The landing page at / is the short path that runs a mock situation and shows the trace.
 * This screen still talks to the harness through frontend/lib/api.ts.
 */
"use client";

import Image from "next/image";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChatPanel, type ChatMessage } from "@/components/chat-panel";
import { DocumentUpload } from "@/components/document-upload";
import { IntakeForm } from "@/components/intake-form";
import { RoadmapPanel } from "@/components/roadmap-panel";
import { RunLogPanel } from "@/components/run-log-panel";
import {
  ApiError,
  createSession,
  getSession,
  listReplayCases,
  postMessage,
  replayCase,
  updateProfile,
  uploadDocument,
} from "@/lib/api";
import { DANA_DEFAULT_QUESTION, DANA_INTAKE } from "@/lib/dana-intake";
import { apiToProfile, emptyProfile, missingRequiredFields, profileToApi } from "@/lib/profile-utils";
import { playbackDelays } from "@/lib/replay-playback";
import type { Claim, DocumentResponse, IntakeProfile, ReplayCase, RunResponse } from "@/lib/types";
import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Prefix for bubbles that exist only in the browser (optimistic user lines and
 * needs_input questions). Database Message.id is a positive integer, so a
 * "local:" string can never equal it. ChatPanel keys rows on msg.id — if this
 * counter ever went 1, 2, 3 it would collide with server ids on the next turn.
 * If the backend starts using string ids, keep a prefix that cannot match them.
 */
const CLIENT_MESSAGE_PREFIX = "local:";
let localMessageSeq = 1;

function nextClientMessageId(): string {
  return `${CLIENT_MESSAGE_PREFIX}${localMessageSeq++}`;
}

/**
 * Pulls FACT/ESTIMATE/ASSUMPTION/RECOMMENDATION chips out of a finished run's
 * roadmap JSON so the assistant chat bubble can show them under the reply.
 * Same nested shape RoadmapPanel reads. If the backend moves claims off
 * output.roadmap.sections, update this flatten (and the roadmap panel).
 */
function claimsFromRun(run: RunResponse): Claim[] {
  const roadmap = run.output?.roadmap as { sections?: { claims?: Claim[] }[] } | undefined;
  if (!roadmap?.sections) return [];
  return roadmap.sections.flatMap((s) => s.claims ?? []);
}

export default function PlannerPage() {
  const [profile, setProfile] = useState<IntakeProfile>(emptyProfile());
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [runs, setRuns] = useState<RunResponse[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatDraft, setChatDraft] = useState(DANA_DEFAULT_QUESTION);

  // Saved-demo replay: the menu, what is on screen, and the switches that let playback be skipped or cancelled.
  // A replay never calls Claude; the server plays a saved run back and this page shows it step by step.
  const [replayCases, setReplayCases] = useState<ReplayCase[]>([]);
  const [replayMode, setReplayMode] = useState<{ label: string; kind: string } | null>(null);
  const [playing, setPlaying] = useState(false);
  const playToken = useRef(0); // each replay or reset gets a new number; a playback that no longer matches stops
  const skipRef = useRef(false); // set by "Skip to result" to jump to the finished run

  useEffect(() => {
    let cancelled = false;
    listReplayCases()
      .then((result) => {
        if (!cancelled) setReplayCases(result.cases);
      })
      .catch(() => {
        /* The menu just stays hidden if the server has no replay endpoint (an older backend). */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const showError = useCallback((err: unknown) => {
    const msg = err instanceof ApiError ? err.message : err instanceof Error ? err.message : String(err);
    setError(msg);
  }, []);

  /**
   * Creates a planning session on first use so upload and send have a UUID, then
   * reuses that id from React state. If the default mock fixture changes, update
   * the fixture_case argument here (Load Dana uses the same case name).
   */
  const ensureSession = useCallback(async (): Promise<string> => {
    if (sessionId) return sessionId;
    const created = await createSession({ fixture_case: "case1_queens_library" });
    setSessionId(created.id);
    return created.id;
  }, [sessionId]);

  /**
   * Replaces the current session with Dana's Queens library example so a reviewer
   * can skip typing intake. Resets documents, chat, and runs because they belong
   * to the old session. If Dana's fields change, edit DANA_INTAKE — not this handler.
   */
  const loadDana = async () => {
    // Leaving a replay: stop any playback and clear the replay banner first.
    playToken.current++;
    skipRef.current = true;
    setReplayMode(null);
    setPlaying(false);
    setBusy(true);
    setError(null);
    try {
      const created = await createSession({ fixture_case: "case1_queens_library" });
      await updateProfile(created.id, { profile: profileToApi(DANA_INTAKE) });
      const fresh = await getSession(created.id);
      setSessionId(fresh.id);
      setProfile(apiToProfile(fresh.profile as Record<string, unknown>));
      setDocuments([]);
      setMessages([]);
      setRuns([]);
      setSelectedRunId(null);
      setChatDraft(DANA_DEFAULT_QUESTION);
    } catch (err) {
      showError(err);
    } finally {
      setBusy(false);
    }
  };

  /**
   * Saves the current intake, then posts the chosen file to this session's
   * documents endpoint and appends the returned record to the upload list.
   * If uploads should skip saving the form first, remove the updateProfile call.
   */
  const handleUpload = async (file: File) => {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await updateProfile(sid, { profile: profileToApi(profile) });
      const doc = await uploadDocument(sid, file);
      setDocuments((prev) => [...prev, doc]);
    } catch (err) {
      showError(err);
    } finally {
      setBusy(false);
    }
  };

  /**
   * Puts a run into the right-hand log, replacing an older copy of the same id,
   * and selects it so the roadmap tab follows. If runs should stack as duplicates
   * instead of replacing, drop the filter on r.id.
   */
  const appendRun = (run: RunResponse) => {
    setRuns((prev) => {
      const without = prev.filter((r) => r.id !== run.id);
      return [...without, run];
    });
    setSelectedRunId(run.id);
  };

  /**
   * Saves intake, shows an optimistic user bubble, then posts the chat line.
   * On failure, drops that bubble so ChatPanel can restore the draft (it rethrows).
   * Client-only ids use nextClientMessageId so they never match database Message.id.
   * If the API starts returning the user message in result.message, stop appending
   * a local user bubble and only render the server copy.
   */
  const handleSend = async (text: string) => {
    // While a saved replay is on screen the chat is off: a new message would start a real (paid) run.
    if (replayMode) return;
    setBusy(true);
    setError(null);
    let optimisticId: string | null = null;
    try {
      const sid = await ensureSession();
      await updateProfile(sid, { profile: profileToApi(profile) });
      const userLocal: ChatMessage = {
        id: nextClientMessageId(),
        session_id: sid,
        role: "user",
        content: text,
        created_at: new Date().toISOString(),
        run_id: null,
      };
      optimisticId = String(userLocal.id);
      setMessages((prev) => [...prev, userLocal]);

      const result = await postMessage(sid, { content: text });
      appendRun(result.run);

      if (result.message) {
        const claims = claimsFromRun(result.run);
        setMessages((prev) => [
          ...prev,
          {
            ...result.message!,
            claims: claims.length ? claims : undefined,
          },
        ]);
      } else if (result.run.status === "needs_input") {
        const question = String(result.run.output?.question ?? "More intake details needed.");
        setMessages((prev) => [
          ...prev,
          {
            id: nextClientMessageId(),
            session_id: sid,
            role: "assistant",
            content: question,
            created_at: new Date().toISOString(),
            run_id: result.run.id,
          },
        ]);
      }
    } catch (err) {
      if (optimisticId != null) {
        const idToDrop = optimisticId;
        setMessages((prev) => prev.filter((m) => String(m.id) !== idToDrop));
      }
      showError(err);
      throw err;
    } finally {
      setBusy(false);
    }
  };

  /**
   * After the user edits intake, sends a canned "please update the roadmap" line
   * through handleSend so a new run is stored. Errors are already shown there.
   * If the prompt text should change, edit the string here — not ChatPanel.
   */
  const handleReplan = async () => {
    try {
      await handleSend("Please update the roadmap with my revised intake.");
    } catch {
      /* handleSend already showed the alert and dropped the optimistic bubble */
    }
  };

  /**
   * Waits up to ms, but returns early when playback is skipped or replaced, so "Skip to result" and
   * "Exit replay" take effect at once instead of after the current pause.
   */
  const pause = async (ms: number, token: number) => {
    const end = Date.now() + ms;
    while (Date.now() < end && !skipRef.current && token === playToken.current) {
      await new Promise((resolve) => setTimeout(resolve, 40));
    }
  };

  /**
   * Replays a saved demo without calling Claude. The server returns the whole saved run at once; this fills
   * the form with that building, shows the question, then reveals the run log one step at a time (scrolling
   * with it, the tool counter climbing) and finally shows the plan, as a live run would. Chat and re-plan are
   * switched off until the replay is exited, because a new message would start a real paid run.
   */
  const handleReplay = async (caseId: string) => {
    const token = ++playToken.current;
    skipRef.current = false;
    setBusy(true);
    setPlaying(true);
    setError(null);
    try {
      const result = await replayCase(caseId);
      if (token !== playToken.current) return;
      setSessionId(null); // the replay's session is never reused for chat
      setDocuments([]);
      setRuns([]);
      setSelectedRunId(null);
      setProfile(apiToProfile(result.session.profile as Record<string, unknown>));
      setChatDraft("");
      setReplayMode({ label: result.case.label, kind: result.case.kind });
      setMessages([
        {
          id: nextClientMessageId(),
          session_id: result.session.id,
          role: "user",
          content: result.case.question,
          created_at: new Date().toISOString(),
          run_id: null,
        },
      ]);

      const events = [...result.run.events].sort((a, b) => a.seq - b.seq);
      const delays = playbackDelays(events);
      const running = (shown: typeof events): RunResponse => ({
        ...result.run,
        status: "running",
        finished_at: null,
        output: {},
        flags: {},
        tool_call_count: shown.filter((e) => e.kind === "tool_call").length,
        elapsed_seconds: null,
        events: shown,
      });
      appendRun(running([]));
      for (let i = 0; i < events.length; i++) {
        await pause(delays[i], token);
        if (token !== playToken.current) return;
        if (skipRef.current) break;
        appendRun(running(events.slice(0, i + 1)));
      }
      if (token !== playToken.current) return;
      appendRun(result.run);
      if (result.message) {
        const claims = claimsFromRun(result.run);
        setMessages((prev) => [...prev, { ...result.message!, claims: claims.length ? claims : undefined }]);
      }
    } catch (err) {
      if (token === playToken.current) showError(err);
    } finally {
      if (token === playToken.current) {
        setBusy(false);
        setPlaying(false);
      }
    }
  };

  /** Leaves the replay and returns to a blank planner, ready for a real run. */
  const exitReplay = () => {
    playToken.current++;
    skipRef.current = true;
    setReplayMode(null);
    setPlaying(false);
    setBusy(false);
    setProfile(emptyProfile());
    setDocuments([]);
    setMessages([]);
    setRuns([]);
    setSelectedRunId(null);
    setChatDraft(DANA_DEFAULT_QUESTION);
  };

  const activeRun =
    runs.find((r) => r.id === selectedRunId) ?? runs[runs.length - 1] ?? null;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="border-b px-4 py-3 flex items-center gap-3 shrink-0">
        <Image src="/fritts-logo-mark.png" alt="Professor Fritts" width={487} height={535} className="h-10 w-auto rounded" />
        <div>
          <h1 className="text-lg font-semibold leading-tight">Professor Fritts</h1>
          <p className="text-sm text-muted-foreground">building renewable energy planner</p>
        </div>
      </header>

      {replayMode && (
        <div className="px-4 pt-3">
          <Alert>
            <AlertTitle>Replay of a saved run: {replayMode.label}</AlertTitle>
            <AlertDescription>
              <p>
                {replayMode.kind === "recorded"
                  ? "A recording of a real Claude run, played back from saved data. No Claude call is being made."
                  : "A scripted demo: the numbers come from real tool data, but we wrote the plan text. No Claude call is being made."}
              </p>
              <div className="pt-2">
                {playing ? (
                  <button
                    type="button"
                    className="rounded border px-2 py-1 text-xs"
                    onClick={() => {
                      skipRef.current = true;
                    }}
                  >
                    Skip to result
                  </button>
                ) : (
                  <button type="button" className="rounded border px-2 py-1 text-xs" onClick={exitReplay}>
                    Exit replay
                  </button>
                )}
              </div>
            </AlertDescription>
          </Alert>
        </div>
      )}

      {error && (
        <div className="px-4 pt-3">
          <Alert variant="destructive">
            <AlertTitle>Something went wrong</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      )}

      <main className="flex-1 grid grid-cols-1 lg:grid-cols-[minmax(280px,1fr)_minmax(320px,1.2fr)_minmax(300px,1fr)] gap-3 p-3 min-h-0">
        <div className="flex flex-col gap-3 min-h-0">
          <IntakeForm
            profile={profile}
            onChange={setProfile}
            onLoadDana={() => void loadDana()}
            onUpdateAndReplan={() => void handleReplan()}
            busy={busy}
            replayCases={replayCases}
            onReplay={(caseId) => void handleReplay(caseId)}
            replayLocked={replayMode !== null}
          />
          <DocumentUpload documents={documents} onUpload={handleUpload} busy={busy} />
        </div>

        <ChatPanel
          messages={messages}
          onSend={handleSend}
          busy={busy}
          missingFields={missingRequiredFields(profile)}
          lockedReason={
            replayMode
              ? "This is a replay of a saved run, so chat is switched off. Exit the replay to plan your own."
              : undefined
          }
          draft={chatDraft}
          onDraftChange={setChatDraft}
        />

        <Tabs defaultValue="run-log" className="h-full flex flex-col min-h-0">
          <TabsList className="shrink-0 w-full">
            <TabsTrigger value="run-log" className="flex-1">
              Run log
            </TabsTrigger>
            <TabsTrigger value="roadmap" className="flex-1">
              Roadmap
            </TabsTrigger>
          </TabsList>
          <TabsContent value="run-log" className="flex-1 min-h-0 mt-2">
            <RunLogPanel runs={runs} selectedRunId={selectedRunId} onSelectRun={setSelectedRunId} />
          </TabsContent>
          <TabsContent value="roadmap" className="flex-1 min-h-0 mt-2">
            <RoadmapPanel run={activeRun} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
