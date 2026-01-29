"""
Cloudflare Workers AI Adapter - Reliable inference at the edge.

Cloudflare provides:
- 10,000 Neurons/day free (roughly 10k requests)
- Models: Llama 3.x 70B, DeepSeek variants
- Global edge deployment for low latency
- Reliable infrastructure

Great for production deployments with predictable workloads.
"""

from typing import Optional, AsyncIterator
import httpx
from .base_adapter import BaseLLMAdapter


class CloudflareAdapter(BaseLLMAdapter):
    """
    Adapter for Cloudflare Workers AI.

    Cloudflare offers reliable edge-deployed AI inference,
    ideal for production deployments.
    """

    # Available models (subset of Workers AI models)
    MODELS = [
        "@cf/meta/llama-3.1-70b-instruct",
        "@cf/meta/llama-3.1-8b-instruct",
        "@cf/deepseek-ai/deepseek-r1-distill-llama-70b",
        "@cf/qwen/qwen1.5-14b-chat-awq",
        "@cf/mistral/mistral-7b-instruct-v0.1",
    ]

    def __init__(self, api_token: str,
                 account_id: str,
                 model: str = "@cf/meta/llama-3.1-8b-instruct",
                 max_tokens: int = 1024):
        """
        Initialize Cloudflare Workers AI adapter.

        Args:
            api_token: Cloudflare API token
            account_id: Cloudflare account ID
            model: Model identifier (default: Llama 3.1 8B for speed)
            max_tokens: Maximum tokens to generate
        """
        super().__init__(api_token, model, max_tokens)
        self.account_id = account_id

        # API endpoint
        self.api_base = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run"

        # HTTP client for async requests
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text using Cloudflare Workers AI.

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

            url = f"{self.api_base}/{self.model}"

            response = await self.client.post(
                url,
                json={
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": 0.7,
                }
            )

            response.raise_for_status()
            data = response.json()

            # Cloudflare returns result in a different format
            if data.get("success"):
                result = data.get("result", {})
                return result.get("response", "")
            else:
                errors = data.get("errors", [])
                return f"[ERROR: {errors}]"

        except httpx.HTTPStatusError as e:
            print(f"Cloudflare API error: {e.response.status_code} - {e.response.text}")
            return f"[ERROR: HTTP {e.response.status_code}]"
        except Exception as e:
            print(f"Error calling Cloudflare API: {e}")
            return f"[ERROR: {str(e)}]"

    async def generate_streaming(self, prompt: str, system_prompt: Optional[str] = None) -> AsyncIterator[str]:
        """
        Generate text with streaming using Cloudflare Workers AI.

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

            url = f"{self.api_base}/{self.model}"

            async with self.client.stream(
                "POST",
                url,
                json={
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
                            content = chunk.get("response", "")
                            if content:
                                yield content
                        except Exception:
                            continue

        except Exception as e:
            print(f"Error in Cloudflare streaming: {e}")
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
