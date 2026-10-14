/**
 * Single-page Professor Fritts planner — intake, chat, and run/roadmap panels.
 * Wires child components to the harness API via frontend/lib/api.ts.
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
  postMessage,
  updateProfile,
  uploadDocument,
} from "@/lib/api";
import { DANA_DEFAULT_QUESTION, DANA_INTAKE } from "@/lib/dana-intake";
import { apiToProfile, emptyProfile, profileToApi } from "@/lib/profile-utils";
import type { Claim, DocumentResponse, IntakeProfile, RunResponse } from "@/lib/types";
import { useCallback, useState } from "react";

let localMessageId = 1;

function claimsFromRun(run: RunResponse): Claim[] {
  const roadmap = run.output?.roadmap as { sections?: { claims?: Claim[] }[] } | undefined;
  if (!roadmap?.sections) return [];
  return roadmap.sections.flatMap((s) => s.claims ?? []);
}

export default function Home() {
  const [profile, setProfile] = useState<IntakeProfile>(emptyProfile());
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [runs, setRuns] = useState<RunResponse[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatDraft, setChatDraft] = useState(DANA_DEFAULT_QUESTION);

  const showError = useCallback((err: unknown) => {
    const msg = err instanceof ApiError ? err.message : err instanceof Error ? err.message : String(err);
    setError(msg);
  }, []);

  const ensureSession = useCallback(async (): Promise<string> => {
    if (sessionId) return sessionId;
    const created = await createSession({ fixture_case: "case1_queens_library" });
    setSessionId(created.id);
    return created.id;
  }, [sessionId]);

  const loadDana = async () => {
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

  const appendRun = (run: RunResponse) => {
    setRuns((prev) => {
      const without = prev.filter((r) => r.id !== run.id);
      return [...without, run];
    });
    setSelectedRunId(run.id);
  };

  const handleSend = async (text: string) => {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await updateProfile(sid, { profile: profileToApi(profile) });
      const userLocal: ChatMessage = {
        id: localMessageId++,
        session_id: sid,
        role: "user",
        content: text,
        created_at: new Date().toISOString(),
        run_id: null,
      };
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
            id: localMessageId++,
            session_id: sid,
            role: "assistant",
            content: question,
            created_at: new Date().toISOString(),
            run_id: result.run.id,
          },
        ]);
      }
    } catch (err) {
      showError(err);
    } finally {
      setBusy(false);
    }
  };

  const handleReplan = async () => {
    await handleSend("Please update the roadmap with my revised intake.");
  };

  const activeRun =
    runs.find((r) => r.id === selectedRunId) ?? runs[runs.length - 1] ?? null;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="border-b px-4 py-3 flex items-center gap-3 shrink-0">
        <Image src="/fritts-logo.png" alt="Professor Fritts" width={40} height={40} className="rounded" />
        <div>
          <h1 className="text-lg font-semibold leading-tight">Professor Fritts</h1>
          <p className="text-sm text-muted-foreground">building renewable energy planner</p>
        </div>
      </header>

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
          />
          <DocumentUpload documents={documents} onUpload={handleUpload} busy={busy} />
        </div>

        <ChatPanel
          messages={messages}
          onSend={handleSend}
          busy={busy}
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
