import { EventEmitter } from "node:events";

import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("node:child_process", () => ({ spawn: vi.fn() }));
vi.mock("./config", () => ({
  getVoiceConfig: vi.fn(() => ({
    soxBin: "sox-test",
    whisperBin: "whisper-test",
    whisperModel: "/models/whisper.bin",
    piperBin: "piper-test",
    piperModel: "/models/piper.onnx",
    sampleRate: 16000,
    vadThreshold: 500,
    vadSilenceMs: 200,
  })),
}));

import { spawn } from "node:child_process";

import { MicCapture } from "./mic-capture";

const FRAME_SAMPLES = 320; // 20ms at 16kHz

function toneFrame(amplitude: number): Buffer {
  const buf = Buffer.alloc(FRAME_SAMPLES * 2);
  for (let i = 0; i < FRAME_SAMPLES; i++) {
    buf.writeInt16LE(amplitude, i * 2);
  }
  return buf;
}

function fakeChild() {
  const child = new EventEmitter() as EventEmitter & {
    stdout: EventEmitter;
    kill: ReturnType<typeof vi.fn>;
  };
  child.stdout = new EventEmitter();
  child.kill = vi.fn();
  return child;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("MicCapture", () => {
  it("spawns sox with the configured sample rate and streams stdout into onChunk", () => {
    const child = fakeChild();
    (spawn as unknown as ReturnType<typeof vi.fn>).mockReturnValue(child);

    const chunks: { buf: ArrayBuffer; isFinal: boolean }[] = [];
    const mic = new MicCapture();
    mic.start((buf, isFinal) => chunks.push({ buf, isFinal }));

    const [bin, args] = (spawn as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(bin).toBe("sox-test");
    expect(args).toContain("-r");
    expect(args).toContain("16000");

    // 5 speech frames then 10 silence frames (200ms hangover at 20ms/frame)
    for (let i = 0; i < 5; i++) {
      child.stdout.emit("data", toneFrame(10000));
    }
    for (let i = 0; i < 10; i++) {
      child.stdout.emit("data", toneFrame(0));
    }

    expect(chunks).toHaveLength(1);
    expect(chunks[0].isFinal).toBe(true);
    // 44-byte WAV header + (5 + 10) frames of PCM
    expect(chunks[0].buf.byteLength).toBe(44 + 15 * FRAME_SAMPLES * 2);
  });

  it("stop() flushes any in-progress segment and kills the sox process", () => {
    const child = fakeChild();
    (spawn as unknown as ReturnType<typeof vi.fn>).mockReturnValue(child);

    const chunks: { buf: ArrayBuffer; isFinal: boolean }[] = [];
    const mic = new MicCapture();
    mic.start((buf, isFinal) => chunks.push({ buf, isFinal }));

    for (let i = 0; i < 3; i++) {
      child.stdout.emit("data", toneFrame(10000));
    }

    mic.stop();

    expect(chunks).toHaveLength(1);
    expect(child.kill).toHaveBeenCalledTimes(1);
  });

  it("throws if start() is called while already recording", () => {
    const child = fakeChild();
    (spawn as unknown as ReturnType<typeof vi.fn>).mockReturnValue(child);

    const mic = new MicCapture();
    mic.start(() => {});

    expect(() => mic.start(() => {})).toThrow(/already recording/);
  });
});
