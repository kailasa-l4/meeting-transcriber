import { getToken } from "./auth";

export interface WsCallbacks {
  onTranscript?: (data: { text: string; is_final: boolean; speaker: number; timestamp: number }) => void;
  onSummary?: (data: { summary: string; time_range: string }) => void;
  onStatus?: (data: { state: string; message: string }) => void;
  onError?: (data: { message: string }) => void;
  onClose?: () => void;
  onOpen?: () => void;
}

let ws: WebSocket | null = null;

function getWsBase(): string {
  // In dev, Vite's proxy doesn't forward WS upgrades with TanStack Start.
  // Connect directly to the backend API server.
  const isDev = import.meta.env.DEV;
  if (isDev) {
    return "ws://localhost:8000";
  }
  // In production, the backend serves everything on the same origin.
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${location.host}`;
}

export function connect(sessionId: string, callbacks: WsCallbacks): void {
  const token = getToken();
  const url = `${getWsBase()}/ws/meeting/${sessionId}?token=${token}`;

  ws = new WebSocket(url);

  ws.onopen = () => {
    callbacks.onOpen?.();
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case "transcript":
          callbacks.onTranscript?.(data);
          break;
        case "summary":
          callbacks.onSummary?.(data);
          break;
        case "status":
          callbacks.onStatus?.(data);
          break;
        case "error":
          callbacks.onError?.(data);
          break;
      }
    } catch (e) {
      console.error("WS parse error:", e);
    }
  };

  ws.onclose = () => {
    callbacks.onClose?.();
  };

  ws.onerror = (err) => {
    console.error("WS error:", err);
  };
}

export function sendStartMeeting(channelId?: string): void {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "start_meeting", channel_id: channelId || undefined }));
  }
}

export function sendStopMeeting(): void {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "stop_meeting" }));
  }
}

export function sendAudio(data: ArrayBuffer): void {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(data);
  }
}

export function disconnect(): void {
  if (ws) {
    ws.close();
    ws = null;
  }
}
