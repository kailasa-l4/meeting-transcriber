import { useCallback, useRef, useState } from "react";
import { connect, disconnect, sendAudio, sendStartMeeting, sendStopMeeting } from "@/lib/ws-client";
import { startCapture, stopCapture } from "@/lib/audio-capture";

export interface TranscriptEntry {
  text: string;
  speaker: number | null;
  timestamp: number | null;
  isFinal: boolean;
}

export interface SummaryEntry {
  summary: string;
  timeRange: string;
}

export type MeetingState = "idle" | "starting" | "recording" | "stopping" | "stopped";

export function useMeeting() {
  const [state, setState] = useState<MeetingState>("idle");
  const [transcripts, setTranscripts] = useState<TranscriptEntry[]>([]);
  const [summaries, setSummaries] = useState<SummaryEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sessionIdRef = useRef<string>("");

  const startMeeting = useCallback(async (channelId?: string) => {
    setError(null);
    setTranscripts([]);
    setSummaries([]);
    setElapsedSeconds(0);
    setState("starting");

    try {
      // Request mic access FIRST (needs user gesture context from the button click)
      await startCapture(sendAudio);

      const res = await fetch("/api/session-id");
      const { session_id } = await res.json();
      sessionIdRef.current = session_id;

      connect(session_id, {
        onTranscript: (data) => {
          setTranscripts((prev) => {
            if (!data.is_final) {
              const withoutInterim = prev.filter((t) => t.isFinal);
              return [...withoutInterim, { text: data.text, speaker: data.speaker, timestamp: data.timestamp, isFinal: false }];
            }
            const withoutInterim = prev.filter((t) => t.isFinal);
            return [...withoutInterim, { text: data.text, speaker: data.speaker, timestamp: data.timestamp, isFinal: true }];
          });
        },
        onSummary: (data) => {
          setSummaries((prev) => [{ summary: data.summary, timeRange: data.time_range }, ...prev]);
        },
        onStatus: (data) => {
          if (data.state === "recording") setState("recording");
          if (data.state === "stopped") {
            setState("stopped");
            stopCapture();
            disconnect();
            if (timerRef.current) clearInterval(timerRef.current);
          }
        },
        onError: (data) => setError(data.message),
        onOpen: () => {
          // Audio is already capturing — just tell the server to start
          sendStartMeeting(channelId);
          timerRef.current = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
        },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start meeting");
      stopCapture();
      setState("idle");
    }
  }, []);

  const stopMeeting = useCallback(() => {
    setState("stopping");
    stopCapture();
    sendStopMeeting();
  }, []);

  return { state, transcripts, summaries, error, elapsedSeconds, startMeeting, stopMeeting };
}
