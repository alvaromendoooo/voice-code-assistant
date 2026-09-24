/**
 * Microphone capture with VAD (voice activity detection) segmentation.
 * Emits short finalized audio chunks on pause, rather than buffering the whole
 * recording -- see the latency discussion in docs/architecture/phase1-design.md.
 */

export type AudioChunkHandler = (chunk: ArrayBuffer, isFinal: boolean) => void;

export class MicCapture {
  start(onChunk: AudioChunkHandler): void {
    throw new Error("not implemented");
  }

  stop(): void {
    throw new Error("not implemented");
  }
}
