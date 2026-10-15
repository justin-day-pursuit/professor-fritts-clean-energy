/**
 * Bills and document upload — lists each received file and shows parsed summary from the API.
 * Lives under intake; parent passes session id and accumulates DocumentResponse rows.
 */
"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DocumentResponse } from "@/lib/types";
import { useRef } from "react";

export interface DocumentUploadProps {
  documents: DocumentResponse[];
  onUpload: (file: File) => Promise<void>;
  busy: boolean;
}

export function DocumentUpload({ documents, onUpload, busy }: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    for (const file of Array.from(files)) {
      await onUpload(file);
    }
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Documents</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            accept=".csv,.pdf,.png,.jpg,.jpeg"
            onChange={(e) => void handleFiles(e.target.files)}
          />
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={() => inputRef.current?.click()}
          >
            Upload file
          </Button>
        </div>
        {documents.length === 0 ? (
          <p className="text-muted-foreground text-xs">No files received yet.</p>
        ) : (
          <ul className="space-y-2">
            {documents.map((doc) => (
              <li key={doc.id} className="rounded-md border p-2 space-y-1">
                <div className="font-medium truncate">{doc.filename}</div>
                <div className="text-xs text-muted-foreground">
                  {(doc.size_bytes / 1024).toFixed(1)} KB · {doc.content_type}
                </div>
                <ParsedSummary summary={doc.parsed_summary} />
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

/** Renders parsed_summary in plain language for bill CSVs and generic uploads. */
function ParsedSummary({ summary }: { summary: Record<string, unknown> }) {
  const parsed = summary.parsed === true;
  const total = summary.total_kwh;
  const status = String(summary.status ?? "received");

  return (
    <div className="text-xs bg-muted/50 rounded p-2 font-mono whitespace-pre-wrap break-all">
      {parsed && total != null ? (
        <>
          Parsed bills · total {String(total)} kWh
          {Array.isArray(summary.months) ? ` · ${summary.months.length} months` : ""}
        </>
      ) : (
        <>
          {status}
          {summary.note ? ` — ${String(summary.note)}` : ""}
        </>
      )}
    </div>
  );
}
