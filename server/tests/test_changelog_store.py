import json

from app.changelog.changelog_store import ChangelogStore


def test_record_proposal_appends_a_pending_entry(tmp_path):
    store = ChangelogStore("session-1", data_dir=tmp_path)

    store.record_proposal(
        proposal_id="p-1",
        file_path="src/foo.py",
        original_snippet="def foo(): return 1",
        unified_diff="--- a\n+++ b\n",
        rationale="why",
    )

    lines = (tmp_path / "session-1.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["kind"] == "proposal"
    assert entry["proposal_id"] == "p-1"
    assert entry["decision"] == "pending"


def test_record_decision_appends_rather_than_mutates(tmp_path):
    store = ChangelogStore("session-2", data_dir=tmp_path)

    store.record_proposal(
        proposal_id="p-1",
        file_path="src/foo.py",
        original_snippet="...",
        unified_diff="...",
        rationale="...",
    )
    store.record_decision("p-1", "accepted")

    lines = (tmp_path / "session-2.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2

    proposal_entry = json.loads(lines[0])
    decision_entry = json.loads(lines[1])
    assert proposal_entry["decision"] == "pending"  # original entry is untouched
    assert decision_entry["kind"] == "decision"
    assert decision_entry["proposal_id"] == "p-1"
    assert decision_entry["decision"] == "accepted"


def test_creates_data_dir_if_missing(tmp_path):
    nested_dir = tmp_path / "nested" / "changelog"
    store = ChangelogStore("session-3", data_dir=nested_dir)

    store.record_decision("p-1", "rejected")

    assert (nested_dir / "session-3.jsonl").exists()
