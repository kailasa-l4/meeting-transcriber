import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { TranscriptLine } from "./transcript-line";
import { useMeeting } from "@/hooks/use-meeting";

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60).toString().padStart(2, "0");
  const s = (seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

export function MeetingRecorder() {
  const [channelId, setChannelId] = useState("");
  const { state, transcripts, summaries, error, elapsedSeconds, startMeeting, stopMeeting } = useMeeting();
  const transcriptEndRef = useRef<HTMLDivElement>(null);

  const isRecording = state === "recording" || state === "starting";
  const isStopping = state === "stopping";
  const isStopped = state === "stopped";

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcripts]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-border">
        <SidebarTrigger />
        <h1 className="font-semibold text-lg flex-1">Meeting Transcriber</h1>
        {isRecording && (
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-sm text-muted-foreground font-mono">{formatTime(elapsedSeconds)}</span>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="p-4 space-y-3 border-b border-border">
        <Input
          placeholder="Slack Channel ID (optional)"
          value={channelId}
          onChange={(e) => setChannelId(e.target.value)}
          disabled={isRecording || isStopping}
        />
        <div className="flex gap-2">
          {!isRecording && !isStopping && !isStopped && (
            <Button onClick={() => startMeeting(channelId || undefined)} className="flex-1">
              Start Meeting
            </Button>
          )}
          {isRecording && (
            <Button variant="destructive" onClick={stopMeeting} className="flex-1">
              Stop Meeting
            </Button>
          )}
          {isStopping && (
            <Button disabled className="flex-1">
              Generating summary...
            </Button>
          )}
          {isStopped && (
            <Button onClick={() => window.location.reload()} className="flex-1">
              New Meeting
            </Button>
          )}
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden flex flex-col gap-4 p-4">
        {/* Transcript */}
        <div className="flex-1 min-h-0">
          <h3 className="text-sm font-medium text-muted-foreground mb-2">Live Transcript</h3>
          <ScrollArea className="h-full max-h-[300px] rounded-md border border-border p-3">
            {transcripts.length === 0 && (
              <p className="text-sm text-muted-foreground">
                {isRecording ? "Listening..." : "Start a meeting to begin transcription"}
              </p>
            )}
            {transcripts.map((t, i) => (
              <TranscriptLine key={i} speaker={t.speaker} text={t.text} isFinal={t.isFinal} />
            ))}
            <div ref={transcriptEndRef} />
          </ScrollArea>
        </div>

        {/* Summaries */}
        <div className="flex-1 min-h-0">
          <h3 className="text-sm font-medium text-muted-foreground mb-2">Summaries</h3>
          <ScrollArea className="h-full max-h-[300px]">
            {summaries.length === 0 && (
              <p className="text-sm text-muted-foreground">Summaries will appear every 3 minutes</p>
            )}
            <div className="space-y-2">
              {summaries.map((s, i) => (
                <Card key={i}>
                  <CardHeader className="py-2 px-3">
                    <CardTitle className="text-xs font-medium">
                      <Badge variant="secondary">{s.timeRange}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="px-3 pb-3 pt-0">
                    <p className="text-sm whitespace-pre-wrap">{s.summary}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  );
}
