# Phase 1 Design — Voice → LLM → Diff → Approval

Status: draft, no code written yet. This document scopes the first vertical slice per
AGENTS.md's phased roadmap: it deliberately covers Phase 1–3 primitives (voice
conversation, editor context, proposed-changes/diff/approval) and stops short of
scaffolding (Phase 4), project-wide context (Phase 5), and agentic workflows (Phase 6).

Goal conversation this slice must support:

> "I implemented this function. Can you review it and tell me how I could improve it?"

## Scope for this slice

In scope:
- Client captures mic audio, runs streaming STT locally, sends text utterances to server.
- Server (Agent Runtime) holds conversation state, calls the LLM with current-file context.
- Server streams back an explanation (text, sentence-chunked) and, optionally, a single
  structured edit proposal for the active file.
- Client renders the diff using the host IDE's native diff/edit APIs and turns explanation
  text into streamed TTS.
- User accepts or rejects; accept applies via the IDE's `WorkspaceEdit`-equivalent, never
  a raw file write from the server.

Out of scope (later phases): multi-file edits, project-wide context (git status/diff, test
runs, diagnostics beyond what the IDE's LSP already surfaces), Tree-sitter-based chunking,
scaffolding-specific prompting, agentic multi-step planning loops.

## Module layout

```
voice-code-assistant/
├── client/                        # IDE extension (TypeScript)
│   ├── src/
│   │   ├── extension.ts           # activation entry point
│   │   ├── connection/
│   │   │   └── socket-client.ts   # WebSocket lifecycle, reconnect, message (de)serialization
│   │   ├── voice/
│   │   │   ├── mic-capture.ts     # mic stream + VAD segmentation
│   │   │   ├── stt.ts             # streaming speech-to-text provider adapter
│   │   │   └── tts.ts             # streaming text-to-speech playback
│   │   ├── context/
│   │   │   └── editor-context.ts  # active file, selection, cursor position snapshot
│   │   ├── diff/
│   │   │   ├── diff-view.ts       # render proposed edit as native diff view
│   │   │   └── apply-edit.ts      # apply accepted edit via WorkspaceEdit-equivalent
│   │   └── ui/
│   │       └── status-bar.ts      # connection/recording state indicator
│   └── package.json
│
├── server/                        # Agent Runtime (Python, FastAPI)
│   ├── app/
│   │   ├── main.py                # FastAPI app, WebSocket route registration
│   │   ├── ws/
│   │   │   └── session.py         # per-connection session, message dispatch loop
│   │   ├── agent/
│   │   │   ├── runtime.py         # orchestrates: context -> LLM -> tool calls -> response
│   │   │   └── llm_provider.py    # provider-agnostic interface (Anthropic/OpenAI/local)
│   │   ├── context_engine/
│   │   │   └── file_context.py    # builds prompt context from current file + selection
│   │   ├── tools/
│   │   │   ├── read_file.py
│   │   │   └── propose_edit.py    # only tool that can produce a diff; never writes to disk
│   │   ├── diff/
│   │   │   └── diff_service.py    # turns an edit proposal into a structured diff payload
│   │   └── schemas/
│   │       └── messages.py        # WebSocket message schema (pydantic models)
│   └── pyproject.toml
│
└── docs/
    └── architecture/
        ├── overview.mermaid
        └── phase1-design.md       # this file
```

Notes:
- `tools/propose_edit.py` is the only path that produces an edit; it returns a proposal
  object, it does not touch the filesystem. This mirrors the non-negotiable rule that the
  LLM never touches the filesystem directly.
- `llm_provider.py` is the provider-independence seam — swapping models means implementing
  this interface, not touching `runtime.py`.
- No Tree-sitter or LSP modules yet in this slice. `context_engine/file_context.py` starts
  as "send the current file text + selection range," nothing structural. LSP diagnostics
  arrive from the client (host IDE's own LSP client), not a server-side LSP process — the
  server has no `lsp/` module in this phase.

## WebSocket message schema

One WebSocket connection per IDE session. All messages are JSON objects with a `type`
discriminator and a `id` (client-generated correlation id) where a request expects a
matching response. Direction is `client->server` or `server->client`.

### Envelope

```json
{
  "type": "string",
  "id": "uuid, present on request/response pairs",
  "payload": { "...": "type-specific" }
}
```

### client -> server

**`voice.utterance`** — one finalized VAD-segmented chunk of transcribed speech.
```json
{
  "type": "voice.utterance",
  "id": "8f3a...",
  "payload": {
    "text": "can you review this function",
    "is_final": true,
    "context": {
      "file_path": "src/foo.py",
      "language": "python",
      "selection": { "start_line": 12, "end_line": 28 },
      "cursor": { "line": 20, "col": 4 },
      "file_text": "..."
    }
  }
}
```

**`diff.decision`** — user accepted/rejected a proposed edit.
```json
{
  "type": "diff.decision",
  "id": "generated fresh",
  "payload": {
    "proposal_id": "matches proposal_id from diff.proposed",
    "decision": "accepted"
  }
}
```

**`session.diagnostics`** — client-forwarded LSP diagnostics for the active file (pushed
opportunistically, not requested; server treats it as latest-known-state, not a queue).
```json
{
  "type": "session.diagnostics",
  "payload": {
    "file_path": "src/foo.py",
    "diagnostics": [
      { "severity": "error", "line": 14, "message": "undefined name 'x'" }
    ]
  }
}
```

### server -> client

**`agent.explanation.delta`** — streamed sentence-chunked explanation text, for
incremental TTS playback.
```json
{
  "type": "agent.explanation.delta",
  "id": "matches originating voice.utterance id",
  "payload": { "text": "This function recomputes the average on every call.", "done": false }
}
```
Client starts TTS on each chunk as it arrives; `done: true` marks the final chunk.

**`diff.proposed`** — a structured edit proposal for the active file.
```json
{
  "type": "diff.proposed",
  "id": "matches originating voice.utterance id",
  "payload": {
    "proposal_id": "p-1234",
    "file_path": "src/foo.py",
    "unified_diff": "--- a/src/foo.py\n+++ b/src/foo.py\n@@ ...",
    "rationale": "Caches the computed average instead of recomputing it each call."
  }
}
```

**`error`** — recoverable or terminal error, correlated to a request when applicable.
```json
{
  "type": "error",
  "id": "matches failed request id, if any",
  "payload": { "code": "llm_provider_error", "message": "upstream request timed out" }
}
```

### Message flow for the goal conversation

```
client: voice.utterance ("review this function", file_context attached)
server: agent.explanation.delta ×N   (streamed, TTS plays incrementally)
server: diff.proposed                (if an improvement is actionable)
client: renders diff in native diff view
client: diff.decision (accepted | rejected)
server: (if accepted) no further action — client already applied via WorkspaceEdit;
        server only needs the decision for conversation-state/logging purposes
```

Note the server does not need a "diff.applied" acknowledgment from an apply step, because
the server never applies anything — `diff.decision` is purely informational for the
conversation history and any future undo/audit trail.

## Resolved decisions

1. **STT/TTS provider is not part of the WebSocket schema.** The LLM's behavior depends
   only on the text content it receives, not on which provider produced or will consume
   that text. `voice.utterance` carries plain transcribed text and `agent.explanation.delta`
   carries plain text for TTS — no provider identifier field. Provider choice is purely an
   internal detail of `client/src/voice/stt.ts` and `tts.ts`.
2. **Diff payload format is a unified diff string** (`diff.proposed.payload.unified_diff`),
   as already specified above. Revisit only if a future phase needs partial (hunk-level)
   approval.
3. **Auth: shared private token between IDE and backend.** The client sends a token on
   WebSocket connect; the server rejects the handshake if it doesn't match. This is a
   local-development-grade secret (e.g. generated once, stored in the extension's settings
   and in the server's environment), not a full auth system — sufficient to stop an
   arbitrary local process from opening the agent's WebSocket port.

   ```
   ws://<host>:<port>/ws?token=<shared-secret>
   ```

   Server validates `token` against its own configured value before accepting the
   connection (reject with HTTP 401 at the WebSocket upgrade, before any session state is
   created). The token is never sent to the LLM provider and never logged.

## Change log / traceability record

To support the project's learning goal ("help develop practical skills... understand and
build systems that make a developer-facing AI agent reliable and controllable"), the
server keeps a per-session, append-only record of every proposed edit and its outcome:
original code, proposed diff, rationale, and the user's accept/reject decision. This lets
the developer look back at what was changed and why, independent of the IDE's own
undo/git history.

- **Storage (Phase 1):** a simple local file, one JSON object per line (JSONL) — e.g.
  `server/data/changelog/<session_id>.jsonl`. No database yet; this is a Phase 1 primitive,
  not a project-wide feature.
- **Written on:** every `diff.proposed` (before the user decides) and updated when the
  matching `diff.decision` arrives, so a rejected proposal is retained too, not just
  accepted ones.
- **Entry shape:**
  ```json
  {
    "proposal_id": "p-1234",
    "timestamp": "2026-09-24T10:15:00Z",
    "file_path": "src/foo.py",
    "original_snippet": "...",
    "unified_diff": "...",
    "rationale": "...",
    "decision": "accepted | rejected | pending"
  }
  ```
- This is server-local bookkeeping, not a new WebSocket message type — the client doesn't
  need to know it exists yet. A later phase could expose it as a "history" panel in the IDE
  (would add a `history.query` request/response pair at that point).

## Module layout additions for the resolved decisions

```
server/
├── app/
│   ├── auth/
│   │   └── token_auth.py       # validates shared token at WebSocket handshake
│   └── changelog/
│       └── changelog_store.py  # append-only JSONL writer/reader for proposal history
```
