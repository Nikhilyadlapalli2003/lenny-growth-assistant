"""
Local LLM provider - talks to a locally running Ollama daemon.
This is the mandatory provider for the evaluation demo.
"""
import json
import logging
from typing import AsyncGenerator

import httpx

from app.config import get_settings
from app.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)
settings = get_settings()


class OllamaProvider(BaseLLMProvider):
    name = "ollama"

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL

    async def generate(
        self,
        messages: list[dict],
        system_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": True,
            "options": {"temperature": temperature},
        }
        try:
            async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        logger.error("Ollama error %s: %s", response.status_code, body)
                        yield f"[Ollama error {response.status_code}] Is `ollama serve` running and is `{self.model}` pulled?"
                        return
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if chunk.get("done"):
                            break
        except httpx.ConnectError:
            logger.exception("Could not reach Ollama at %s", self.base_url)
            yield (
                "I couldn't reach the local Ollama server. Start it with `ollama serve` "
                f"and make sure `{self.model}` is pulled (`ollama pull {self.model}`)."
            )
        except httpx.TimeoutException:
            logger.exception("Ollama request timed out")
            yield "The local model timed out. Try a smaller model or a shorter prompt."

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except httpx.HTTPError:
            return False
