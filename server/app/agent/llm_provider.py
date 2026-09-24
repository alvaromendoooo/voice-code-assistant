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
