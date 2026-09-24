/**
 * Streaming text-to-speech playback. Consumes explanation text chunks as they arrive
 * from agent.explanation.delta messages and starts playback incrementally, rather than
 * waiting for the full explanation.
 */

export interface TtsProvider {
  speakChunk(text: string): Promise<void>;
}
