/**
 * Converts between the idiomatic-camelCase TypeScript message types (messages.ts) and
 * the snake_case JSON actually sent on the wire, which matches the Python/pydantic
 * schema in server/app/schemas/messages.py verbatim (e.g. `is_final`, `file_path`,
 * `proposal_id`). Keeping the TS-facing types camelCase avoids fighting TS lint/style
 * conventions everywhere else in this module while still producing wire-correct JSON.
 */

import type {
  ClientToServerMessage,
  Cursor,
  EditorContext,
  ServerToClientMessage,
  Selection,
} from "./messages";

function selectionToWire(selection?: Selection) {
  if (!selection) return undefined;
  return { start_line: selection.startLine, end_line: selection.endLine };
}

function cursorToWire(cursor?: Cursor) {
  if (!cursor) return undefined;
  return { line: cursor.line, col: cursor.col };
}

function editorContextToWire(context: EditorContext) {
  return {
    file_path: context.filePath,
    language: context.language,
    selection: selectionToWire(context.selection),
    cursor: cursorToWire(context.cursor),
    file_text: context.fileText,
  };
}

export function toWireMessage(message: ClientToServerMessage): unknown {
  switch (message.type) {
    case "voice.utterance":
      return {
        type: message.type,
        id: message.id,
        payload: {
          text: message.payload.text,
          is_final: message.payload.isFinal,
          context: editorContextToWire(message.payload.context),
        },
      };
    case "diff.decision":
      return {
        type: message.type,
        id: message.id,
        payload: {
          proposal_id: message.payload.proposalId,
          decision: message.payload.decision,
        },
      };
    case "session.diagnostics":
      return {
        type: message.type,
        payload: {
          file_path: message.payload.filePath,
          diagnostics: message.payload.diagnostics,
        },
      };
  }
}

export function fromWireMessage(raw: unknown): ServerToClientMessage | undefined {
  if (typeof raw !== "object" || raw === null || !("type" in raw)) {
    return undefined;
  }
  const message = raw as { type: string; id?: string; payload: Record<string, unknown> };

  switch (message.type) {
    case "agent.explanation.delta":
      return {
        type: "agent.explanation.delta",
        id: message.id as string,
        payload: {
          text: message.payload.text as string,
          done: message.payload.done as boolean,
        },
      };
    case "diff.proposed":
      return {
        type: "diff.proposed",
        id: message.id as string,
        payload: {
          proposalId: message.payload.proposal_id as string,
          filePath: message.payload.file_path as string,
          unifiedDiff: message.payload.unified_diff as string,
          rationale: message.payload.rationale as string,
        },
      };
    case "error":
      return {
        type: "error",
        id: message.id,
        payload: {
          code: message.payload.code as string,
          message: message.payload.message as string,
        },
      };
    default:
      return undefined;
  }
}
