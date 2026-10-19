/**
 * Center chat — user messages, Fritts replies, and the send box.
 * needs_input runs show the assistant question once (from the API), not as a duplicate user bubble.
 */
"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { ClaimSource } from "@/components/claim-source";
import { downloadRoadmapMarkdown } from "@/lib/api";
import { LabelBadge } from "@/components/label-badge";
import type { Claim, MessageResponse } from "@/lib/types";
import { useState } from "react";

/**
 * Chat row. Server messages keep numeric Message.id. Client-only bubbles use a
 * "local:" string from page.tsx so React keys (msg.id) never collide with the
 * database. If ids become UUIDs on the server, keep a prefix that cannot match.
 */
export interface ChatMessage extends Omit<MessageResponse, "id"> {
  id: number | string;
  claims?: Claim[];
}

interface FollowUpBoxProps {
  onSend: (text: string) => Promise<void>;
  busy: boolean;
  runId?: number | null;
}

/**
 * Inline follow-up box displayed inside the completed-plan speech bubble.
 * Includes prompt pills for natural next steps and a text box to continue brainstorming.
 */
function FollowUpBox({ onSend, busy, runId }: FollowUpBoxProps) {
  const [draft, setDraft] = useState("");
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    if (!runId || downloading) return;
    setDownloading(true);
    try {
      const text = await downloadRoadmapMarkdown(runId);
      const blob = new Blob([text], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `roadmap-run-${runId}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download roadmap", err);
    } finally {
      setDownloading(false);
    }
  };

  const handlePillClick = async (promptText: string) => {
    if (busy) return;
    setDraft(promptText);
    try {
      await onSend(promptText);
      setDraft("");
    } catch {
      // Keep draft if send fails
    }
  };

  const submit = async () => {
    const trimmed = draft.trim();
    if (!trimmed || busy) return;
    setDraft("");
    try {
      await onSend(trimmed);
    } catch {
      setDraft(trimmed);
    }
  };

  return (
    <div className="mt-3 pt-3 border-t border-dashed space-y-2.5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-foreground">
          Continue chatting with Professor Fritts:
        </span>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {runId ? (
          <button
            type="button"
            disabled={downloading}
            onClick={() => void handleDownload()}
            className="inline-flex items-center gap-1 rounded-full border bg-background px-2.5 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors disabled:opacity-50"
          >
            📥 {downloading ? "Downloading…" : "Download roadmap (.md)"}
          </button>
        ) : null}
        <button
          type="button"
          disabled={busy}
          onClick={() =>
            void handlePillClick(
              "Could you explain Section 6 (Costs & Financing Scenarios) in simpler terms?"
            )
          }
          className="inline-flex items-center gap-1 rounded-full border bg-background px-2.5 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors disabled:opacity-50"
        >
          🔍 Explain Section 6 (Costs)
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() =>
            void handlePillClick(
              "What missing information or professional verifications do we need next to make this plan actionable?"
            )
          }
          className="inline-flex items-center gap-1 rounded-full border bg-background px-2.5 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors disabled:opacity-50"
        >
          ✏️ Add missing information / Next steps
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() =>
            void handlePillClick(
              "How can we reduce the upfront capital cost or improve payback?"
            )
          }
          className="inline-flex items-center gap-1 rounded-full border bg-background px-2.5 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors disabled:opacity-50"
        >
          💡 Reduce upfront cost
        </button>
      </div>

      <div className="flex gap-2 items-end pt-1">
        <Textarea
          rows={2}
          placeholder="Ask a question or brainstorm adjustments to this plan…"
          value={draft}
          disabled={busy}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void submit();
            }
          }}
          className="min-h-[50px] text-xs bg-background"
        />
        <Button
          type="button"
          size="sm"
          disabled={busy || !draft.trim()}
          onClick={() => void submit()}
          className="h-8 text-xs shrink-0"
        >
          Ask
        </Button>
      </div>
    </div>
  );
}

export interface ChatPanelProps {
  messages: ChatMessage[];
  onSend: (text: string) => Promise<void>;
  busy: boolean;
  draft?: string;
  onDraftChange?: (text: string) => void;
  /** Intake fields still empty; while any remain, sending is blocked and they are listed under the box. */
  missingFields?: string[];
  /** When set, sending is switched off and this sentence is shown (used while a saved replay is on screen). */
  lockedReason?: string;
}

export function ChatPanel({ messages, onSend, busy, draft, onDraftChange, missingFields = [], lockedReason }: ChatPanelProps) {
  const blocked = missingFields.length > 0 || Boolean(lockedReason);
  const [localDraft, setLocalDraft] = useState("");
  const text = draft ?? localDraft;
  const setText = onDraftChange ?? setLocalDraft;

  /**
   * Clears the box, then asks the parent to post the line. If send fails, the
   * parent drops the optimistic bubble and rethrows; this catch puts the draft
   * back. If you stop throwing from handleSend, restore the draft there instead.
   */
  const submit = async () => {
    const trimmed = text.trim();
    if (!trimmed || busy || blocked) return;
    setText("");
    try {
      await onSend(trimmed);
    } catch {
      setText(trimmed);
    }
  };

  return (
    <Card className="h-full flex flex-col min-h-0">
      <CardHeader className="pb-2 shrink-0">
        <CardTitle className="text-base">Chat with Professor Fritts</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 min-h-0 p-0">
        <ScrollArea className="h-[min(520px,50vh)] px-4">
          <div className="space-y-3 py-2">
            {messages.length === 0 && (
              <p className="text-sm text-muted-foreground">
                Ask a planning question after filling intake (or load Dana&apos;s example).
              </p>
            )}
            {(() => {
              const lastPlanIndex = messages.reduce(
                (acc, m, i) =>
                  m.role === "assistant" && m.claims && m.claims.length > 0 ? i : acc,
                -1
              );
              return messages.map((msg, index) => (
                <div
                  key={msg.id}
                  className={
                    msg.role === "user"
                      ? "ml-8 rounded-lg bg-primary/10 p-3 text-sm"
                      : "mr-8 rounded-lg border bg-card p-3 text-sm space-y-2"
                  }
                >
                  <div className="text-xs font-medium text-muted-foreground mb-1">
                    {msg.role === "user" ? "You" : "Professor Fritts"}
                  </div>
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                  {msg.claims && msg.claims.length > 0 && (
                    <ul className="space-y-2 pt-2 border-t">
                      {msg.claims.map((claim, i) => (
                        <li key={`${msg.id}-claim-${i}`} className="space-y-1">
                          <LabelBadge label={claim.label} confidence={claim.confidence} />
                          <p className="text-xs">{claim.text}</p>
                          <ClaimSource claim={claim} />
                        </li>
                      ))}
                    </ul>
                  )}
                  {index === lastPlanIndex && (
                    <FollowUpBox onSend={onSend} busy={busy} runId={msg.run_id} />
                  )}
                </div>
              ));
            })()}
          </div>
        </ScrollArea>
      </CardContent>
      <CardFooter className="flex flex-col gap-2 border-t pt-4">
        <Textarea
          rows={3}
          placeholder="Ask Professor Fritts…"
          value={text}
          disabled={busy}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void submit();
            }
          }}
        />
        {lockedReason ? (
          <p className="w-full text-xs text-muted-foreground">{lockedReason}</p>
        ) : (
          blocked && (
            <p className="w-full text-xs text-muted-foreground">
              Fill in the intake first. Still needed: {missingFields.join(", ")}
            </p>
          )
        )}
        <Button type="button" disabled={busy || blocked || !text.trim()} onClick={() => void submit()}>
          Send
        </Button>
      </CardFooter>
    </Card>
  );
}
