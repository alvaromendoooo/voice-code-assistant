import { EventEmitter } from "node:events";

import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("node:child_process", () => ({ spawn: vi.fn() }));
vi.mock("node:fs/promises", () => ({ rm: vi.fn() }));
vi.mock("./config", () => ({
  getVoiceConfig: vi.fn(() => ({
    soxBin: "sox-test",
    whisperBin: "whisper-test",
    whisperModel: "/models/whisper.bin",
    piperBin: "piper-test",
    piperModel: "/models/piper.onnx",
    sampleRate: 16000,
    vadThreshold: 500,
    vadSilenceMs: 600,
  })),
}));

import { spawn } from "node:child_process";
import * as fs from "node:fs/promises";

import { PiperTtsProvider } from "./tts";

function fakeChild() {
  const child = new EventEmitter() as EventEmitter & {
    stderr: EventEmitter;
    stdin: { write: ReturnType<typeof vi.fn>; end: ReturnType<typeof vi.fn> };
  };
  child.stderr = new EventEmitter();
  child.stdin = { write: vi.fn(), end: vi.fn() };
  return child;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("PiperTtsProvider", () => {
  it("pipes text to piper via stdin, then plays the resulting wav via sox, in order", async () => {
    const piperChild = fakeChild();
    const soxChild = fakeChild();
    const spawnMock = spawn as unknown as ReturnType<typeof vi.fn>;
    spawnMock.mockReturnValueOnce(piperChild).mockReturnValueOnce(soxChild);

    const provider = new PiperTtsProvider();
    const promise = provider.speakChunk("hello there");

    await Promise.resolve();
    await Promise.resolve();
    expect(piperChild.stdin.write).toHaveBeenCalledWith("hello there");
    expect(piperChild.stdin.end).toHaveBeenCalled();
    piperChild.emit("close", 0);

    // sox is only spawned after piper finishes
    await Promise.resolve();
    await Promise.resolve();
    expect(spawnMock).toHaveBeenCalledTimes(2);
    soxChild.emit("close", 0);

    await promise;

    const [piperBin, piperArgs] = spawnMock.mock.calls[0];
    expect(piperBin).toBe("piper-test");
    expect(piperArgs).toContain("--model");
    expect(piperArgs).toContain("/models/piper.onnx");

    const [soxBin, soxArgs] = spawnMock.mock.calls[1];
    expect(soxBin).toBe("sox-test");
    expect(soxArgs).toContain("-d");

    expect(fs.rm).toHaveBeenCalledTimes(1); // temp wav cleaned up
  });

  it("rejects when piper exits with a non-zero code and never spawns sox", async () => {
    const piperChild = fakeChild();
    (spawn as unknown as ReturnType<typeof vi.fn>).mockReturnValue(piperChild);

    const provider = new PiperTtsProvider();
    const promise = provider.speakChunk("hello");

    await Promise.resolve();
    piperChild.emit("close", 1);

    await expect(promise).rejects.toThrow(/piper exited with code 1/);
    expect(spawn).toHaveBeenCalledTimes(1);
  });
});
