/**
 * Manual smoke test for the client<->server WebSocket connection, run against a real
 * uvicorn process (not FastAPI's in-process TestClient, which the server-side smoke
 * test already covers). Validates that SocketClient can actually connect, send a
 * voice.utterance, and receive the expected agent.explanation.delta / diff.proposed
 * sequence with correct field-name translation to/from the Python wire format.
 *
 * Usage: node dist/../scripts-dist/smoke-test.js (see client/README-less inline notes
 * below -- compiled via `npx tsc scripts/smoke-test.ts --outDir scripts-dist
 * --module commonjs --target ES2022 --esModuleInterop`), with the server already
 * running at ws://127.0.0.1:8765/ws.
 */

import { SocketClient } from "../src/connection/socket-client";
import type { ServerToClientMessage } from "../src/connection/messages";

async function main(): Promise<void> {
  const client = new SocketClient({
    serverUrl: "ws://127.0.0.1:8765/ws",
    sharedToken: "unused-in-phase1-local-dev",
  });

  const received: ServerToClientMessage[] = [];
  client.onMessage((message) => {
    received.push(message);
    console.log(JSON.stringify(message));
  });

  await client.connect();
  console.log("connected");

  client.send({
    type: "voice.utterance",
    id: "utt-1",
    payload: {
      text: "Can you review this function?",
      isFinal: true,
      context: {
        filePath: "src/foo.py",
        language: "python",
        selection: { startLine: 1, endLine: 2 },
        cursor: { line: 2, col: 0 },
        fileText: "def foo():\n    return 1\n",
      },
    },
  });

  const proposal = await waitFor(received, (m) => m.type === "diff.proposed");
  if (proposal.type !== "diff.proposed") {
    throw new Error("expected diff.proposed");
  }

  client.send({
    type: "diff.decision",
    id: "dec-1",
    payload: { proposalId: proposal.payload.proposalId, decision: "accepted" },
  });

  await sleep(200);
  client.disconnect();
  console.log("smoke test passed");
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitFor(
  received: ServerToClientMessage[],
  predicate: (m: ServerToClientMessage) => boolean,
  timeoutMs = 5000
): Promise<ServerToClientMessage> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const found = received.find(predicate);
    if (found) return found;
    await sleep(20);
  }
  throw new Error("timed out waiting for expected message");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
