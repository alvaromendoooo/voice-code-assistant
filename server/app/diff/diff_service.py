"""Turns an EditProposal into a unified diff string for the DiffProposed message.

Format decision (unified diff string, not structured range edits) is recorded in
docs/architecture/phase1-design.md.
"""

from __future__ import annotations

import difflib

from app.tools.propose_edit import EditProposal


def build_unified_diff(proposal: EditProposal) -> str:
    diff_lines = difflib.unified_diff(
        proposal.original_text.splitlines(keepends=True),
        proposal.proposed_text.splitlines(keepends=True),
        fromfile=f"a/{proposal.file_path}",
        tofile=f"b/{proposal.file_path}",
    )
    return "".join(diff_lines)
