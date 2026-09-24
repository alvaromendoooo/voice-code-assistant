from app.context_engine.file_context import EditorContextSnapshot, build_prompt_context


def test_build_prompt_context_includes_file_and_text():
    snapshot = EditorContextSnapshot(
        file_path="src/foo.py",
        language="python",
        file_text="def foo():\n    return 1\n",
    )

    prompt = build_prompt_context(snapshot)

    assert "src/foo.py" in prompt
    assert "python" in prompt
    assert "def foo():" in prompt
    assert "Selected lines" not in prompt
    assert "Cursor" not in prompt


def test_build_prompt_context_includes_selection_and_cursor_when_present():
    snapshot = EditorContextSnapshot(
        file_path="src/foo.py",
        language="python",
        file_text="def foo():\n    return 1\n",
        selection=(1, 2),
        cursor=(2, 4),
    )

    prompt = build_prompt_context(snapshot)

    assert "Selected lines: 1-2" in prompt
    assert "Cursor: line 2, col 4" in prompt
