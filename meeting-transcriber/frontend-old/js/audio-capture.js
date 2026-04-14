/**
 * Audio capture module — isolated so a future Capacitor swap only changes this file.
 * Exports: startCapture(onChunk), stopCapture()
 */

let audioContext = null;
let mediaStream = null;
let workletNode = null;

/**
 * Start capturing microphone audio.
 * @param {function(ArrayBuffer): void} onChunk - Called with Int16 PCM ArrayBuffer chunks
 * @returns {Promise<void>}
 */
export async function startCapture(onChunk) {
  // Request microphone with constraints optimized for speech
  mediaStream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      sampleRate: 16000,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });

  audioContext = new AudioContext({ sampleRate: 16000 });

  // Load the AudioWorklet processor
  await audioContext.audioWorklet.addModule("/js/audio-processor.worklet.js");

  const source = audioContext.createMediaStreamSource(mediaStream);
  workletNode = new AudioWorkletNode(audioContext, "audio-chunk-processor");

  workletNode.port.onmessage = (event) => {
    onChunk(event.data);
  };

  source.connect(workletNode);
  // Don't connect to destination — we don't want to play back the mic audio
}

/**
 * Stop capturing audio and release resources.
 */
export function stopCapture() {
  if (workletNode) {
    workletNode.disconnect();
    workletNode = null;
  }

  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
  }

  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
}
