import { describe, expect, it } from "vitest";

import { fromWireMessage, toWireMessage } from "./wire-format";
import type {
  DiffDecision,
  SessionDiagnostics,
  VoiceUtterance,
} from "./messages";

describe("toWireMessage", () => {
  it("converts a voice.utterance to snake_case wire format", () => {
    const message: VoiceUtterance = {
      type: "voice.utterance",
      id: "utt-1",
      payload: {
        text: "review this",
        isFinal: true,
        context: {
          filePath: "src/foo.py",
          language: "python",
          selection: { startLine: 1, endLine: 2 },
          cursor: { line: 2, col: 4 },
          fileText: "def foo(): pass",
        },
      },
    };

    expect(toWireMessage(message)).toEqual({
      type: "voice.utterance",
      id: "utt-1",
      payload: {
        text: "review this",
        is_final: true,
        context: {
          file_path: "src/foo.py",
          language: "python",
          selection: { start_line: 1, end_line: 2 },
          cursor: { line: 2, col: 4 },
          file_text: "def foo(): pass",
        },
      },
    });
  });

  it("omits selection and cursor from the wire payload when absent", () => {
    const message: VoiceUtterance = {
      type: "voice.utterance",
      id: "utt-1",
      payload: {
        text: "hi",
        isFinal: false,
        context: {
          filePath: "src/foo.py",
          language: "python",
          fileText: "x = 1",
        },
      },
    };

    const wire = toWireMessage(message) as { payload: { context: Record<string, unknown> } };

    expect(wire.payload.context.selection).toBeUndefined();
    expect(wire.payload.context.cursor).toBeUndefined();
  });

  it("converts a diff.decision to snake_case wire format", () => {
    const message: DiffDecision = {
      type: "diff.decision",
      id: "dec-1",
      payload: { proposalId: "p-123", decision: "accepted" },
    };

    expect(toWireMessage(message)).toEqual({
      type: "diff.decision",
      id: "dec-1",
      payload: { proposal_id: "p-123", decision: "accepted" },
    });
  });

  it("converts session.diagnostics to snake_case wire format", () => {
    const message: SessionDiagnostics = {
      type: "session.diagnostics",
      payload: {
        filePath: "src/foo.py",
        diagnostics: [{ severity: "error", line: 3, message: "boom" }],
      },
    };

    expect(toWireMessage(message)).toEqual({
      type: "session.diagnostics",
      payload: {
        file_path: "src/foo.py",
        diagnostics: [{ severity: "error", line: 3, message: "boom" }],
      },
    });
  });
});

describe("fromWireMessage", () => {
  it("converts a diff.proposed wire message to camelCase", () => {
    const raw = {
      type: "diff.proposed",
      id: "utt-1",
      payload: {
        proposal_id: "p-123",
        file_path: "src/foo.py",
        unified_diff: "--- a\n+++ b\n",
        rationale: "why",
      },
    };

    expect(fromWireMessage(raw)).toEqual({
      type: "diff.proposed",
      id: "utt-1",
      payload: {
        proposalId: "p-123",
        filePath: "src/foo.py",
        unifiedDiff: "--- a\n+++ b\n",
        rationale: "why",
      },
    });
  });

  it("converts an agent.explanation.delta wire message unchanged in field names", () => {
    const raw = {
      type: "agent.explanation.delta",
      id: "utt-1",
      payload: { text: "hello", done: false },
    };

    expect(fromWireMessage(raw)).toEqual(raw);
  });

  it("returns undefined for an unrecognized message type", () => {
    expect(fromWireMessage({ type: "not.a.real.type", payload: {} })).toBeUndefined();
  });

  it("returns undefined for malformed input", () => {
    expect(fromWireMessage(null)).toBeUndefined();
    expect(fromWireMessage("not an object")).toBeUndefined();
    expect(fromWireMessage({})).toBeUndefined();
  });
});
