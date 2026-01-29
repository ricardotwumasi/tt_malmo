"""
LLM Adapters - Interfaces to different LLM providers.

Supports:
- Gemini (Google AI API) - Free tier with gemini-2.5-flash-lite
- Claude (Anthropic API) - Paid tier with claude-opus-4
- OpenRouter (Gateway) - Access to many free models
- Cerebras (Ultra-fast) - Free tier, fastest inference
- Cloudflare (Workers AI) - Free tier, edge deployment
"""

from .base_adapter import BaseLLMAdapter
from .claude_adapter import ClaudeAdapter
from .gemini_adapter import GeminiAdapter
from .openrouter_adapter import OpenRouterAdapter
from .cerebras_adapter import CerebrasAdapter
from .cloudflare_adapter import CloudflareAdapter
from .factory import (
    create_adapter,
    list_providers,
    get_default_model,
    get_available_models,
    check_provider_available,
    get_available_providers,
    SUPPORTED_PROVIDERS,
)

__all__ = [
    # Base
    'BaseLLMAdapter',
    # Adapters
    'ClaudeAdapter',
    'GeminiAdapter',
    'OpenRouterAdapter',
    'CerebrasAdapter',
    'CloudflareAdapter',
    # Factory functions
    'create_adapter',
    'list_providers',
    'get_default_model',
    'get_available_models',
    'check_provider_available',
    'get_available_providers',
    'SUPPORTED_PROVIDERS',
]
