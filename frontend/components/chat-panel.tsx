/**
 * Center chat — user messages, Fritts replies, and the send box.
 * needs_input runs show the assistant question once (from the API), not as a duplicate user bubble.
 */
"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
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

export interface ChatPanelProps {
  messages: ChatMessage[];
  onSend: (text: string) => Promise<void>;
  busy: boolean;
  draft?: string;
  onDraftChange?: (text: string) => void;
}

export function ChatPanel({ messages, onSend, busy, draft, onDraftChange }: ChatPanelProps) {
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
    if (!trimmed || busy) return;
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
            {messages.map((msg) => (
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
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
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
        <Button type="button" disabled={busy || !text.trim()} onClick={() => void submit()}>
          Send
        </Button>
      </CardFooter>
    </Card>
  );
}
