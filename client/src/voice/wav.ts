/**
 * Minimal RIFF/WAV header writer for raw PCM buffers. Used to wrap SoX's raw PCM stdout
 * into a file whisper.cpp can read, and to inspect what Piper/SoX produce in tests.
 */

export interface PcmFormat {
  sampleRate: number;
  channels: number;
  bitDepth: number;
}

export function pcmToWav(pcm: Buffer, format: PcmFormat): Buffer {
  const { sampleRate, channels, bitDepth } = format;
  const bytesPerSample = bitDepth / 8;
  const blockAlign = channels * bytesPerSample;
  const byteRate = sampleRate * blockAlign;
  const dataSize = pcm.length;

  const header = Buffer.alloc(44);
  header.write("RIFF", 0, "ascii");
  header.writeUInt32LE(36 + dataSize, 4);
  header.write("WAVE", 8, "ascii");
  header.write("fmt ", 12, "ascii");
  header.writeUInt32LE(16, 16); // fmt chunk size (PCM)
  header.writeUInt16LE(1, 20); // audio format: PCM
  header.writeUInt16LE(channels, 22);
  header.writeUInt32LE(sampleRate, 24);
  header.writeUInt32LE(byteRate, 28);
  header.writeUInt16LE(blockAlign, 32);
  header.writeUInt16LE(bitDepth, 34);
  header.write("data", 36, "ascii");
  header.writeUInt32LE(dataSize, 40);

  return Buffer.concat([header, pcm]);
}
