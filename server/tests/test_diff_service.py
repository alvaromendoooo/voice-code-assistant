from app.diff.diff_service import build_unified_diff
from app.tools.propose_edit import EditProposal


def test_build_unified_diff_shows_added_line():
    proposal = EditProposal(
        proposal_id="p-1",
        file_path="src/foo.py",
        original_text="def foo():\n    return 1\n",
        proposed_text="def foo():\n    return 1\n\n\ndef bar():\n    return 2\n",
        rationale="added a function",
    )

    diff = build_unified_diff(proposal)

    assert "--- a/src/foo.py" in diff
    assert "+++ b/src/foo.py" in diff
    assert "+def bar():" in diff
    assert "+    return 2" in diff


def test_build_unified_diff_is_empty_when_texts_are_identical():
    proposal = EditProposal(
        proposal_id="p-2",
        file_path="src/foo.py",
        original_text="def foo():\n    return 1\n",
        proposed_text="def foo():\n    return 1\n",
        rationale="no-op",
    )

    assert build_unified_diff(proposal) == ""
