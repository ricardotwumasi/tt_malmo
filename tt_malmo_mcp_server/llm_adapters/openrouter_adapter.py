"""
OpenRouter Adapter - Access to multiple free-tier LLM models.

OpenRouter provides a unified API gateway to many models with free tiers.
Model availability changes - check https://openrouter.ai/models?q=:free

Rate limits: 20 RPM, varies by model
"""

from typing import Optional, AsyncIterator
import httpx
from .base_adapter import BaseLLMAdapter


class OpenRouterAdapter(BaseLLMAdapter):
    """
    Adapter for OpenRouter API - gateway to multiple LLM providers.

    OpenRouter provides access to many models through a single API,
    including free tiers perfect for development and benchmarking.
    """

    API_BASE = "https://openrouter.ai/api/v1"

    # Available free models (updated January 2025)
    FREE_MODELS = [
        "qwen/qwen3-coder:free",
        "nvidia/nemotron-nano-9b-v2:free",
        "z-ai/glm-4.5-air:free",
        "liquid/lfm-2.5-1.2b-instruct:free",
        "openai/gpt-oss-20b:free",
    ]

    def __init__(self, api_key: str,
                 model: str = "nvidia/nemotron-nano-9b-v2:free",
                 max_tokens: int = 1024,
                 site_url: str = "https://github.com/ricardotwumasi/tt_malmo",
                 site_name: str = "Malmo AI Benchmark"):
        """
        Initialize OpenRouter adapter.

        Args:
            api_key: OpenRouter API key
            model: Model identifier (default: deepseek/deepseek-r1:free)
            max_tokens: Maximum tokens to generate
            site_url: Your site URL (required by OpenRouter)
            site_name: Your site name (required by OpenRouter)
        """
        super().__init__(api_key, model, max_tokens)
        self.site_url = site_url
        self.site_name = site_name

        # HTTP client for async requests
        self.client = httpx.AsyncClient(
            base_url=self.API_BASE,
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": site_url,
                "X-Title": site_name,
                "Content-Type": "application/json"
            },
            timeout=60.0
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text using OpenRouter.

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
            print(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
            return f"[ERROR: HTTP {e.response.status_code}]"
        except Exception as e:
            print(f"Error calling OpenRouter API: {e}")
            return f"[ERROR: {str(e)}]"

    async def generate_streaming(self, prompt: str, system_prompt: Optional[str] = None) -> AsyncIterator[str]:
        """
        Generate text with streaming using OpenRouter.

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
            print(f"Error in OpenRouter streaming: {e}")
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
    def list_free_models(cls) -> list:
        """List available free models."""
        return cls.FREE_MODELS

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
