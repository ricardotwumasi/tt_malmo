"""
Ollama Adapter - Easy local LLM inference on Windows/Mac/Linux.

Ollama provides a simple way to run local LLMs with GPU acceleration
without requiring compilation or build tools.

Installation:
    1. Download from: https://ollama.com/download
    2. Install (user-level install on Windows works without admin)
    3. Run: ollama serve
    4. Pull a model: ollama pull qwen2.5-coder:32b

Ollama provides an OpenAI-compatible API at http://localhost:11434/v1
"""

import os
import json
from typing import Optional, AsyncIterator, Dict, Any
import httpx

from .base_adapter import BaseLLMAdapter


# Default configuration with environment variable overrides
OLLAMA_CONFIG = {
    "url": os.getenv("OLLAMA_URL", "http://localhost:11434/v1"),
    "model": os.getenv("OLLAMA_MODEL", "qwen2.5-coder:32b"),
    "description": "Easy local LLM inference with Ollama",
}

# Recommended models for Ollama (pulled from Ollama registry)
RECOMMENDED_MODELS = {
    "qwen2.5-coder:32b": {
        "name": "Qwen 2.5 Coder 32B",
        "size": "~20GB",
        "speed": "10-30 tokens/sec",
        "description": "Excellent coding model, great for agents",
        "pull_cmd": "ollama pull qwen2.5-coder:32b",
    },
    "deepseek-r1:70b": {
        "name": "DeepSeek R1 70B",
        "size": "~40GB",
        "speed": "5-15 tokens/sec",
        "description": "Strong reasoning, good for complex tasks",
        "pull_cmd": "ollama pull deepseek-r1:70b",
    },
    "llama3.3:70b": {
        "name": "Llama 3.3 70B",
        "size": "~40GB",
        "speed": "5-15 tokens/sec",
        "description": "High-quality general-purpose model",
        "pull_cmd": "ollama pull llama3.3:70b",
    },
    "codestral:22b": {
        "name": "Codestral 22B",
        "size": "~13GB",
        "speed": "20-40 tokens/sec",
        "description": "Fast coding model from Mistral",
        "pull_cmd": "ollama pull codestral:22b",
    },
    "qwen2.5:7b": {
        "name": "Qwen 2.5 7B",
        "size": "~4.5GB",
        "speed": "50-100 tokens/sec",
        "description": "Fast, lightweight model for testing",
        "pull_cmd": "ollama pull qwen2.5:7b",
    },
}


def check_ollama_available() -> bool:
    """
    Check if Ollama server is available.

    Returns:
        True if Ollama server responds at the configured URL
    """
    try:
        import httpx
        # Ollama uses /api/tags for listing models
        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


def get_ollama_models() -> Dict[str, Dict[str, str]]:
    """Get recommended models for Ollama."""
    return RECOMMENDED_MODELS


class OllamaAdapter(BaseLLMAdapter):
    """
    Ollama local inference adapter.

    Uses the OpenAI-compatible API provided by Ollama.
    Ollama handles model downloading, GPU acceleration, and serving automatically.

    Features:
    - Automatic GPU detection and utilization
    - Easy model management (pull, run, stop)
    - OpenAI-compatible API
    - Works on Windows/Mac/Linux

    Quick Start:
        1. Install Ollama: https://ollama.com/download
        2. Start server: ollama serve
        3. Pull model: ollama pull qwen2.5-coder:32b
        4. Use this adapter

    Usage:
        adapter = OllamaAdapter(model="qwen2.5-coder:32b")
        response = await adapter.generate("Write a Python function...")
    """

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        timeout: float = 120.0,
    ):
        """
        Initialize Ollama adapter.

        Args:
            model: Model name (e.g., "qwen2.5-coder:32b")
            base_url: URL of Ollama server (default: http://localhost:11434/v1)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or OLLAMA_CONFIG["url"]
        actual_model = model or OLLAMA_CONFIG["model"]

        # Initialize base class (api_key is None for local inference)
        super().__init__(api_key="", model=actual_model, max_tokens=max_tokens)

        self.temperature = temperature
        self.timeout = timeout

        # HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text using Ollama.

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

            print(f"[OllamaAdapter] Generating with {self.model}...")

            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                }
            )

            response.raise_for_status()
            data = response.json()

            return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.text
            except Exception:
                pass
            print(f"[OllamaAdapter] HTTP error: {e.response.status_code} - {error_detail}")
            return f"[ERROR: HTTP {e.response.status_code}]"
        except httpx.ConnectError:
            print(f"[OllamaAdapter] Connection failed to {self.base_url}")
            print(f"[OllamaAdapter] Is Ollama running? Start with: ollama serve")
            return f"[ERROR: Cannot connect to Ollama at {self.base_url}]"
        except httpx.ReadTimeout:
            print(f"[OllamaAdapter] Request timed out after {self.timeout}s")
            return f"[ERROR: Request timed out]"
        except Exception as e:
            print(f"[OllamaAdapter] Error: {e}")
            return f"[ERROR: {str(e)}]"

    async def generate_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Generate text with streaming using Ollama.

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

            print(f"[OllamaAdapter] Starting streaming generation with {self.model}...")

            async with self.client.stream(
                "POST",
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "stream": True,
                }
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    # Handle SSE format
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        if data_str == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data_str)
                            content = (
                                chunk.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content", "")
                            )
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

        except httpx.ConnectError:
            yield f"[ERROR: Cannot connect to Ollama at {self.base_url}]"
        except httpx.ReadTimeout:
            yield f"[ERROR: Request timed out]"
        except Exception as e:
            print(f"[OllamaAdapter] Streaming error: {e}")
            yield f"[ERROR: {str(e)}]"

    async def list_local_models(self) -> list:
        """
        List models available locally in Ollama.

        Returns:
            List of model names
        """
        try:
            # Use Ollama's native API for listing models
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:11434/api/tags",
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            print(f"[OllamaAdapter] Error listing models: {e}")
            return []

    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama registry.

        Note: This can take a while for large models.

        Args:
            model_name: Name of model to pull (e.g., "qwen2.5-coder:32b")

        Returns:
            True if successful
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/pull",
                    json={"name": model_name},
                    timeout=3600.0  # 1 hour timeout for large models
                )
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"[OllamaAdapter] Error pulling model: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return RECOMMENDED_MODELS.get(self.model, {
            "name": self.model,
            "description": "Custom Ollama model"
        })

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation).

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token for English text
        return len(text) // 4

    @classmethod
    def list_recommended_models(cls) -> Dict[str, Dict[str, str]]:
        """List recommended models for Ollama."""
        return RECOMMENDED_MODELS

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
