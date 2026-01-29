"""
Tests for OpenRouter Adapter.

Tests cover:
- Adapter initialization
- API request formation
- Response parsing
- Error handling
- Free model listing
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestOpenRouterAdapterInit:
    """Test OpenRouter adapter initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        from llm_adapters.openrouter_adapter import OpenRouterAdapter

        adapter = OpenRouterAdapter(api_key="test-key")

        assert adapter.api_key == "test-key"
        assert adapter.model == "deepseek/deepseek-r1:free"
        assert adapter.max_tokens == 1024
        assert "Malmo" in adapter.site_name

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        from llm_adapters.openrouter_adapter import OpenRouterAdapter

        adapter = OpenRouterAdapter(
            api_key="test-key",
            model="meta-llama/llama-3.3-70b-instruct:free",
            max_tokens=512,
            site_url="https://example.com",
            site_name="Test Site"
        )

        assert adapter.model == "meta-llama/llama-3.3-70b-instruct:free"
        assert adapter.max_tokens == 512
        assert adapter.site_url == "https://example.com"
        assert adapter.site_name == "Test Site"


class TestOpenRouterAdapterGenerate:
    """Test OpenRouter adapter generate method."""

    @pytest.mark.asyncio
    async def test_generate_request_format(self):
        """Test that API requests are formatted correctly."""
        from llm_adapters.openrouter_adapter import OpenRouterAdapter

        adapter = OpenRouterAdapter(api_key="test-key")

        # Mock the httpx client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "Test response"}}
            ]
        }
        mock_response.raise_for_status = MagicMock()

        adapter.client.post = AsyncMock(return_value=mock_response)

        result = await adapter.generate("Hello!")

        assert result == "Test response"

        # Verify request format
        call_args = adapter.client.post.call_args
        assert call_args[0][0] == "/chat/completions"
        request_json = call_args[1]["json"]
        assert request_json["model"] == "deepseek/deepseek-r1:free"
        assert request_json["messages"][0]["role"] == "user"
        assert request_json["messages"][0]["content"] == "Hello!"

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self):
        """Test generation with system prompt."""
        from llm_adapters.openrouter_adapter import OpenRouterAdapter

        adapter = OpenRouterAdapter(api_key="test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_response.raise_for_status = MagicMock()

        adapter.client.post = AsyncMock(return_value=mock_response)

        await adapter.generate(
            "What is your purpose?",
            system_prompt="You are a Minecraft agent."
        )

        call_args = adapter.client.post.call_args
        messages = call_args[1]["json"]["messages"]

        # Should have system message first, then user message
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a Minecraft agent."
        assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_generate_error_handling(self):
        """Test error handling."""
        from llm_adapters.openrouter_adapter import OpenRouterAdapter
        import httpx

        adapter = OpenRouterAdapter(api_key="test-key")

        # Simulate HTTP error
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limited"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limited", request=MagicMock(), response=mock_response
        )

        adapter.client.post = AsyncMock(return_value=mock_response)

        result = await adapter.generate("Test")

        assert "[ERROR:" in result


class TestOpenRouterFreeModels:
    """Test free model listing."""

    def test_list_free_models(self):
        """Test that free models are listed."""
        from llm_adapters.openrouter_adapter import OpenRouterAdapter

        models = OpenRouterAdapter.list_free_models()

        assert len(models) > 0
        assert all(":free" in m for m in models)
        assert "deepseek/deepseek-r1:free" in models


class TestOpenRouterAdapterTokenCounting:
    """Test token counting."""

    def test_count_tokens_estimate(self):
        """Test token estimation."""
        from llm_adapters.openrouter_adapter import OpenRouterAdapter

        adapter = OpenRouterAdapter(api_key="test-key")

        # Test rough estimation (4 chars per token)
        count = adapter.count_tokens("A" * 40)

        assert count == 10


class TestOpenRouterAdapterCleanup:
    """Test resource cleanup."""

    @pytest.mark.asyncio
    async def test_close(self):
        """Test client cleanup."""
        from llm_adapters.openrouter_adapter import OpenRouterAdapter

        adapter = OpenRouterAdapter(api_key="test-key")
        adapter.client.aclose = AsyncMock()

        await adapter.close()

        adapter.client.aclose.assert_called_once()
