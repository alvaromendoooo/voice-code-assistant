/**
 * Microphone capture with VAD (voice activity detection) segmentation.
 * Emits short finalized audio chunks on pause, rather than buffering the whole
 * recording -- see the latency discussion in docs/architecture/phase1-design.md.
 *
 * Recording itself is delegated to SoX (a free, no-compile-required binary) rather than a
 * native Node audio binding, since this repo has no native build toolchain configured.
 * SoX's raw PCM stdout is fed through vad.ts's pure segmenter; each finalized segment is
 * wrapped into a WAV buffer (whisper.cpp reads files, not raw streams) and handed to the
 * caller via onChunk.
 */

import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";

import { getVoiceConfig } from "./config";
import { SpeechSegmenter } from "./vad";
import { pcmToWav } from "./wav";

export type AudioChunkHandler = (chunk: ArrayBuffer, isFinal: boolean) => void;

export class MicCapture {
  private process: ChildProcessWithoutNullStreams | undefined;
  private segmenter: SpeechSegmenter | undefined;

  start(onChunk: AudioChunkHandler): void {
    if (this.process) {
      throw new Error("MicCapture.start called while already recording");
    }

    const config = getVoiceConfig();

    this.segmenter = new SpeechSegmenter(
      {
        sampleRate: config.sampleRate,
        threshold: config.vadThreshold,
        silenceMs: config.vadSilenceMs,
      },
      (pcm) => {
        const wav = pcmToWav(pcm, { sampleRate: config.sampleRate, channels: 1, bitDepth: 16 });
        onChunk(toArrayBuffer(wav), true);
      }
    );

    const child = spawn(config.soxBin, [
      "-d", // default input device
      "-t",
      "raw",
      "-r",
      String(config.sampleRate),
      "-e",
      "signed",
      "-b",
      "16",
      "-c",
      "1",
      "-", // raw PCM to stdout
    ]);
    this.process = child;

    child.stdout.on("data", (data: Buffer) => {
      this.segmenter?.push(data);
    });
    child.on("error", (err) => {
      console.error("MicCapture: SoX process error", err);
    });
  }

  stop(): void {
    this.segmenter?.flush();
    this.segmenter = undefined;
    this.process?.kill();
    this.process = undefined;
  }
}

function toArrayBuffer(buffer: Buffer): ArrayBuffer {
  // Buffer's backing store is always a real ArrayBuffer in this codebase (never a
  // SharedArrayBuffer), but TS types .buffer as the wider ArrayBufferLike.
  return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength) as ArrayBuffer;
}
