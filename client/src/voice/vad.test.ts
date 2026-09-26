import { describe, expect, it } from "vitest";

import { SpeechSegmenter } from "./vad";

const SAMPLE_RATE = 16000;
const FRAME_MS = 20;
const FRAME_SAMPLES = (SAMPLE_RATE * FRAME_MS) / 1000; // 320 samples -> 640 bytes

function toneFrame(amplitude: number): Buffer {
  const buf = Buffer.alloc(FRAME_SAMPLES * 2);
  for (let i = 0; i < FRAME_SAMPLES; i++) {
    buf.writeInt16LE(amplitude, i * 2);
  }
  return buf;
}

function silenceFrame(): Buffer {
  return toneFrame(0);
}

describe("SpeechSegmenter", () => {
  it("does not emit a segment for silence-only input", () => {
    const segments: Buffer[] = [];
    const segmenter = new SpeechSegmenter(
      { sampleRate: SAMPLE_RATE, threshold: 500, silenceMs: 200, frameMs: FRAME_MS },
      (pcm) => segments.push(pcm)
    );

    for (let i = 0; i < 20; i++) {
      segmenter.push(silenceFrame());
    }

    expect(segments).toHaveLength(0);
  });

  it("emits one finalized segment after speech is followed by sustained silence", () => {
    const segments: Buffer[] = [];
    const segmenter = new SpeechSegmenter(
      { sampleRate: SAMPLE_RATE, threshold: 500, silenceMs: 200, frameMs: FRAME_MS },
      (pcm) => segments.push(pcm)
    );

    // 5 frames of speech (100ms)
    for (let i = 0; i < 5; i++) {
      segmenter.push(toneFrame(10000));
    }
    // silenceMs=200 / frameMs=20 => 10 silence frames needed to close the segment
    for (let i = 0; i < 10; i++) {
      segmenter.push(silenceFrame());
    }

    expect(segments).toHaveLength(1);
    // segment includes the 5 speech frames plus the 10 trailing silence frames
    expect(segments[0].length).toBe(15 * FRAME_SAMPLES * 2);
  });

  it("does not finalize a segment while silence hangover has not yet elapsed", () => {
    const segments: Buffer[] = [];
    const segmenter = new SpeechSegmenter(
      { sampleRate: SAMPLE_RATE, threshold: 500, silenceMs: 200, frameMs: FRAME_MS },
      (pcm) => segments.push(pcm)
    );

    for (let i = 0; i < 5; i++) {
      segmenter.push(toneFrame(10000));
    }
    // only 5 silence frames (100ms), below the 200ms hangover threshold
    for (let i = 0; i < 5; i++) {
      segmenter.push(silenceFrame());
    }

    expect(segments).toHaveLength(0);
  });

  it("flush() finalizes an in-progress segment", () => {
    const segments: Buffer[] = [];
    const segmenter = new SpeechSegmenter(
      { sampleRate: SAMPLE_RATE, threshold: 500, silenceMs: 200, frameMs: FRAME_MS },
      (pcm) => segments.push(pcm)
    );

    for (let i = 0; i < 3; i++) {
      segmenter.push(toneFrame(10000));
    }
    segmenter.flush();

    expect(segments).toHaveLength(1);
    expect(segments[0].length).toBe(3 * FRAME_SAMPLES * 2);
  });

  it("handles chunk boundaries that don't align with frame size", () => {
    const segments: Buffer[] = [];
    const segmenter = new SpeechSegmenter(
      { sampleRate: SAMPLE_RATE, threshold: 500, silenceMs: 200, frameMs: FRAME_MS },
      (pcm) => segments.push(pcm)
    );

    const speech = Buffer.concat([toneFrame(10000), toneFrame(10000)]);
    // split into uneven chunks, not aligned to the 640-byte frame size
    segmenter.push(speech.subarray(0, 100));
    segmenter.push(speech.subarray(100, 900));
    segmenter.push(speech.subarray(900));
    segmenter.flush();

    expect(segments).toHaveLength(1);
    expect(segments[0].length).toBe(2 * FRAME_SAMPLES * 2);
  });
});
