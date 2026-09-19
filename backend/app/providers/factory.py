"""
Runtime provider selector. Reads DEFAULT_LLM_PROVIDER from settings, with an
optional per-request override (query param / header), enabling a live toggle
without redeploying.
"""
from app.config import get_settings
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import BaseLLMProvider
from app.providers.ollama_provider import OllamaProvider

settings = get_settings()

_PROVIDERS: dict[str, type[BaseLLMProvider]] = {
    "ollama": OllamaProvider,
    "anthropic": AnthropicProvider,
}


def get_provider(name: str | None = None) -> BaseLLMProvider:
    chosen = name if (name and settings.ALLOW_PROVIDER_OVERRIDE_VIA_HEADER) else None
    chosen = chosen or settings.DEFAULT_LLM_PROVIDER
    provider_cls = _PROVIDERS.get(chosen, OllamaProvider)
    return provider_cls()
