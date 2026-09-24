"""Agent Runtime: orchestrates context -> LLM -> optional tool call -> response.

This is the Phase 1 skeleton. It wires the pieces together but does not yet implement
prompt construction, streaming, or edit-proposal logic -- see the AGENTS.md code
modification protocol and docs/architecture/phase1-design.md for the intended flow.
"""

from __future__ import annotations

from app.agent.llm_provider import LLMProvider
from app.context_engine.file_context import EditorContextSnapshot
from app.tools.propose_edit import EditProposal


class AgentRuntime:
    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm_provider = llm_provider

    async def handle_utterance(
        self,
        utterance_text: str,
        context: EditorContextSnapshot,
    ) -> tuple[list[str], EditProposal | None]:
        """Process one voice utterance.

        Returns the explanation as a list of text chunks (for streamed TTS playback)
        and, if the LLM decided an edit is warranted, a single edit proposal for the
        active file.
        """
        raise NotImplementedError
