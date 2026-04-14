import { startCapture, stopCapture } from "./audio-capture.js";
import * as wsClient from "./ws-client.js";
import {
  requestWakeLock,
  releaseWakeLock,
  isSupported as wakeLockSupported,
} from "./wake-lock.js";

// DOM elements
const startBtn = document.getElementById("start-btn");
const stopBtn = document.getElementById("stop-btn");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const timerEl = document.getElementById("timer");
const transcriptEl = document.getElementById("transcript");
const summariesEl = document.getElementById("summaries");
const channelInput = document.getElementById("channel-id");
const userNameInput = document.getElementById("user-name");
const wakeLockWarning = document.getElementById("wake-lock-warning");

let sessionId = null;
let timerInterval = null;
let startTime = null;
let isRecording = false;

const SPEAKER_COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4", "#ec4899"];

// Show wake lock warning if not supported
if (!wakeLockSupported()) {
  wakeLockWarning.textContent =
    "Your browser does not support Screen Wake Lock. The screen may turn off during recording.";
  wakeLockWarning.classList.add("visible");
}

startBtn.addEventListener("click", handleStart);
stopBtn.addEventListener("click", handleStop);

async function handleStart() {
  startBtn.disabled = true;
  statusText.textContent = "Starting...";

  try {
    // Get a session ID from the server
    const resp = await fetch("/api/session-id");
    const data = await resp.json();
    sessionId = data.session_id;

    // Acquire wake lock
    const lockAcquired = await requestWakeLock();
    if (!lockAcquired && wakeLockSupported()) {
      wakeLockWarning.textContent =
        "Could not acquire screen wake lock. Screen may turn off.";
      wakeLockWarning.classList.add("visible");
    }

    // Connect WebSocket
    wsClient.connect(sessionId, {
      onTranscript: handleTranscript,
      onSummary: handleSummary,
      onStatus: handleStatus,
      onError: handleError,
      onOpen: () => {
        // Send start command
        wsClient.sendControl({
          type: "start_meeting",
          channel_id: channelInput.value.trim() || null,
          user_name: userNameInput.value.trim() || "Unknown",
        });
      },
      onClose: () => {
        if (isRecording) {
          handleStop();
        }
      },
    });

    // Start audio capture
    await startCapture((audioChunk) => {
      wsClient.sendAudio(audioChunk);
    });

    isRecording = true;
    startTime = Date.now();
    timerInterval = setInterval(updateTimer, 1000);

    startBtn.classList.add("hidden");
    stopBtn.classList.remove("hidden");
    statusDot.className = "status-dot recording";
    channelInput.disabled = true;
    userNameInput.disabled = true;

    // Clear previous content
    transcriptEl.innerHTML = "";
    summariesEl.innerHTML = "";
  } catch (err) {
    console.error("Failed to start:", err);
    statusText.textContent = `Error: ${err.message}`;
    startBtn.disabled = false;
    await releaseWakeLock();
  }
}

async function handleStop() {
  stopBtn.disabled = true;
  statusText.textContent = "Stopping...";

  // Stop audio capture immediately
  stopCapture();

  // Send stop command — server will generate final summary then send "stopped" status
  wsClient.sendControl({ type: "stop_meeting" });

  // Cleanup happens in handleStatus when server sends state="stopped"
}

function finishStop() {
  wsClient.disconnect();
  releaseWakeLock();

  isRecording = false;
  clearInterval(timerInterval);

  stopBtn.classList.add("hidden");
  startBtn.classList.remove("hidden");
  startBtn.disabled = false;
  stopBtn.disabled = false;
  statusDot.className = "status-dot idle";
  statusText.textContent = "Stopped";
  channelInput.disabled = false;
  userNameInput.disabled = false;
}

function formatTimestamp(seconds) {
  if (seconds == null) return "--:--";
  const m = String(Math.floor(seconds / 60)).padStart(2, "0");
  const s = String(Math.floor(seconds % 60)).padStart(2, "0");
  return `${m}:${s}`;
}

function handleTranscript(data) {
  if (data.is_final) {
    // Remove interim element if present
    const interim = transcriptEl.querySelector(".transcript-interim");
    if (interim) interim.remove();

    const line = document.createElement("div");
    line.className = "transcript-line";

    const ts = document.createElement("span");
    ts.className = "transcript-ts";
    ts.textContent = formatTimestamp(data.timestamp);

    const speaker = document.createElement("span");
    speaker.className = "transcript-speaker";
    const speakerNum = data.speaker ?? 0;
    speaker.textContent = `S${speakerNum}`;
    speaker.style.color = SPEAKER_COLORS[speakerNum % SPEAKER_COLORS.length];

    const text = document.createElement("span");
    text.className = "transcript-text";
    text.textContent = data.text;

    line.appendChild(ts);
    line.appendChild(speaker);
    line.appendChild(text);
    transcriptEl.appendChild(line);
  } else {
    // Show interim text at the bottom
    let interim = transcriptEl.querySelector(".transcript-interim");
    if (!interim) {
      interim = document.createElement("div");
      interim.className = "transcript-line transcript-interim";
      transcriptEl.appendChild(interim);
    }
    interim.textContent = data.text;
  }
  // Auto-scroll
  transcriptEl.scrollTop = transcriptEl.scrollHeight;
}

function handleSummary(data) {
  const card = document.createElement("div");
  card.className = "summary-card";

  const header = document.createElement("div");
  header.className = "summary-header";
  header.textContent = `Summary (${data.time_range})`;

  const body = document.createElement("div");
  body.className = "summary-body";
  body.textContent = data.summary;

  card.appendChild(header);
  card.appendChild(body);
  summariesEl.prepend(card);
}

function handleStatus(data) {
  statusText.textContent = data.message;

  if (data.state === "recording") {
    statusDot.className = "status-dot recording";
  } else if (data.state === "stopped") {
    finishStop();
  }
}

function handleError(data) {
  statusText.textContent = `Error: ${data.message}`;
  console.error("Server error:", data.message);
}

function updateTimer() {
  if (!startTime) return;
  const elapsed = Math.floor((Date.now() - startTime) / 1000);
  const mins = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const secs = String(elapsed % 60).padStart(2, "0");
  timerEl.textContent = `${mins}:${secs}`;
}

// Re-acquire wake lock on visibility change (e.g., tab switch)
document.addEventListener("visibilitychange", async () => {
  if (document.visibilityState === "visible" && isRecording) {
    await requestWakeLock();
  }
});
