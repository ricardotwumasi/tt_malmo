"""
LLM Adapters - Interfaces to different LLM providers.

Supports:
- Claude (Anthropic API)
- Gemini (Google AI API)
"""

from .base_adapter import BaseLLMAdapter
from .claude_adapter import ClaudeAdapter
from .gemini_adapter import GeminiAdapter

__all__ = ['BaseLLMAdapter', 'ClaudeAdapter', 'GeminiAdapter']
