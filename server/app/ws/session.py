"""Per-connection WebSocket session: message dispatch loop.

Owns one AgentRuntime instance and one ChangelogStore per connected client. Does not
apply edits or touch the filesystem -- it only relays proposals/decisions between the
client and the agent runtime.
"""

from __future__ import annotations

import uuid

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

from app.agent.runtime import AgentRuntime
from app.changelog.changelog_store import ChangelogStore
from app.context_engine.file_context import EditorContextSnapshot
from app.diff.diff_service import build_unified_diff
from app.schemas.messages import (
    AgentExplanationDelta,
    AgentExplanationDeltaPayload,
    Diagnostic,
    DiffDecision,
    DiffProposed,
    DiffProposedPayload,
    ErrorMessage,
    ErrorPayload,
    SessionDiagnostics,
    VoiceUtterance,
)


class Session:
    def __init__(self, websocket: WebSocket, agent_runtime: AgentRuntime) -> None:
        self.session_id = str(uuid.uuid4())
        self._websocket = websocket
        self._agent_runtime = agent_runtime
        self._changelog = ChangelogStore(self.session_id)
        self._latest_diagnostics: dict[str, list[Diagnostic]] = {}

    async def run(self) -> None:
        """Accept the connection and dispatch incoming messages until disconnect."""
        await self._websocket.accept()
        try:
            while True:
                raw = await self._websocket.receive_json()
                await self._dispatch(raw)
        except WebSocketDisconnect:
            return

    async def _dispatch(self, raw: dict) -> None:
        message_id = raw.get("id")
        message_type = raw.get("type")
        try:
            if message_type == "voice.utterance":
                await self._handle_voice_utterance(VoiceUtterance.model_validate(raw))
            elif message_type == "diff.decision":
                await self._handle_diff_decision(DiffDecision.model_validate(raw))
            elif message_type == "session.diagnostics":
                await self._handle_session_diagnostics(
                    SessionDiagnostics.model_validate(raw)
                )
            else:
                await self._send_error(
                    message_id, "unknown_message_type", f"unrecognized type: {message_type!r}"
                )
        except ValidationError as exc:
            await self._send_error(message_id, "invalid_message", str(exc))

    async def _handle_voice_utterance(self, message: VoiceUtterance) -> None:
        raw_context = message.payload.context
        context = EditorContextSnapshot(
            file_path=raw_context.file_path,
            language=raw_context.language,
            file_text=raw_context.file_text,
            selection=(
                (raw_context.selection.start_line, raw_context.selection.end_line)
                if raw_context.selection
                else None
            ),
            cursor=(
                (raw_context.cursor.line, raw_context.cursor.col)
                if raw_context.cursor
                else None
            ),
        )

        chunks, proposal = await self._agent_runtime.handle_utterance(
            message.payload.text, context
        )

        for index, chunk in enumerate(chunks):
            await self._send(
                AgentExplanationDelta(
                    id=message.id,
                    payload=AgentExplanationDeltaPayload(
                        text=chunk, done=(index == len(chunks) - 1)
                    ),
                )
            )

        if proposal is not None:
            unified_diff = build_unified_diff(proposal)
            self._changelog.record_proposal(
                proposal_id=proposal.proposal_id,
                file_path=proposal.file_path,
                original_snippet=proposal.original_text,
                unified_diff=unified_diff,
                rationale=proposal.rationale,
            )
            await self._send(
                DiffProposed(
                    id=message.id,
                    payload=DiffProposedPayload(
                        proposal_id=proposal.proposal_id,
                        file_path=proposal.file_path,
                        unified_diff=unified_diff,
                        rationale=proposal.rationale,
                    ),
                )
            )

    async def _handle_diff_decision(self, message: DiffDecision) -> None:
        self._changelog.record_decision(
            message.payload.proposal_id, message.payload.decision
        )

    async def _handle_session_diagnostics(self, message: SessionDiagnostics) -> None:
        self._latest_diagnostics[message.payload.file_path] = message.payload.diagnostics

    async def _send(self, message: BaseModel) -> None:
        await self._websocket.send_json(message.model_dump(mode="json"))

    async def _send_error(self, message_id: str | None, code: str, text: str) -> None:
        await self._send(ErrorMessage(id=message_id, payload=ErrorPayload(code=code, message=text)))
