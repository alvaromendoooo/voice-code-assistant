import { EventEmitter } from "node:events";

import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("node:child_process", () => ({ spawn: vi.fn() }));
vi.mock("node:fs/promises", () => ({
  writeFile: vi.fn(),
  readFile: vi.fn(),
  rm: vi.fn(),
}));
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

import { WhisperCppSttProvider } from "./stt";

function fakeChild() {
  const child = new EventEmitter() as EventEmitter & { stderr: EventEmitter };
  child.stderr = new EventEmitter();
  return child;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("WhisperCppSttProvider", () => {
  it("returns an empty string for non-final chunks without spawning anything", async () => {
    const provider = new WhisperCppSttProvider();

    const result = await provider.transcribeChunk(new ArrayBuffer(8), false);

    expect(result).toBe("");
    expect(spawn).not.toHaveBeenCalled();
  });

  it("writes the chunk to a temp wav, invokes whisper.cpp, and returns the trimmed transcript", async () => {
    const child = fakeChild();
    (spawn as unknown as ReturnType<typeof vi.fn>).mockReturnValue(child);
    (fs.readFile as unknown as ReturnType<typeof vi.fn>).mockResolvedValue("  hello world\n");

    const provider = new WhisperCppSttProvider();
    const promise = provider.transcribeChunk(new ArrayBuffer(16), true);

    // let the writeFile/spawn microtasks run, then simulate a clean exit
    await Promise.resolve();
    await Promise.resolve();
    child.emit("close", 0);

    const result = await promise;

    expect(result).toBe("hello world");
    expect(spawn).toHaveBeenCalledTimes(1);
    const [bin, args] = (spawn as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(bin).toBe("whisper-test");
    expect(args).toContain("-m");
    expect(args).toContain("/models/whisper.bin");
    expect(args).toContain("-otxt");
    expect(fs.writeFile).toHaveBeenCalledTimes(1);
    expect(fs.rm).toHaveBeenCalledTimes(2); // wav + txt cleanup
  });

  it("rejects when whisper.cpp exits with a non-zero code", async () => {
    const child = fakeChild();
    (spawn as unknown as ReturnType<typeof vi.fn>).mockReturnValue(child);

    const provider = new WhisperCppSttProvider();
    const promise = provider.transcribeChunk(new ArrayBuffer(16), true);

    await Promise.resolve();
    await Promise.resolve();
    child.stderr.emit("data", Buffer.from("boom"));
    child.emit("close", 1);

    await expect(promise).rejects.toThrow(/whisper.cpp exited with code 1/);
    expect(fs.rm).toHaveBeenCalledTimes(2); // cleanup still happens on error
  });
});
