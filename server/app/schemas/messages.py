"""WebSocket message schema, as specified in docs/architecture/phase1-design.md.

Provider identity (STT/TTS/LLM vendor) is intentionally absent from every payload here:
the agent's behavior depends only on message content, not on which provider produced or
will consume it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


# ---- shared value types -----------------------------------------------------

class Selection(BaseModel):
    start_line: int
    end_line: int


class Cursor(BaseModel):
    line: int
    col: int


class EditorContext(BaseModel):
    file_path: str
    language: str
    selection: Selection | None = None
    cursor: Cursor | None = None
    file_text: str


class Diagnostic(BaseModel):
    severity: Literal["error", "warning", "info", "hint"]
    line: int
    message: str


# ---- client -> server ---------------------------------------------------------

class VoiceUtterancePayload(BaseModel):
    text: str
    is_final: bool
    context: EditorContext


class VoiceUtterance(BaseModel):
    type: Literal["voice.utterance"] = "voice.utterance"
    id: str
    payload: VoiceUtterancePayload


class DiffDecisionPayload(BaseModel):
    proposal_id: str
    decision: Literal["accepted", "rejected"]


class DiffDecision(BaseModel):
    type: Literal["diff.decision"] = "diff.decision"
    id: str
    payload: DiffDecisionPayload


class SessionDiagnosticsPayload(BaseModel):
    file_path: str
    diagnostics: list[Diagnostic]


class SessionDiagnostics(BaseModel):
    type: Literal["session.diagnostics"] = "session.diagnostics"
    payload: SessionDiagnosticsPayload


# ---- server -> client ---------------------------------------------------------

class AgentExplanationDeltaPayload(BaseModel):
    text: str
    done: bool


class AgentExplanationDelta(BaseModel):
    type: Literal["agent.explanation.delta"] = "agent.explanation.delta"
    id: str
    payload: AgentExplanationDeltaPayload


class DiffProposedPayload(BaseModel):
    proposal_id: str
    file_path: str
    unified_diff: str
    rationale: str


class DiffProposed(BaseModel):
    type: Literal["diff.proposed"] = "diff.proposed"
    id: str
    payload: DiffProposedPayload


class ErrorPayload(BaseModel):
    code: str
    message: str


class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    id: str | None = None
    payload: ErrorPayload
