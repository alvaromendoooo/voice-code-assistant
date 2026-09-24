/**
 * Status bar indicator for connection state and recording state.
 */

export type ConnectionState = "disconnected" | "connecting" | "connected";
export type RecordingState = "idle" | "listening";

export class StatusBar {
  setConnectionState(state: ConnectionState): void {
    throw new Error("not implemented");
  }

  setRecordingState(state: RecordingState): void {
    throw new Error("not implemented");
  }
}
