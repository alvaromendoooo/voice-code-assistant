/**
 * Streaming speech-to-text provider adapter.
 * Provider choice (local vs. cloud streaming API) is an internal detail here and does
 * not affect the WebSocket schema -- only plain transcribed text crosses the wire.
 */

export interface SttProvider {
  transcribeChunk(audioChunk: ArrayBuffer, isFinal: boolean): Promise<string>;
}
