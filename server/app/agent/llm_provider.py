"""Provider-agnostic LLM interface.

The agent runtime depends only on this interface, never on a specific vendor SDK
(Anthropic, OpenAI, local/Ollama, ...). Concrete adapters live alongside this module,
one per provider, and are selected via configuration -- not by branching in the runtime.
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, ValidationError


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class EditDecision:
    proposed_text: str
    rationale: str


class LLMProvider(Protocol):
    """Minimal surface the agent runtime needs from any LLM backend."""

    async def stream_reply(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        """Yield response text incrementally (e.g. sentence or token chunks)."""
        ...

    async def decide_edit(
        self, messages: list[LLMMessage], file_text: str
    ) -> EditDecision | None:
        """Decide whether an edit is warranted for file_text given the conversation.

        Returns None when no edit should be proposed.
        """
        ...


class StubLLMProvider:
    """Deterministic canned-response provider.

    Used to validate the WebSocket wire format end-to-end without depending on a real
    LLM backend. Kept as the no-API-key fallback in main.py.
    """

    _CANNED_SENTENCES = (
        "I looked at the current file.",
        "This is a stub response used to validate the WebSocket wire format end-to-end.",
        "Swap in a real LLMProvider once the round-trip is confirmed working.",
    )
    _EDIT_TRIGGER_KEYWORDS = ("review", "improve")

    async def stream_reply(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        for sentence in self._CANNED_SENTENCES:
            yield sentence

    async def decide_edit(
        self, messages: list[LLMMessage], file_text: str
    ) -> EditDecision | None:
        combined_text = " ".join(m.content for m in messages).lower()
        if not any(keyword in combined_text for keyword in self._EDIT_TRIGGER_KEYWORDS):
            return None

        proposed_text = file_text.rstrip("\n") + "\n# TODO: reviewed by Voice Code Assistant (stub)\n"
        return EditDecision(
            proposed_text=proposed_text,
            rationale="Stub proposal for Phase 1 wire-format validation; not a real code review.",
        )


class _EditDecisionSchema(BaseModel):
    should_edit: bool
    proposed_text: str
    rationale: str


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

    async def decide_edit(
        self, messages: list[LLMMessage], file_text: str
    ) -> EditDecision | None:
        system_instruction, contents = _split_system_prompt(messages)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=_EditDecisionSchema,
            # The SDK's defaults (5 attempts, up to 60s backoff each) can turn a run
            # of transient 503s into a multi-minute hang. This call is a best-effort
            # enhancement (see the except clause below), so bound it to fail fast --
            # unlike stream_reply, which keeps default retry/timeout behavior since
            # it's the primary value of the response and streaming needs more time.
            http_options=types.HttpOptions(
                timeout=20_000,
                retry_options=types.HttpRetryOptions(attempts=2, initial_delay=1, max_delay=5),
            ),
        )
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=contents,
                config=config,
            )
        except genai_errors.APIError:
            # The edit decision is a best-effort enhancement on top of the
            # explanation, which the caller already has by this point -- degrade to
            # "no edit proposed" rather than failing the whole utterance.
            return None
        decision = response.parsed
        if not isinstance(decision, _EditDecisionSchema) or not decision.should_edit:
            return None
        return EditDecision(proposed_text=decision.proposed_text, rationale=decision.rationale)


class OllamaProvider:
    """Local Ollama-backed LLM provider, talking to Ollama's REST API directly.

    Ollama must already be running locally (`ollama serve`, or the desktop app) with
    the given model pulled (`ollama pull <model>`). No API key needed.
    """

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")

    async def stream_reply(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", f"{self._base_url}/api/chat", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    content = data.get("message", {}).get("content")
                    if content:
                        yield content
                    if data.get("done"):
                        break

    async def decide_edit(
        self, messages: list[LLMMessage], file_text: str
    ) -> EditDecision | None:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "format": _EditDecisionSchema.model_json_schema(),
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(f"{self._base_url}/api/chat", json=payload)
                response.raise_for_status()
            except httpx.HTTPError:
                # Best-effort enhancement -- degrade to "no edit proposed" rather than
                # failing the whole utterance if Ollama is unreachable or errors.
                return None

        content = response.json().get("message", {}).get("content", "")
        try:
            decision = _EditDecisionSchema.model_validate_json(content)
        except ValidationError:
            return None
        if not decision.should_edit:
            return None
        return EditDecision(proposed_text=decision.proposed_text, rationale=decision.rationale)


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
