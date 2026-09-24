"""Agent Runtime: orchestrates context -> LLM -> optional tool call -> response."""

from __future__ import annotations

from app.agent.llm_provider import LLMMessage, LLMProvider
from app.context_engine.file_context import EditorContextSnapshot, build_prompt_context
from app.tools.propose_edit import EditProposal, propose_edit

_EXPLANATION_SYSTEM_PROMPT = (
    "You are a voice-first coding assistant. Explain your findings about the "
    "developer's code concisely, in a few sentences suitable for reading aloud."
)

_EDIT_DECISION_SYSTEM_PROMPT = (
    "You are a voice-first coding assistant deciding whether to propose a code edit. "
    "Given the developer's request and the current file, set should_edit to true only "
    "when a concrete improvement is warranted. When true, proposed_text must be the "
    "complete corrected file content (not a diff or a snippet) and rationale must "
    "explain why. When false, leave proposed_text and rationale empty."
)


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
        prompt_context = build_prompt_context(context)
        user_message = LLMMessage(
            role="user", content=f"{prompt_context}\n\nDeveloper: {utterance_text}"
        )

        explanation_messages = [
            LLMMessage(role="system", content=_EXPLANATION_SYSTEM_PROMPT),
            user_message,
        ]
        chunks = [
            chunk async for chunk in self._llm_provider.stream_reply(explanation_messages)
        ]

        decision_messages = [
            LLMMessage(role="system", content=_EDIT_DECISION_SYSTEM_PROMPT),
            user_message,
        ]
        decision = await self._llm_provider.decide_edit(decision_messages, context.file_text)

        proposal = None
        if decision is not None:
            proposal = propose_edit(
                file_path=context.file_path,
                original_text=context.file_text,
                proposed_text=decision.proposed_text,
                rationale=decision.rationale,
            )
        return chunks, proposal
