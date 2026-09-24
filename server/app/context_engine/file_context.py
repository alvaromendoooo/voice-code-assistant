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
    raise NotImplementedError
