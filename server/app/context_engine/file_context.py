"""Phase 1 context engine: current file + selection only.

No project-wide context (git, tests, diagnostics beyond client-forwarded LSP output,
Tree-sitter structural parsing) yet -- that is Phase 5 in AGENTS.md's roadmap.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EditorContextSnapshot:
    file_path: str
    language: str
    file_text: str
    selection: tuple[int, int] | None = None
    cursor: tuple[int, int] | None = None


def build_prompt_context(snapshot: EditorContextSnapshot) -> str:
    """Render an EditorContextSnapshot into prompt text for the LLM."""
    lines = [f"File: {snapshot.file_path} ({snapshot.language})"]
    if snapshot.selection is not None:
        start, end = snapshot.selection
        lines.append(f"Selected lines: {start}-{end}")
    if snapshot.cursor is not None:
        line, col = snapshot.cursor
        lines.append(f"Cursor: line {line}, col {col}")
    lines.append("---")
    lines.append(snapshot.file_text)
    return "\n".join(lines)
