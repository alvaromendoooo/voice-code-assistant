"""Turns an EditProposal into a unified diff string for the DiffProposed message.

Format decision (unified diff string, not structured range edits) is recorded in
docs/architecture/phase1-design.md.
"""

from __future__ import annotations

from app.tools.propose_edit import EditProposal


def build_unified_diff(proposal: EditProposal) -> str:
    raise NotImplementedError
