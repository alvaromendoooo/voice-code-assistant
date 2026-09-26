# Local voice setup (STT/TTS)

The client's `client/src/voice/` modules use fully local, free tooling for speech-to-text
and text-to-speech — no cloud API keys, no rate limits:

- **SoX** — microphone recording and audio playback.
- **whisper.cpp** — speech-to-text (`WhisperCppSttProvider`).
- **Piper** — text-to-speech (`PiperTtsProvider`).

None of these are bundled with the repo; each is a one-time manual install.

## 1. SoX

Download from https://sourceforge.net/projects/sox/ (Windows) or install via your package
manager (`apt install sox`, `brew install sox`). Confirm `sox` is on `PATH`:

```
sox --version
```

## 2. whisper.cpp

Build or download a `whisper-cli`/`main` binary from
https://github.com/ggml-org/whisper.cpp, and download a ggml model (e.g.
`ggml-base.en.bin`) from the same repo's model links. Note the binary and model paths.

## 3. Piper

Download a prebuilt Piper release for your platform from
https://github.com/OHF-Voice/piper1-gpl (or the original rhasspy/piper release page), and a
voice model (e.g. `en_US-lessac-medium.onnx`, with its accompanying `.onnx.json` in the
same directory). Note the binary and model paths.

## 4. Configure

Add these to the repo-root `.env` (same file `server/app/config.py` already loads —
gitignored, never commit real values):

```
VCA_WHISPER_MODEL=C:\path\to\ggml-base.en.bin
VCA_PIPER_MODEL=C:\path\to\en_US-lessac-medium.onnx

# optional overrides -- defaults shown
VCA_SOX_BIN=sox
VCA_WHISPER_BIN=whisper-cli
VCA_PIPER_BIN=piper
VCA_SAMPLE_RATE=16000
VCA_VAD_THRESHOLD=500
VCA_VAD_SILENCE_MS=600
```

`VCA_SOX_BIN`, `VCA_WHISPER_BIN`, and `VCA_PIPER_BIN` only need to be set if the binary
isn't on `PATH`; point them at the full executable path otherwise.

## 5. Verify

```
cd client
npm install
npm test
```

For an end-to-end check with real hardware (mic + speakers), run
`client/scripts/smoke-test-voice.ts` — it records a few seconds of speech, transcribes it,
prints the text, then speaks a canned reply back.
