/**
 * WebSocket lifecycle: connect (with shared-token auth), send, and dispatch incoming
 * messages to registered handlers.
 *
 * Uses the `ws` package rather than a global WebSocket so behavior is consistent
 * across VS Code extension-host Node versions.
 */

import WebSocket from "ws";

import type { ClientToServerMessage, ServerToClientMessage } from "./messages";
import { fromWireMessage, toWireMessage } from "./wire-format";

export type ServerMessageHandler = (message: ServerToClientMessage) => void;

export interface SocketClientOptions {
  serverUrl: string;
  sharedToken: string;
}

export class SocketClient {
  private socket: WebSocket | undefined;
  private readonly handlers: ServerMessageHandler[] = [];

  constructor(private readonly options: SocketClientOptions) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const url = `${this.options.serverUrl}?token=${encodeURIComponent(this.options.sharedToken)}`;
      const socket = new WebSocket(url);
      this.socket = socket;

      const onOpen = () => {
        settle();
        resolve();
      };
      const onError = (err: Error) => {
        settle();
        reject(err);
      };
      const settle = () => {
        socket.off("open", onOpen);
        socket.off("error", onError);
      };

      socket.on("open", onOpen);
      socket.on("error", onError);
      socket.on("message", (data: WebSocket.RawData) => this.handleRawMessage(data));
      socket.on("close", () => {
        this.socket = undefined;
      });
    });
  }

  disconnect(): void {
    this.socket?.close();
    this.socket = undefined;
  }

  send(message: ClientToServerMessage): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error("SocketClient.send called while not connected");
    }
    this.socket.send(JSON.stringify(toWireMessage(message)));
  }

  onMessage(handler: ServerMessageHandler): void {
    this.handlers.push(handler);
  }

  private handleRawMessage(data: WebSocket.RawData): void {
    let parsed: unknown;
    try {
      parsed = JSON.parse(data.toString());
    } catch {
      return;
    }

    const message = fromWireMessage(parsed);
    if (!message) {
      return;
    }
    for (const handler of this.handlers) {
      handler(message);
    }
  }
}
