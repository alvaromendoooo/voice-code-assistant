"""Agent Runtime: orchestrates context -> LLM -> optional tool call -> response.

This is the Phase 1 skeleton. It wires the pieces together but does not yet implement
prompt construction, streaming, or edit-proposal logic -- see the AGENTS.md code
modification protocol and docs/architecture/phase1-design.md for the intended flow.
"""

from __future__ import annotations

from app.agent.llm_provider import LLMMessage, LLMProvider
from app.context_engine.file_context import EditorContextSnapshot, build_prompt_context
from app.tools.propose_edit import EditProposal, propose_edit

_SYSTEM_PROMPT = (
    "You are a voice-first coding assistant. Explain findings concisely and propose "
    "an edit only when clearly warranted."
)

# Phase 1 heuristic standing in for real LLM-driven edit decisions -- see
# _maybe_propose_edit below.
_EDIT_TRIGGER_KEYWORDS = ("review", "improve")


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
        messages = [
            LLMMessage(role="system", content=_SYSTEM_PROMPT),
            LLMMessage(
                role="user",
                content=f"{build_prompt_context(context)}\n\nDeveloper: {utterance_text}",
            ),
        ]

        chunks = [chunk async for chunk in self._llm_provider.stream_reply(messages)]
        proposal = self._maybe_propose_edit(utterance_text, context)
        return chunks, proposal

    def _maybe_propose_edit(
        self,
        utterance_text: str,
        context: EditorContextSnapshot,
    ) -> EditProposal | None:
        """Stub decision logic for whether to propose an edit.

        This keyword check stands in for a real LLM decision and is only here to
        exercise the diff.proposed path while validating the wire format. Replace once
        a real LLMProvider drives this decision.
        """
        if not any(keyword in utterance_text.lower() for keyword in _EDIT_TRIGGER_KEYWORDS):
            return None

        proposed_text = (
            context.file_text.rstrip("\n")
            + "\n# TODO: reviewed by Voice Code Assistant (stub)\n"
        )
        return propose_edit(
            file_path=context.file_path,
            original_text=context.file_text,
            proposed_text=proposed_text,
            rationale=(
                "Stub proposal for Phase 1 wire-format validation; not a real code review."
            ),
        )
