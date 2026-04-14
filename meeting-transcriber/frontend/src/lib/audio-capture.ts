let audioContext: AudioContext | null = null;
let workletNode: AudioWorkletNode | null = null;
let stream: MediaStream | null = null;

export async function startCapture(onChunk: (data: ArrayBuffer) => void): Promise<void> {
  stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      sampleRate: 16000,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });

  audioContext = new AudioContext({ sampleRate: 16000 });
  await audioContext.audioWorklet.addModule("/js/audio-processor.worklet.js");

  const source = audioContext.createMediaStreamSource(stream);
  workletNode = new AudioWorkletNode(audioContext, "audio-chunk-processor");

  workletNode.port.onmessage = (event: MessageEvent) => {
    onChunk(event.data);
  };

  source.connect(workletNode);
}

export function stopCapture(): void {
  if (workletNode) {
    workletNode.disconnect();
    workletNode = null;
  }
  if (stream) {
    stream.getTracks().forEach((t) => t.stop());
    stream = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
}
