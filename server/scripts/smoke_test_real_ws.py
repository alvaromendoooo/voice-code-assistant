"""Real-socket smoke test: connects to an already-running uvicorn process over an
actual WebSocket (no TestClient/anyio portal involved), to rule out test-harness
threading artifacts. Start the server first:

    uv run uvicorn app.main:app --host 127.0.0.1 --port 8765

Then: uv run python -m scripts.smoke_test_real_ws
"""

from __future__ import annotations

import asyncio
import json

import websockets


async def main() -> None:
    async with websockets.connect("ws://127.0.0.1:8765/ws") as ws:
        await ws.send(
            json.dumps(
                {
                    "type": "voice.utterance",
                    "id": "utt-1",
                    "payload": {
                        "text": "Can you review this function?",
                        "is_final": True,
                        "context": {
                            "file_path": "src/foo.py",
                            "language": "python",
                            "selection": {"start_line": 1, "end_line": 2},
                            "cursor": {"line": 2, "col": 0},
                            "file_text": "def foo():\n    return 1\n",
                        },
                    },
                }
            )
        )

        proposal_id = None
        for _ in range(500):
            raw = await ws.recv()
            message = json.loads(raw)
            print(message)
            if message["type"] == "diff.proposed":
                proposal_id = message["payload"]["proposal_id"]
                break
            if message["type"] == "error":
                raise RuntimeError(f"server returned an error: {message}")
            if message["type"] == "agent.explanation.delta" and message["payload"]["done"]:
                # No edit was proposed for this utterance -- that's a valid outcome.
                print("\nno edit proposed; smoke test passed (explanation only)")
                return

        assert proposal_id is not None, "expected a diff.proposed message"

        await ws.send(
            json.dumps(
                {
                    "type": "diff.decision",
                    "id": "dec-1",
                    "payload": {"proposal_id": proposal_id, "decision": "accepted"},
                }
            )
        )

    print("\nsmoke test passed")


if __name__ == "__main__":
    asyncio.run(main())
