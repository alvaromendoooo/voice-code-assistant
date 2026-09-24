"""Tests OllamaProvider.decide_edit against a fake HTTP client, no real Ollama needed.

Covers the malformed-response-body regression: decide_edit must degrade to None
rather than raising, per its own documented "best-effort" contract.
"""

import httpx
import pytest

from app.agent.llm_provider import LLMMessage, OllamaProvider


class _FakeResponse:
    def __init__(self, *, json_body=None, raw_text="", status_error=False):
        self._json_body = json_body
        self._raw_text = raw_text
        self._status_error = status_error

    def raise_for_status(self):
        if self._status_error:
            raise httpx.HTTPStatusError("boom", request=None, response=self)

    def json(self):
        if self._json_body is None:
            import json as json_module

            raise json_module.JSONDecodeError("bad json", self._raw_text, 0)
        return self._json_body


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def post(self, url, json):
        return self._response


@pytest.fixture
def patch_httpx_client(monkeypatch):
    def _patch(response: _FakeResponse):
        monkeypatch.setattr(
            "app.agent.llm_provider.httpx.AsyncClient",
            lambda *args, **kwargs: _FakeAsyncClient(response),
        )

    return _patch


async def test_decide_edit_returns_decision_on_valid_response(patch_httpx_client):
    patch_httpx_client(
        _FakeResponse(
            json_body={
                "message": {
                    "content": '{"should_edit": true, "proposed_text": "fixed", "rationale": "why"}'
                }
            }
        )
    )
    provider = OllamaProvider(model="test-model")

    decision = await provider.decide_edit([LLMMessage(role="user", content="review")], "orig")

    assert decision is not None
    assert decision.proposed_text == "fixed"
    assert decision.rationale == "why"


async def test_decide_edit_returns_none_when_should_edit_is_false(patch_httpx_client):
    patch_httpx_client(
        _FakeResponse(
            json_body={
                "message": {
                    "content": '{"should_edit": false, "proposed_text": "", "rationale": ""}'
                }
            }
        )
    )
    provider = OllamaProvider(model="test-model")

    decision = await provider.decide_edit([LLMMessage(role="user", content="review")], "orig")

    assert decision is None


async def test_decide_edit_returns_none_on_http_error(patch_httpx_client):
    patch_httpx_client(_FakeResponse(status_error=True))
    provider = OllamaProvider(model="test-model")

    decision = await provider.decide_edit([LLMMessage(role="user", content="review")], "orig")

    assert decision is None


async def test_decide_edit_returns_none_on_malformed_json_body(patch_httpx_client):
    # Regression test: response.json() used to be called outside the try/except,
    # so a non-JSON body would raise instead of degrading to None.
    patch_httpx_client(_FakeResponse(json_body=None, raw_text="not json"))
    provider = OllamaProvider(model="test-model")

    decision = await provider.decide_edit([LLMMessage(role="user", content="review")], "orig")

    assert decision is None
