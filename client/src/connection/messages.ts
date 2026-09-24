/**
 * WebSocket message schema, mirrored from server/app/schemas/messages.py.
 * Keep both in sync manually for Phase 1 -- see docs/architecture/phase1-design.md.
 *
 * Provider identity (STT/TTS/LLM vendor) is intentionally absent from every payload:
 * the agent's behavior depends only on message content, not on which provider produced
 * or will consume it.
 */

export interface Selection {
  startLine: number;
  endLine: number;
}

export interface Cursor {
  line: number;
  col: number;
}

export interface EditorContext {
  filePath: string;
  language: string;
  selection?: Selection;
  cursor?: Cursor;
  fileText: string;
}

export interface Diagnostic {
  severity: "error" | "warning" | "info" | "hint";
  line: number;
  message: string;
}

// ---- client -> server ----

export interface VoiceUtterance {
  type: "voice.utterance";
  id: string;
  payload: {
    text: string;
    isFinal: boolean;
    context: EditorContext;
  };
}

export interface DiffDecision {
  type: "diff.decision";
  id: string;
  payload: {
    proposalId: string;
    decision: "accepted" | "rejected";
  };
}

export interface SessionDiagnostics {
  type: "session.diagnostics";
  payload: {
    filePath: string;
    diagnostics: Diagnostic[];
  };
}

export type ClientToServerMessage = VoiceUtterance | DiffDecision | SessionDiagnostics;

// ---- server -> client ----

export interface AgentExplanationDelta {
  type: "agent.explanation.delta";
  id: string;
  payload: {
    text: string;
    done: boolean;
  };
}

export interface DiffProposed {
  type: "diff.proposed";
  id: string;
  payload: {
    proposalId: string;
    filePath: string;
    unifiedDiff: string;
    rationale: string;
  };
}

export interface ErrorMessage {
  type: "error";
  id?: string;
  payload: {
    code: string;
    message: string;
  };
}

export type ServerToClientMessage = AgentExplanationDelta | DiffProposed | ErrorMessage;
