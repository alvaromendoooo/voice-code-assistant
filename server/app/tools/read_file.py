"""read_file tool: returns the content already provided by the client's editor context.

Phase 1 does not give the agent independent filesystem access -- it only ever sees what
the IDE extension sends over the WebSocket. A real filesystem-backed read_file is a
Phase 5 concern (project-wide context), gated behind workspace-boundary checks.
"""

from __future__ import annotations


def read_file(file_path: str, file_text: str) -> str:
    """Return the given file's text.

    Placeholder signature for the eventual tool-calling interface described in
    AGENTS.md's Agent Tools section. Currently a passthrough over client-supplied text.
    """
    raise NotImplementedError
