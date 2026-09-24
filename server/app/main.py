"""FastAPI app entry point: WebSocket route + shared-token handshake check."""

from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketException, status

from app.agent.llm_provider import StubLLMProvider
from app.agent.runtime import AgentRuntime
from app.auth.token_auth import is_token_valid
from app.ws.session import Session

app = FastAPI(title="Voice Code Assistant - Agent Runtime")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = None) -> None:
    if not is_token_valid(token):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    # StubLLMProvider stands in until a real provider adapter exists -- see
    # docs/architecture/phase1-design.md and app/agent/llm_provider.py.
    agent_runtime = AgentRuntime(StubLLMProvider())
    session = Session(websocket, agent_runtime)
    await session.run()
