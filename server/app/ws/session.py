"""Per-connection WebSocket session: message dispatch loop.

Owns one AgentRuntime instance and one ChangelogStore per connected client. Does not
apply edits or touch the filesystem -- it only relays proposals/decisions between the
client and the agent runtime.
"""

from __future__ import annotations

import uuid

from fastapi import WebSocket

from app.agent.runtime import AgentRuntime
from app.changelog.changelog_store import ChangelogStore
from app.schemas.messages import (
    DiffDecision,
    SessionDiagnostics,
    VoiceUtterance,
)


class Session:
    def __init__(self, websocket: WebSocket, agent_runtime: AgentRuntime) -> None:
        self.session_id = str(uuid.uuid4())
        self._websocket = websocket
        self._agent_runtime = agent_runtime
        self._changelog = ChangelogStore(self.session_id)

    async def run(self) -> None:
        """Accept the connection and dispatch incoming messages until disconnect."""
        raise NotImplementedError

    async def _handle_voice_utterance(self, message: VoiceUtterance) -> None:
        raise NotImplementedError

    async def _handle_diff_decision(self, message: DiffDecision) -> None:
        raise NotImplementedError

    async def _handle_session_diagnostics(self, message: SessionDiagnostics) -> None:
        raise NotImplementedError
