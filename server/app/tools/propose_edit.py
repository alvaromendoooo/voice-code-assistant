"""propose_edit tool: the only path by which the agent can produce a code change.

This function must never write to the filesystem. It returns a proposal; the diff
service turns it into a unified diff, the client renders it, and only the user's
explicit acceptance -- applied client-side via the IDE's own edit APIs -- ever touches
the file. See the Code Modification Protocol in AGENTS.md.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EditProposal:
    proposal_id: str
    file_path: str
    original_text: str
    proposed_text: str
    rationale: str


def propose_edit(
    file_path: str,
    original_text: str,
    proposed_text: str,
    rationale: str,
) -> EditProposal:
    raise NotImplementedError
