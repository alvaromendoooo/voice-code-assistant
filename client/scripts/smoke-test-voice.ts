/**
 * Manual smoke test for the local voice stack: records a few seconds via MicCapture,
 * transcribes the finalized segment via WhisperCppSttProvider, prints the text, then
 * speaks a canned reply via PiperTtsProvider. Needs real SoX/whisper.cpp/Piper binaries
 * and a working microphone/speakers -- see docs/setup-voice-local.md. Not run in CI.
 *
 * Usage (from client/): npx tsx scripts/smoke-test-voice.ts
 */

import { MicCapture } from "../src/voice/mic-capture";
import { WhisperCppSttProvider } from "../src/voice/stt";
import { PiperTtsProvider } from "../src/voice/tts";

async function main(): Promise<void> {
  const mic = new MicCapture();
  const stt = new WhisperCppSttProvider();
  const tts = new PiperTtsProvider();

  console.log("Speak now, then pause...");

  const transcript = await new Promise<string>((resolve, reject) => {
    mic.start((chunk, isFinal) => {
      if (!isFinal) return;
      mic.stop();
      stt.transcribeChunk(chunk, true).then(resolve, reject);
    });
  });

  console.log(`Transcribed: "${transcript}"`);

  const reply = transcript.length > 0 ? `You said: ${transcript}` : "I didn't catch that.";
  await tts.speakChunk(reply);

  console.log("smoke test passed");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
