/**
 * AudioWorklet processor: converts Float32 PCM to Int16 PCM
 * and posts binary buffers to the main thread.
 */
class AudioChunkProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._bufferSize = 4096; // Samples before sending a chunk
    this._buffer = new Float32Array(this._bufferSize);
    this._offset = 0;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || !input[0]) return true;

    const samples = input[0]; // Mono channel

    for (let i = 0; i < samples.length; i++) {
      this._buffer[this._offset++] = samples[i];

      if (this._offset >= this._bufferSize) {
        // Convert Float32 -> Int16
        const int16 = new Int16Array(this._bufferSize);
        for (let j = 0; j < this._bufferSize; j++) {
          const s = Math.max(-1, Math.min(1, this._buffer[j]));
          int16[j] = s < 0 ? s * 0x8000 : s * 0x7fff;
        }

        this.port.postMessage(int16.buffer, [int16.buffer]);
        this._buffer = new Float32Array(this._bufferSize);
        this._offset = 0;
      }
    }

    return true;
  }
}

registerProcessor("audio-chunk-processor", AudioChunkProcessor);
