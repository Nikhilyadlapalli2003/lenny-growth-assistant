import pytest

from app.providers.factory import get_provider
from app.providers.ollama_provider import OllamaProvider
from app.providers.anthropic_provider import AnthropicProvider


def test_factory_defaults_to_ollama(monkeypatch):
    provider = get_provider(None)
    assert isinstance(provider, (OllamaProvider, AnthropicProvider))


def test_factory_respects_explicit_choice():
    assert isinstance(get_provider("anthropic"), AnthropicProvider)
    assert isinstance(get_provider("ollama"), OllamaProvider)


@pytest.mark.asyncio
async def test_anthropic_provider_without_key_yields_helpful_message():
    provider = AnthropicProvider(api_key="")
    chunks = []
    async for token in provider.generate(messages=[{"role": "user", "content": "hi"}], system_prompt="sys"):
        chunks.append(token)
    text = "".join(chunks)
    assert "ANTHROPIC_API_KEY" in text
