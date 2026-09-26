/**
 * Streaming text-to-speech playback. Consumes explanation text chunks as they arrive
 * from agent.explanation.delta messages and starts playback incrementally, rather than
 * waiting for the full explanation.
 */

import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";

import { getVoiceConfig } from "./config";

export interface TtsProvider {
  speakChunk(text: string): Promise<void>;
}

/**
 * Synthesizes speech via a local Piper CLI binary and plays it back via SoX. speakChunk
 * resolves only once playback finishes, so sequential chunks don't overlap.
 */
export class PiperTtsProvider implements TtsProvider {
  async speakChunk(text: string): Promise<void> {
    const config = getVoiceConfig();
    const outPath = path.join(os.tmpdir(), `vca-tts-${randomUUID()}.wav`);

    try {
      await runPiper(config.piperBin, config.piperModel, text, outPath);
      await playWav(config.soxBin, outPath);
    } finally {
      await fs.rm(outPath, { force: true });
    }
  }
}

function runPiper(bin: string, model: string, text: string, outPath: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const child = spawn(bin, ["--model", model, "--output_file", outPath]);
    let stderr = "";

    child.stderr?.on("data", (chunk: Buffer) => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`piper exited with code ${code}: ${stderr}`));
      }
    });

    child.stdin.write(text);
    child.stdin.end();
  });
}

function playWav(soxBin: string, wavPath: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const child = spawn(soxBin, [wavPath, "-d"]);
    let stderr = "";

    child.stderr?.on("data", (chunk: Buffer) => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`sox playback exited with code ${code}: ${stderr}`));
      }
    });
  });
}
