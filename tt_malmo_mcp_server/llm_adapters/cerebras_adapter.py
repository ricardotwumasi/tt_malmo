"""
Cerebras Adapter - Ultra-fast inference for real-time agent decisions.

Cerebras provides extremely fast inference, ideal for:
- Real-time agent decision loops
- Low-latency responses
- High-throughput benchmarking

Free tier: 30 RPM, 1M tokens/day
Models: Llama 3.1 8B, Llama 3.3 70B
"""

from typing import Optional, AsyncIterator
import httpx
from .base_adapter import BaseLLMAdapter


class CerebrasAdapter(BaseLLMAdapter):
    """
    Adapter for Cerebras Cloud API - ultra-fast LLM inference.

    Cerebras offers the fastest inference speeds, making it ideal
    for real-time agent decision-making in Minecraft.
    """

    API_BASE = "https://api.cerebras.ai/v1"

    # Available models
    MODELS = [
        "llama3.1-8b",
        "llama3.3-70b",
    ]

    def __init__(self, api_key: str,
                 model: str = "llama3.1-8b",
                 max_tokens: int = 1024):
        """
        Initialize Cerebras adapter.

        Args:
            api_key: Cerebras API key
            model: Model identifier (default: llama3.1-8b for speed)
            max_tokens: Maximum tokens to generate
        """
        super().__init__(api_key, model, max_tokens)

        # HTTP client for async requests
        self.client = httpx.AsyncClient(
            base_url=self.API_BASE,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0  # Short timeout - Cerebras is fast
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text using Cerebras.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text
        """
        try:
            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": 0.7,
                }
            )

            response.raise_for_status()
            data = response.json()

            return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            print(f"Cerebras API error: {e.response.status_code} - {e.response.text}")
            return f"[ERROR: HTTP {e.response.status_code}]"
        except Exception as e:
            print(f"Error calling Cerebras API: {e}")
            return f"[ERROR: {str(e)}]"

    async def generate_streaming(self, prompt: str, system_prompt: Optional[str] = None) -> AsyncIterator[str]:
        """
        Generate text with streaming using Cerebras.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Yields:
            Text chunks as they are generated
        """
        try:
            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            async with self.client.stream(
                "POST",
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": 0.7,
                    "stream": True,
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            import json
                            chunk = json.loads(data)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue

        except Exception as e:
            print(f"Error in Cerebras streaming: {e}")
            yield f"[ERROR: {str(e)}]"

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count (rough estimate).

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4

    @classmethod
    def list_models(cls) -> list:
        """List available models."""
        return cls.MODELS

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
