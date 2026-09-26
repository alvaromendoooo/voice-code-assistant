/**
 * Loads the same repo-root `.env` file that `server/app/config.py` loads (shared,
 * gitignored), and reads the local STT/TTS tooling config from it. Binaries default to
 * assuming they're on PATH; model paths have no universal default location so they're
 * required. See docs/setup-voice-local.md for how to install/configure these.
 */

import * as path from "node:path";

import { config as loadDotenv } from "dotenv";

const REPO_ROOT_ENV_PATH = path.resolve(__dirname, "../../../.env");

let loaded = false;

function ensureEnvLoaded(): void {
  if (loaded) return;
  loadDotenv({ path: REPO_ROOT_ENV_PATH, override: false });
  loaded = true;
}

export interface VoiceConfig {
  soxBin: string;
  whisperBin: string;
  whisperModel: string;
  piperBin: string;
  piperModel: string;
  sampleRate: number;
  vadThreshold: number;
  vadSilenceMs: number;
}

export function getVoiceConfig(): VoiceConfig {
  ensureEnvLoaded();

  const whisperModel = process.env.VCA_WHISPER_MODEL;
  if (!whisperModel) {
    throw new Error("VCA_WHISPER_MODEL is not set (path to a whisper.cpp ggml model file)");
  }
  const piperModel = process.env.VCA_PIPER_MODEL;
  if (!piperModel) {
    throw new Error("VCA_PIPER_MODEL is not set (path to a Piper .onnx voice model file)");
  }

  return {
    soxBin: process.env.VCA_SOX_BIN ?? "sox",
    whisperBin: process.env.VCA_WHISPER_BIN ?? "whisper-cli",
    whisperModel,
    piperBin: process.env.VCA_PIPER_BIN ?? "piper",
    piperModel,
    sampleRate: Number(process.env.VCA_SAMPLE_RATE ?? "16000"),
    vadThreshold: Number(process.env.VCA_VAD_THRESHOLD ?? "500"),
    vadSilenceMs: Number(process.env.VCA_VAD_SILENCE_MS ?? "600"),
  };
}
