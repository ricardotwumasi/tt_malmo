"""
Claude Adapter - Anthropic API integration.

Supports Claude Opus 4.5 and other Claude models.
"""

from typing import Optional
import anthropic
from .base_adapter import BaseLLMAdapter


class ClaudeAdapter(BaseLLMAdapter):
    """
    Adapter for Anthropic's Claude models.

    Uses the official Anthropic Python SDK.
    """

    def __init__(self, api_key: str,
                 model: str = "claude-opus-4-20250514",
                 max_tokens: int = 1024):
        """
        Initialize Claude adapter.

        Args:
            api_key: Anthropic API key
            model: Claude model identifier (default: claude-opus-4-20250514)
            max_tokens: Maximum tokens to generate
        """
        super().__init__(api_key, model, max_tokens)
        self.client = anthropic.Anthropic(api_key=api_key)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text using Claude.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text
        """
        try:
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": messages
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            response = self.client.messages.create(**kwargs)

            # Extract text from response
            return response.content[0].text

        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return f"[ERROR: {str(e)}]"

    async def generate_streaming(self, prompt: str, system_prompt: Optional[str] = None):
        """
        Generate text with streaming using Claude.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Yields:
            Text chunks as they are generated
        """
        try:
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": messages
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            with self.client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            print(f"Error in Claude streaming: {e}")
            yield f"[ERROR: {str(e)}]"

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using Claude's tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            Token count
        """
        try:
            response = self.client.count_tokens(text)
            return response.token_count
        except Exception as e:
            print(f"Error counting tokens: {e}")
            # Rough estimate: 4 chars per token
            return len(text) // 4
