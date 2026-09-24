from app.agent.llm_provider import StubLLMProvider
from app.agent.runtime import AgentRuntime
from app.context_engine.file_context import EditorContextSnapshot


def _context(file_text: str = "def foo():\n    return 1\n") -> EditorContextSnapshot:
    return EditorContextSnapshot(
        file_path="src/foo.py",
        language="python",
        file_text=file_text,
    )


async def test_handle_utterance_returns_explanation_chunks():
    runtime = AgentRuntime(StubLLMProvider())

    chunks, proposal = await runtime.handle_utterance("What does this do?", _context())

    assert chunks == list(StubLLMProvider._CANNED_SENTENCES)
    assert proposal is None


async def test_handle_utterance_proposes_an_edit_when_review_is_requested():
    runtime = AgentRuntime(StubLLMProvider())

    _, proposal = await runtime.handle_utterance(
        "Can you review this function?", _context()
    )

    assert proposal is not None
    assert proposal.file_path == "src/foo.py"
    assert proposal.original_text == "def foo():\n    return 1\n"
    assert "TODO" in proposal.proposed_text
