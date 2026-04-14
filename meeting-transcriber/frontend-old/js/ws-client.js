/**
 * WebSocket client for communicating with the meeting transcriber backend.
 */

let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT = 5;
const BASE_DELAY = 1000;

// Event callbacks
let onTranscript = null;
let onSummary = null;
let onStatus = null;
let onError = null;
let onClose = null;
let onOpen = null;

/**
 * Connect to the meeting WebSocket.
 * @param {string} sessionId
 * @param {object} callbacks - { onTranscript, onSummary, onStatus, onError, onClose, onOpen }
 */
export function connect(sessionId, callbacks = {}) {
  onTranscript = callbacks.onTranscript || null;
  onSummary = callbacks.onSummary || null;
  onStatus = callbacks.onStatus || null;
  onError = callbacks.onError || null;
  onClose = callbacks.onClose || null;
  onOpen = callbacks.onOpen || null;

  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${protocol}//${location.host}/ws/meeting/${sessionId}`;

  ws = new WebSocket(url);

  ws.onopen = () => {
    reconnectAttempts = 0;
    if (onOpen) onOpen();
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case "transcript":
          if (onTranscript) onTranscript(data);
          break;
        case "summary":
          if (onSummary) onSummary(data);
          break;
        case "status":
          if (onStatus) onStatus(data);
          break;
        case "error":
          if (onError) onError(data);
          break;
      }
    } catch (e) {
      console.error("Failed to parse WebSocket message:", e);
    }
  };

  ws.onclose = () => {
    if (onClose) onClose();
  };

  ws.onerror = (err) => {
    console.error("WebSocket error:", err);
  };
}

/**
 * Send binary audio data.
 * @param {ArrayBuffer} chunk
 */
export function sendAudio(chunk) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(chunk);
  }
}

/**
 * Send a JSON control message.
 * @param {object} message
 */
export function sendControl(message) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(message));
  }
}

/**
 * Close the WebSocket connection.
 */
export function disconnect() {
  if (ws) {
    ws.close();
    ws = null;
  }
}
