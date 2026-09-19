"""
Cloud LLM provider using the Anthropic API.
"""
import logging
from typing import AsyncGenerator

import anthropic

from app.config import get_settings
from app.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)
settings = get_settings()


class AnthropicProvider(BaseLLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_MODEL
        self._client = anthropic.AsyncAnthropic(api_key=self.api_key) if self.api_key else None

    async def generate(
        self,
        messages: list[dict],
        system_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        if not self._client:
            yield "No ANTHROPIC_API_KEY configured. Set it in .env or switch provider to 'ollama'."
            return
        try:
            async with self._client.messages.stream(
                model=self.model,
                system=system_prompt,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except anthropic.AuthenticationError:
            logger.exception("Anthropic auth failed")
            yield "Anthropic authentication failed - check ANTHROPIC_API_KEY."
        except anthropic.APIError:
            logger.exception("Anthropic API error")
            yield "The Anthropic API returned an error. Falling back is recommended (switch provider to 'ollama')."

    async def health_check(self) -> bool:
        return bool(self.api_key)
