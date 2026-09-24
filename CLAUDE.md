# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

This repository currently contains only planning/design documents — there is no implementation code yet. The two files that define the project are:

- `voice-code-assistant/AGENTS.md` — the full project spec: goals, principles, workflows, architecture, and phased development plan. **Read this file before starting any implementation work in this repo.**
- `docs/architecture/overview.mermaid` — a high-level flowchart of the intended system (Developer → Voice Layer → Agent Runtime → Context Engine / Tool Interface → Diff Engine → IDE → Apply Patch).

There is no build system, package manifest, test runner, or source tree yet. Do not assume any particular language or framework — one has not been chosen. When implementation begins, this file should be updated with real build/lint/test commands and the actual module layout.

## What This Project Is

A voice-first coding assistant: the developer talks to an agent about their codebase, the agent proposes changes, and changes are only ever applied as diffs the developer explicitly accepts or rejects inside their IDE. Voice is the conversational interface; the IDE remains the visual interface for code and diff approval.

## Non-Negotiable Design Rules (from AGENTS.md)

These constraints apply to any code written in this repo, regardless of what stack is eventually chosen:

- **Human approval is mandatory.** The assistant must never silently modify files. All edits flow through: request → analysis → proposed change → diff shown in IDE → explicit user approval → apply. Never wire up a path that writes to the user's files without a diff/approval step in between.
- **The LLM never touches the filesystem directly.** Code modification goes through a `propose_edit()`-style tool call, not direct writes — the tool/diff layer is the security and abstraction boundary between the LLM and the developer's environment.
- **Tool-mediated environment access.** The agent interacts with the dev environment through a constrained tool interface (e.g. `read_file`, `search_code`, `list_files`, `get_project_structure`, `get_git_status`, `get_git_diff`, `get_diagnostics`, `run_tests`, `run_command`, `propose_edit`), not unrestricted access.
- **Provider independence.** Keep voice providers and LLM providers swappable behind an internal abstraction; don't couple the agent runtime to one vendor's SDK.
- **Context is retrieved selectively**, not by dumping the whole repo into the LLM. Avoid exposing secrets or unnecessary repository contents to external models.
- **Plan before implementing** non-trivial requests (identify affected components/files/dependencies/risks) rather than jumping straight to large code generation.
- **Build incrementally**, following the phased roadmap in AGENTS.md (voice conversation → editor context → proposed changes/diffing → scaffolding → project-aware context → agentic workflows). Don't build later-phase functionality (e.g. full agentic workflows) before earlier-phase primitives exist.
- **Scaffolding requests generate structure only** (e.g. a function skeleton with the right signature and a loop), not a full implementation, unless the user explicitly asks for the implementation.
- **Code review distinguishes severity classes**: bugs vs. maintainability vs. performance vs. security vs. style vs. optional improvement. Don't present style preferences as correctness problems.
- **Never modify or remove existing tests just to make an implementation pass.** When a test fails, determine whether the implementation, the test, the requirement, or the environment is at fault before changing anything.

## Architecture (target, not yet built)

```
IDE/Editor (code, voice, proposed diff, accept/reject)
        │  IPC / WebSocket
        ▼
Voice Assistant Core
  Voice Input → Agent Runtime → Voice Output
                     │
              Context Engine
                     │
              Tool Interface
                     │
        ┌────────────┼────────────┐
   File System       Git       Test Runner
```

Code modification protocol: `LLM → propose_edit() → Workspace/Diff Service → generate diff → IDE → user approval → apply patch`.
