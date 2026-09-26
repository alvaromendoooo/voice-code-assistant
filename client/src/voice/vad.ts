/**
 * Energy-based voice activity segmenter. Consumes raw mono 16-bit PCM in arbitrarily-sized
 * chunks (as they arrive from SoX's stdout) and emits one finalized segment buffer per
 * utterance: speech is deemed to have ended once enough consecutive low-energy frames
 * follow it. Pure logic, no I/O, so it's independently testable from mic-capture.ts.
 */

const BYTES_PER_SAMPLE = 2; // 16-bit PCM

export interface VadOptions {
  sampleRate: number;
  threshold: number; // RMS threshold on the 16-bit sample scale
  silenceMs: number; // sustained silence duration that ends a segment
  frameMs?: number; // analysis frame size, default 20ms
}

export type SegmentHandler = (pcm: Buffer) => void;

export class SpeechSegmenter {
  private readonly frameBytes: number;
  private readonly silenceFrameThreshold: number;
  private leftover: Buffer = Buffer.alloc(0);
  private speechFrames: Buffer[] = [];
  private inSpeech = false;
  private silenceFrameCount = 0;

  constructor(
    private readonly options: VadOptions,
    private readonly onSegment: SegmentHandler
  ) {
    const frameMs = options.frameMs ?? 20;
    const frameSamples = Math.round((options.sampleRate * frameMs) / 1000);
    this.frameBytes = frameSamples * BYTES_PER_SAMPLE;
    this.silenceFrameThreshold = Math.max(1, Math.ceil(options.silenceMs / frameMs));
  }

  push(chunk: Buffer): void {
    const data = Buffer.concat([this.leftover, chunk]);
    let offset = 0;
    while (offset + this.frameBytes <= data.length) {
      this.processFrame(data.subarray(offset, offset + this.frameBytes));
      offset += this.frameBytes;
    }
    this.leftover = Buffer.from(data.subarray(offset));
  }

  /** Finalizes any in-progress segment. Call when the input stream ends. */
  flush(): void {
    this.finalizeSegment();
  }

  private processFrame(frame: Buffer): void {
    const isSpeech = computeRms(frame) >= this.options.threshold;

    if (isSpeech) {
      this.inSpeech = true;
      this.silenceFrameCount = 0;
      this.speechFrames.push(frame);
      return;
    }

    if (!this.inSpeech) {
      return; // silence before any detected speech: ignore
    }

    this.silenceFrameCount += 1;
    this.speechFrames.push(frame);
    if (this.silenceFrameCount >= this.silenceFrameThreshold) {
      this.finalizeSegment();
    }
  }

  private finalizeSegment(): void {
    if (this.speechFrames.length === 0) {
      return;
    }
    const pcm = Buffer.concat(this.speechFrames);
    this.speechFrames = [];
    this.inSpeech = false;
    this.silenceFrameCount = 0;
    this.onSegment(pcm);
  }
}

function computeRms(frame: Buffer): number {
  const sampleCount = frame.length / BYTES_PER_SAMPLE;
  if (sampleCount === 0) return 0;
  let sumSquares = 0;
  for (let i = 0; i < frame.length; i += BYTES_PER_SAMPLE) {
    const sample = frame.readInt16LE(i);
    sumSquares += sample * sample;
  }
  return Math.sqrt(sumSquares / sampleCount);
}
