import { describe, expect, it } from "vitest";

import { pcmToWav } from "./wav";

describe("pcmToWav", () => {
  it("writes a valid 44-byte RIFF/WAVE header followed by the PCM data", () => {
    const pcm = Buffer.from([1, 2, 3, 4]);
    const wav = pcmToWav(pcm, { sampleRate: 16000, channels: 1, bitDepth: 16 });

    expect(wav.length).toBe(44 + pcm.length);
    expect(wav.toString("ascii", 0, 4)).toBe("RIFF");
    expect(wav.toString("ascii", 8, 12)).toBe("WAVE");
    expect(wav.toString("ascii", 12, 16)).toBe("fmt ");
    expect(wav.toString("ascii", 36, 40)).toBe("data");
    expect(wav.subarray(44)).toEqual(pcm);
  });

  it("encodes sample rate, channel count, and derived byte rate/block align", () => {
    const pcm = Buffer.alloc(100);
    const wav = pcmToWav(pcm, { sampleRate: 22050, channels: 2, bitDepth: 16 });

    expect(wav.readUInt32LE(24)).toBe(22050); // sample rate
    expect(wav.readUInt16LE(22)).toBe(2); // channels
    expect(wav.readUInt16LE(34)).toBe(16); // bit depth
    expect(wav.readUInt16LE(32)).toBe(4); // block align: channels * bytesPerSample
    expect(wav.readUInt32LE(28)).toBe(22050 * 4); // byte rate
  });

  it("records the correct data and RIFF chunk sizes", () => {
    const pcm = Buffer.alloc(10);
    const wav = pcmToWav(pcm, { sampleRate: 16000, channels: 1, bitDepth: 16 });

    expect(wav.readUInt32LE(40)).toBe(10); // data chunk size
    expect(wav.readUInt32LE(4)).toBe(36 + 10); // RIFF chunk size
  });
});
