"""Provider-agnostic LLM interface.

The agent runtime depends only on this interface, never on a specific vendor SDK
(Anthropic, OpenAI, local/Ollama, ...). Concrete adapters live alongside this module,
one per provider, and are selected via configuration -- not by branching in the runtime.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

from google import genai
from google.genai import types


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


class GeminiProvider:
    """Google Gemini-backed LLM provider.

    Reads GOOGLE_API_KEY from the environment (populated from the repo-root .env by
    app.config.load_environment). Selected automatically in main.py when that key is
    present; falls back to StubLLMProvider otherwise.
    """

    def __init__(self, model: str = "gemini-3.6-flash", api_key: str | None = None) -> None:
        resolved_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not resolved_key:
            raise RuntimeError("GOOGLE_API_KEY is not set")
        self._client = genai.Client(api_key=resolved_key)
        self._model = model

    async def stream_reply(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        system_instruction, contents = _split_system_prompt(messages)
        config = (
            types.GenerateContentConfig(system_instruction=system_instruction)
            if system_instruction
            else None
        )
        stream = await self._client.aio.models.generate_content_stream(
            model=self._model,
            contents=contents,
            config=config,
        )
        async for chunk in stream:
            if chunk.text:
                yield chunk.text


def _split_system_prompt(
    messages: list[LLMMessage],
) -> tuple[str | None, list[types.Content]]:
    system_parts = [m.content for m in messages if m.role == "system"]
    contents = [
        types.Content(role=_to_gemini_role(m.role), parts=[types.Part(text=m.content)])
        for m in messages
        if m.role != "system"
    ]
    return ("\n".join(system_parts) or None, contents)


def _to_gemini_role(role: str) -> str:
    return "model" if role == "assistant" else "user"
