/**
 * Streaming speech-to-text provider adapter.
 * Provider choice (local vs. cloud streaming API) is an internal detail here and does
 * not affect the WebSocket schema -- only plain transcribed text crosses the wire.
 */

import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";

import { getVoiceConfig } from "./config";

export interface SttProvider {
  transcribeChunk(audioChunk: ArrayBuffer, isFinal: boolean): Promise<string>;
}

/**
 * Transcribes finalized WAV segments via a local whisper.cpp CLI binary. Writes the
 * transcript to a `.txt` file via `-otxt` rather than parsing stdout, since stdout also
 * carries progress/log noise that varies across whisper.cpp builds/versions.
 */
export class WhisperCppSttProvider implements SttProvider {
  async transcribeChunk(audioChunk: ArrayBuffer, isFinal: boolean): Promise<string> {
    if (!isFinal) {
      // MVP transcribes only finalized VAD segments; voice.utterance carries one full
      // text per utterance, not interim deltas (see docs/architecture/phase1-design.md).
      return "";
    }

    const config = getVoiceConfig();
    const base = path.join(os.tmpdir(), `vca-stt-${randomUUID()}`);
    const wavPath = `${base}.wav`;
    const txtPath = `${base}.txt`;

    try {
      await fs.writeFile(wavPath, Buffer.from(audioChunk));
      await runWhisper(config.whisperBin, config.whisperModel, wavPath, base);
      const text = await fs.readFile(txtPath, "utf8");
      return text.trim();
    } finally {
      await fs.rm(wavPath, { force: true });
      await fs.rm(txtPath, { force: true });
    }
  }
}

function runWhisper(bin: string, model: string, wavPath: string, outputBase: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const child = spawn(bin, ["-m", model, "-f", wavPath, "-otxt", "-of", outputBase, "-nt"]);
    let stderr = "";

    child.stderr?.on("data", (chunk: Buffer) => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`whisper.cpp exited with code ${code}: ${stderr}`));
      }
    });
  });
}
