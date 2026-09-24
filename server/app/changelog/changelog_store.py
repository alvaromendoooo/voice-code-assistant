"""Append-only JSONL record of proposed edits, for developer traceability.

One file per session at data/changelog/<session_id>.jsonl. See
docs/architecture/phase1-design.md for the entry shape and rationale. This is
server-local bookkeeping; it has no corresponding WebSocket message in Phase 1.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "changelog"


class ChangelogStore:
    def __init__(self, session_id: str, data_dir: Path = DATA_DIR) -> None:
        self._session_id = session_id
        self._path = data_dir / f"{session_id}.jsonl"

    def record_proposal(
        self,
        proposal_id: str,
        file_path: str,
        original_snippet: str,
        unified_diff: str,
        rationale: str,
    ) -> None:
        self._append(
            {
                "kind": "proposal",
                "proposal_id": proposal_id,
                "timestamp": self._now(),
                "file_path": file_path,
                "original_snippet": original_snippet,
                "unified_diff": unified_diff,
                "rationale": rationale,
                "decision": "pending",
            }
        )

    def record_decision(
        self,
        proposal_id: str,
        decision: Literal["accepted", "rejected"],
    ) -> None:
        # The store is append-only, so a decision is a new entry correlated by
        # proposal_id rather than a mutation of the original "proposal" entry.
        self._append(
            {
                "kind": "decision",
                "proposal_id": proposal_id,
                "timestamp": self._now(),
                "decision": decision,
            }
        )

    def _append(self, entry: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
