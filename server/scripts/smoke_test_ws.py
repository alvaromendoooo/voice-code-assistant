"""Manual smoke test for the Phase 1 WebSocket round-trip.

Exercises: voice.utterance -> agent.explanation.delta (x N) -> diff.proposed ->
diff.decision, against the in-process app (no server process needs to be running).

Run with: uv run python scripts/smoke_test_ws.py
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    client = TestClient(app)

    with client.websocket_connect("/ws") as ws:
        ws.send_json(
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

        proposal_id = None
        # Explanation streaming can arrive in many small chunks depending on the
        # provider (e.g. Ollama streams near-token-level), so cap on message count
        # generously rather than assuming a fixed number of chunks.
        for _ in range(500):
            message = ws.receive_json()
            print(message)
            if message["type"] == "diff.proposed":
                proposal_id = message["payload"]["proposal_id"]
                break
            if message["type"] == "error":
                raise RuntimeError(f"server returned an error: {message}")

        assert proposal_id is not None, "expected a diff.proposed message"

        ws.send_json(
            {
                "type": "diff.decision",
                "id": "dec-1",
                "payload": {"proposal_id": proposal_id, "decision": "accepted"},
            }
        )

    print("\nsmoke test passed")


if __name__ == "__main__":
    main()
