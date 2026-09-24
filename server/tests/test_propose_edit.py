from app.tools.propose_edit import propose_edit


def test_propose_edit_generates_unique_ids():
    first = propose_edit("src/foo.py", "a", "b", "rationale")
    second = propose_edit("src/foo.py", "a", "b", "rationale")

    assert first.proposal_id != second.proposal_id
    assert first.proposal_id.startswith("p-")


def test_propose_edit_preserves_fields():
    proposal = propose_edit(
        file_path="src/foo.py",
        original_text="original",
        proposed_text="proposed",
        rationale="why",
    )

    assert proposal.file_path == "src/foo.py"
    assert proposal.original_text == "original"
    assert proposal.proposed_text == "proposed"
    assert proposal.rationale == "why"
