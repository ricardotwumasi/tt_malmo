"""
Tests for Gemini Adapter.

Tests cover:
- Adapter initialization
- Generate method
- Streaming generation
- Token counting
- Error handling
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGeminiAdapterInit:
    """Test Gemini adapter initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        with patch('llm_adapters.gemini_adapter.genai') as mock_genai:
            from llm_adapters.gemini_adapter import GeminiAdapter

            adapter = GeminiAdapter(api_key="test-key")

            assert adapter.api_key == "test-key"
            assert adapter.model == "models/gemini-2.5-flash-lite"
            assert adapter.max_tokens == 1024
            mock_genai.configure.assert_called_once_with(api_key="test-key")

    def test_init_with_custom_model(self):
        """Test initialization with custom model."""
        with patch('llm_adapters.gemini_adapter.genai') as mock_genai:
            from llm_adapters.gemini_adapter import GeminiAdapter

            adapter = GeminiAdapter(
                api_key="test-key",
                model="models/gemini-2.5-pro",
                max_tokens=2048
            )

            assert adapter.model == "models/gemini-2.5-pro"
            assert adapter.max_tokens == 2048


class TestGeminiAdapterGenerate:
    """Test Gemini adapter generate method."""

    @pytest.mark.asyncio
    async def test_generate_basic(self):
        """Test basic text generation."""
        with patch('llm_adapters.gemini_adapter.genai') as mock_genai:
            # Setup mock
            mock_response = MagicMock()
            mock_response.text = "Test response from Gemini"

            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            from llm_adapters.gemini_adapter import GeminiAdapter
            adapter = GeminiAdapter(api_key="test-key")

            result = await adapter.generate("Hello, Gemini!")

            assert result == "Test response from Gemini"
            mock_model.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self):
        """Test generation with system prompt."""
        with patch('llm_adapters.gemini_adapter.genai') as mock_genai:
            mock_response = MagicMock()
            mock_response.text = "System-aware response"

            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            from llm_adapters.gemini_adapter import GeminiAdapter
            adapter = GeminiAdapter(api_key="test-key")

            result = await adapter.generate(
                "What is your role?",
                system_prompt="You are a helpful assistant."
            )

            # Verify system prompt was prepended
            call_args = mock_model.generate_content.call_args
            prompt = call_args[0][0]
            assert "You are a helpful assistant." in prompt
            assert "What is your role?" in prompt

    @pytest.mark.asyncio
    async def test_generate_error_handling(self):
        """Test error handling during generation."""
        with patch('llm_adapters.gemini_adapter.genai') as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = Exception("API Error")
            mock_genai.GenerativeModel.return_value = mock_model

            from llm_adapters.gemini_adapter import GeminiAdapter
            adapter = GeminiAdapter(api_key="test-key")

            result = await adapter.generate("Test prompt")

            assert "[ERROR:" in result


class TestGeminiAdapterStreaming:
    """Test Gemini adapter streaming generation."""

    @pytest.mark.asyncio
    async def test_streaming_basic(self):
        """Test basic streaming generation."""
        with patch('llm_adapters.gemini_adapter.genai') as mock_genai:
            # Create mock chunks
            chunk1 = MagicMock()
            chunk1.text = "Hello "
            chunk2 = MagicMock()
            chunk2.text = "World!"

            mock_model = MagicMock()
            mock_model.generate_content.return_value = [chunk1, chunk2]
            mock_genai.GenerativeModel.return_value = mock_model

            from llm_adapters.gemini_adapter import GeminiAdapter
            adapter = GeminiAdapter(api_key="test-key")

            chunks = []
            async for chunk in adapter.generate_streaming("Say hello"):
                chunks.append(chunk)

            assert len(chunks) == 2
            assert chunks[0] == "Hello "
            assert chunks[1] == "World!"


class TestGeminiAdapterTokenCounting:
    """Test Gemini adapter token counting."""

    def test_count_tokens_success(self):
        """Test successful token counting."""
        with patch('llm_adapters.gemini_adapter.genai') as mock_genai:
            mock_response = MagicMock()
            mock_response.total_tokens = 10

            mock_model = MagicMock()
            mock_model.count_tokens.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            from llm_adapters.gemini_adapter import GeminiAdapter
            adapter = GeminiAdapter(api_key="test-key")

            count = adapter.count_tokens("Hello world")

            assert count == 10

    def test_count_tokens_fallback(self):
        """Test token counting fallback on error."""
        with patch('llm_adapters.gemini_adapter.genai') as mock_genai:
            mock_model = MagicMock()
            mock_model.count_tokens.side_effect = Exception("Error")
            mock_genai.GenerativeModel.return_value = mock_model

            from llm_adapters.gemini_adapter import GeminiAdapter
            adapter = GeminiAdapter(api_key="test-key")

            # Should fall back to character-based estimate
            count = adapter.count_tokens("A" * 40)

            assert count == 10  # 40 chars / 4 = 10


class TestGeminiAdapterIntegration:
    """Integration tests requiring API key."""

    @pytest.mark.skipif(
        not os.getenv('GOOGLE_API_KEY'),
        reason="Requires GOOGLE_API_KEY"
    )
    @pytest.mark.asyncio
    async def test_real_api_call(self):
        """Test real API call (requires API key)."""
        from llm_adapters.gemini_adapter import GeminiAdapter

        adapter = GeminiAdapter(
            api_key=os.getenv('GOOGLE_API_KEY'),
            model="models/gemini-2.5-flash-lite"
        )

        result = await adapter.generate("Say 'hello' and nothing else.")

        assert len(result) > 0
        assert "hello" in result.lower()
