import { useState, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { TranscriptLine } from "./transcript-line";
import { transcriptionsApi, type TranscriptionSegment } from "@/lib/api";

function formatDuration(seconds: number | null): string {
  if (!seconds) return "";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s`;
}

export function FileTranscriber() {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{
    transcript: string;
    segments: TranscriptionSegment[];
    duration: number | null;
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const data = await transcriptionsApi.upload(file);
      const segments: TranscriptionSegment[] = data.segments
        ? JSON.parse(data.segments)
        : [];
      setResult({
        transcript: data.transcript || "",
        segments,
        duration: data.duration_seconds,
      });
      queryClient.invalidateQueries({ queryKey: ["transcriptions"] });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }

  function handleReset() {
    setFile(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-border">
        <SidebarTrigger />
        <h1 className="font-semibold text-lg flex-1">Transcribe File</h1>
        {result && (
          <span className="text-sm text-muted-foreground">
            {formatDuration(result.duration)}
          </span>
        )}
      </div>

      {/* Upload area */}
      {!result && (
        <div className="p-4 space-y-4">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              dragOver
                ? "border-primary bg-primary/10"
                : "border-border hover:border-primary/50"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*,video/*"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) setFile(f);
              }}
            />
            <div className="text-muted-foreground">
              {file ? (
                <div>
                  <p className="text-foreground font-medium">{file.name}</p>
                  <p className="text-sm mt-1">
                    {(file.size / (1024 * 1024)).toFixed(1)} MB
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-lg mb-1">Drop audio or video file here</p>
                  <p className="text-sm">or click to browse</p>
                </div>
              )}
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="flex-1"
            >
              {uploading ? "Transcribing..." : "Transcribe"}
            </Button>
            {file && !uploading && (
              <Button variant="outline" onClick={handleReset}>
                Clear
              </Button>
            )}
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          {uploading && (
            <div className="text-center py-8">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-primary border-r-transparent" />
              <p className="mt-3 text-sm text-muted-foreground">
                Processing with Deepgram Nova-3...
              </p>
            </div>
          )}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="flex-1 overflow-hidden flex flex-col p-4 gap-4">
          <div className="flex items-center gap-2">
            <Badge variant="secondary">{file?.name}</Badge>
            <Button variant="outline" size="sm" onClick={handleReset}>
              New Upload
            </Button>
          </div>

          <ScrollArea className="flex-1 rounded-md border border-border p-3">
            {result.segments.length > 0 ? (
              result.segments.map((seg, i) => (
                <TranscriptLine
                  key={i}
                  speaker={seg.speaker}
                  text={seg.text}
                  isFinal={true}
                />
              ))
            ) : (
              <p className="text-sm whitespace-pre-wrap">{result.transcript}</p>
            )}
          </ScrollArea>
        </div>
      )}
    </div>
  );
}
