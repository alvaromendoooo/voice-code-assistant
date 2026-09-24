from app.agent.llm_provider import OllamaProvider, StubLLMProvider
from app.main import _build_llm_provider


def test_explicit_stub_provider(monkeypatch):
    monkeypatch.setenv("VCA_LLM_PROVIDER", "stub")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    assert isinstance(_build_llm_provider(), StubLLMProvider)


def test_explicit_ollama_provider(monkeypatch):
    monkeypatch.setenv("VCA_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

    provider = _build_llm_provider()

    assert isinstance(provider, OllamaProvider)
    assert provider._model == "qwen2.5-coder:7b"


def test_falls_back_to_stub_when_nothing_configured(monkeypatch):
    monkeypatch.delenv("VCA_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    assert isinstance(_build_llm_provider(), StubLLMProvider)
