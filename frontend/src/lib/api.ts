import { getToken, clearAuth } from "./auth";

const BASE_URL = "";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearAuth();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || res.statusText);
  }

  return res.json();
}

// Auth
export const authApi = {
  register: (data: { username: string; password: string; display_name: string }) =>
    request<{ token: string; user_id: number; username: string; display_name: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: { username: string; password: string }) =>
    request<{ token: string; user_id: number; username: string; display_name: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  me: () => request<{ id: number; username: string; display_name: string }>("/api/auth/me"),
};

// Meetings
export interface Meeting {
  id: number;
  session_id: string;
  title: string | null;
  status: string;
  duration_seconds: number | null;
  started_at: string;
  ended_at: string | null;
}

export interface MeetingDetail {
  meeting: Meeting & { channel_id: string; slack_thread_ts: string; user_id: number };
  transcripts: { speaker: number | null; text: string; timestamp: number | null }[];
  summaries: { type: string; content: string; time_range: string | null; created_at: string }[];
}

export const meetingsApi = {
  list: () => request<Meeting[]>("/api/meetings"),
  get: (id: number) => request<MeetingDetail>(`/api/meetings/${id}`),
};

// Transcriptions
export interface Transcription {
  id: number;
  file_name: string;
  status: string;
  duration_seconds: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface TranscriptionSegment {
  speaker: number;
  text: string;
  start: number;
  end: number;
}

export interface TranscriptionDetail extends Transcription {
  transcript: string | null;
  segments: string | null; // JSON string of TranscriptionSegment[]
  error_message: string | null;
}

export const transcriptionsApi = {
  list: () => request<Transcription[]>("/api/transcriptions"),
  get: (id: number) => request<TranscriptionDetail>(`/api/transcriptions/${id}`),
  upload: async (file: File): Promise<TranscriptionDetail> => {
    const token = getToken();
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch("/api/transcriptions/upload", {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (res.status === 401) {
      clearAuth();
      if (typeof window !== "undefined") window.location.href = "/login";
      throw new Error("Unauthorized");
    }
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || res.statusText);
    }
    return res.json();
  },
};
