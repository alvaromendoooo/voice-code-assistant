"""Provider-agnostic LLM interface.

The agent runtime depends only on this interface, never on a specific vendor SDK
(Anthropic, OpenAI, local/Ollama, ...). Concrete adapters live alongside this module,
one per provider, and are selected via configuration -- not by branching in the runtime.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMProvider(Protocol):
    """Minimal surface the agent runtime needs from any LLM backend."""

    async def stream_reply(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        """Yield response text incrementally (e.g. sentence or token chunks)."""
        ...


class StubLLMProvider:
    """Deterministic canned-response provider.

    Used to validate the WebSocket wire format end-to-end without depending on a real
    LLM backend. Replace with a real provider adapter once the round-trip is confirmed.
    """

    _CANNED_SENTENCES = (
        "I looked at the current file.",
        "This is a stub response used to validate the WebSocket wire format end-to-end.",
        "Swap in a real LLMProvider once the round-trip is confirmed working.",
    )

    async def stream_reply(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        for sentence in self._CANNED_SENTENCES:
            yield sentence
