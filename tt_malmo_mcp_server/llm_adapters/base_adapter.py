"""
Base LLM Adapter - Abstract interface for all LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMAdapter(ABC):
    """
    Abstract base class for LLM adapters.

    All LLM providers (Claude, Gemini, etc.) must implement this interface.
    """

    def __init__(self, api_key: str, model: str, max_tokens: int = 1024):
        """
        Initialize LLM adapter.

        Args:
            api_key: API key for the provider
            model: Model identifier
            max_tokens: Maximum tokens to generate
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text from prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    async def generate_streaming(self, prompt: str, system_prompt: Optional[str] = None):
        """
        Generate text with streaming.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Yields:
            Text chunks as they are generated
        """
        pass

    def get_model_name(self) -> str:
        """
        Get model name.

        Returns:
            Model identifier
        """
        return self.model
