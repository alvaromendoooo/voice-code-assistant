"""FastAPI app entry point: WebSocket route + shared-token handshake check."""

from __future__ import annotations

import os

from app.config import load_environment

load_environment()

from fastapi import FastAPI, WebSocket, WebSocketException, status  # noqa: E402

from app.agent.llm_provider import (  # noqa: E402
    GeminiProvider,
    LLMProvider,
    OllamaProvider,
    StubLLMProvider,
)
from app.agent.runtime import AgentRuntime  # noqa: E402
from app.auth.token_auth import is_token_valid  # noqa: E402
from app.ws.session import Session  # noqa: E402

app = FastAPI(title="Voice Code Assistant - Agent Runtime")


def _build_llm_provider() -> LLMProvider:
    """Selects a provider based on VCA_LLM_PROVIDER, falling back to auto-detection.

    VCA_LLM_PROVIDER: "gemini" | "ollama" | "stub" (case-insensitive). If unset, uses
    GeminiProvider when GOOGLE_API_KEY is present, else StubLLMProvider.
    """
    provider_name = os.environ.get("VCA_LLM_PROVIDER", "").strip().lower()
    if provider_name == "ollama":
        return OllamaProvider(model=os.environ.get("OLLAMA_MODEL", "llama3.2"))
    if provider_name == "gemini":
        return GeminiProvider()
    if provider_name == "stub":
        return StubLLMProvider()

    if os.environ.get("GOOGLE_API_KEY"):
        return GeminiProvider()
    return StubLLMProvider()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = None) -> None:
    if not is_token_valid(token):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    agent_runtime = AgentRuntime(_build_llm_provider())
    session = Session(websocket, agent_runtime)
    await session.run()
