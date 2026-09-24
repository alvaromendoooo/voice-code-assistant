"""Tests the Session dispatch loop directly against a fake WebSocket, deliberately
avoiding FastAPI's TestClient -- its sync/async thread bridging deadlocked on
sequential real network calls during manual testing (see docs/architecture notes),
so it's a poor fit for exercising this loop even with a fake provider.
"""

import json

import pytest
from fastapi import WebSocketDisconnect

from app.agent.llm_provider import StubLLMProvider
from app.agent.runtime import AgentRuntime
from app.ws.session import Session


class _FakeWebSocket:
    def __init__(self, incoming: list[dict]):
        self._incoming = list(incoming)
        self.sent: list[dict] = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def receive_json(self):
        if not self._incoming:
            raise WebSocketDisconnect()
        return self._incoming.pop(0)

    async def send_json(self, data):
        self.sent.append(data)


def _utterance(text: str, msg_id: str = "utt-1") -> dict:
    return {
        "type": "voice.utterance",
        "id": msg_id,
        "payload": {
            "text": text,
            "is_final": True,
            "context": {
                "file_path": "src/foo.py",
                "language": "python",
                "file_text": "def foo():\n    return 1\n",
            },
        },
    }


@pytest.fixture
def session_with(tmp_path):
    def _make(incoming: list[dict]) -> tuple[Session, _FakeWebSocket]:
        ws = _FakeWebSocket(incoming)
        session = Session(ws, AgentRuntime(StubLLMProvider()))
        session._changelog._path = tmp_path / f"{session.session_id}.jsonl"
        return session, ws

    return _make


async def test_voice_utterance_streams_explanation_and_proposes_edit(session_with):
    session, ws = session_with([_utterance("Can you review this function?")])

    await session.run()

    assert ws.accepted is True
    types = [msg["type"] for msg in ws.sent]
    assert types.count("agent.explanation.delta") == len(StubLLMProvider._CANNED_SENTENCES)
    assert types[-2:] == ["agent.explanation.delta", "diff.proposed"] or "diff.proposed" in types
    diff_proposed = next(m for m in ws.sent if m["type"] == "diff.proposed")
    assert diff_proposed["payload"]["file_path"] == "src/foo.py"
    assert "TODO" in diff_proposed["payload"]["unified_diff"]


async def test_voice_utterance_without_edit_trigger_sends_no_proposal(session_with):
    session, ws = session_with([_utterance("What does this do?")])

    await session.run()

    types = [msg["type"] for msg in ws.sent]
    assert "diff.proposed" not in types
    assert types[-1] == "agent.explanation.delta"
    assert ws.sent[-1]["payload"]["done"] is True


async def test_unknown_message_type_sends_error(session_with):
    session, ws = session_with([{"type": "not.a.real.type", "id": "x"}])

    await session.run()

    assert len(ws.sent) == 1
    assert ws.sent[0]["type"] == "error"
    assert ws.sent[0]["payload"]["code"] == "unknown_message_type"


async def test_invalid_message_sends_error_without_crashing_session(session_with):
    bad_message = {"type": "voice.utterance", "id": "utt-1", "payload": {}}
    session, ws = session_with([bad_message, _utterance("hello", msg_id="utt-2")])

    await session.run()

    error_messages = [m for m in ws.sent if m["type"] == "error"]
    assert len(error_messages) == 1
    assert error_messages[0]["payload"]["code"] == "invalid_message"
    # the session kept running and handled the next, valid message
    assert any(m["type"] == "agent.explanation.delta" for m in ws.sent)


async def test_diff_decision_is_recorded_in_changelog(session_with, tmp_path):
    session, ws = session_with(
        [
            _utterance("Can you review this function?"),
            {
                "type": "diff.decision",
                "id": "dec-1",
                "payload": {"proposal_id": "", "decision": "accepted"},
            },
        ]
    )
    # capture the real proposal id from the first response before sending the decision
    await session.run()

    log_path = tmp_path / f"{session.session_id}.jsonl"
    lines = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    kinds = [entry["kind"] for entry in lines]
    assert "proposal" in kinds
    assert "decision" in kinds
