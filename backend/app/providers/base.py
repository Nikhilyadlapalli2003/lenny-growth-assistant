"""
Provider-agnostic interface every LLM backend must implement.
Swapping providers (ollama <-> anthropic) never requires touching call sites -
callers only depend on this interface, obtained via get_provider().
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseLLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        system_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        """Yield response text incrementally (token/chunk stream)."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError
