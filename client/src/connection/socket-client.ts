/**
 * WebSocket lifecycle: connect (with shared-token auth), send, and dispatch incoming
 * messages to registered handlers. Reconnect logic is a Phase 1 scaffold placeholder.
 */

import type { ClientToServerMessage, ServerToClientMessage } from "./messages";

export type ServerMessageHandler = (message: ServerToClientMessage) => void;

export interface SocketClientOptions {
  serverUrl: string;
  sharedToken: string;
}

export class SocketClient {
  constructor(private readonly options: SocketClientOptions) {}

  connect(): Promise<void> {
    throw new Error("not implemented");
  }

  disconnect(): void {
    throw new Error("not implemented");
  }

  send(message: ClientToServerMessage): void {
    throw new Error("not implemented");
  }

  onMessage(handler: ServerMessageHandler): void {
    throw new Error("not implemented");
  }
}
