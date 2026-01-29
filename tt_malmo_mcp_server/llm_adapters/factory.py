"""
LLM Adapter Factory - Create adapters for different providers.

This factory pattern simplifies adapter creation and allows
easy switching between providers for A/B testing and benchmarking.
"""

from typing import Optional
import os

from .base_adapter import BaseLLMAdapter
from .gemini_adapter import GeminiAdapter
from .claude_adapter import ClaudeAdapter
from .openrouter_adapter import OpenRouterAdapter
from .cerebras_adapter import CerebrasAdapter
from .cloudflare_adapter import CloudflareAdapter


# Supported provider types
SUPPORTED_PROVIDERS = ['gemini', 'claude', 'openrouter', 'cerebras', 'cloudflare']

# Default models per provider
DEFAULT_MODELS = {
    'gemini': 'models/gemini-2.5-flash-lite',
    'claude': 'claude-opus-4-20250514',
    'openrouter': 'deepseek/deepseek-r1:free',
    'cerebras': 'llama3.1-8b',
    'cloudflare': '@cf/meta/llama-3.1-8b-instruct',
}


def create_adapter(
    llm_type: str,
    model: Optional[str] = None,
    max_tokens: int = 1024,
    **kwargs
) -> BaseLLMAdapter:
    """
    Create an LLM adapter based on provider type.

    Args:
        llm_type: Provider type ('gemini', 'claude', 'openrouter', 'cerebras', 'cloudflare')
        model: Optional model override (uses default if not specified)
        max_tokens: Maximum tokens to generate
        **kwargs: Additional provider-specific arguments

    Returns:
        Configured LLM adapter

    Raises:
        ValueError: If provider type is unknown or API key is missing
    """
    llm_type = llm_type.lower()

    if llm_type not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unknown LLM type: {llm_type}. "
            f"Supported types: {', '.join(SUPPORTED_PROVIDERS)}"
        )

    # Use default model if not specified
    if model is None:
        model = DEFAULT_MODELS[llm_type]

    # Create adapter based on type
    if llm_type == 'gemini':
        api_key = kwargs.get('api_key') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        return GeminiAdapter(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens
        )

    elif llm_type == 'claude':
        api_key = kwargs.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        return ClaudeAdapter(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens
        )

    elif llm_type == 'openrouter':
        api_key = kwargs.get('api_key') or os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")

        return OpenRouterAdapter(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            site_url=kwargs.get('site_url', 'https://github.com/ricardotwumasi/tt_malmo'),
            site_name=kwargs.get('site_name', 'Malmo AI Benchmark')
        )

    elif llm_type == 'cerebras':
        api_key = kwargs.get('api_key') or os.getenv('CEREBRAS_API_KEY')
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY environment variable not set")

        return CerebrasAdapter(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens
        )

    elif llm_type == 'cloudflare':
        api_token = kwargs.get('api_token') or os.getenv('CLOUDFLARE_API_TOKEN')
        account_id = kwargs.get('account_id') or os.getenv('CLOUDFLARE_ACCOUNT_ID')

        if not api_token:
            raise ValueError("CLOUDFLARE_API_TOKEN environment variable not set")
        if not account_id:
            raise ValueError("CLOUDFLARE_ACCOUNT_ID environment variable not set")

        return CloudflareAdapter(
            api_token=api_token,
            account_id=account_id,
            model=model,
            max_tokens=max_tokens
        )

    # Should never reach here due to earlier check
    raise ValueError(f"Unknown LLM type: {llm_type}")


def list_providers() -> list:
    """List all supported LLM providers."""
    return SUPPORTED_PROVIDERS


def get_default_model(llm_type: str) -> str:
    """Get default model for a provider."""
    return DEFAULT_MODELS.get(llm_type.lower(), "unknown")


def get_available_models(llm_type: str) -> list:
    """Get list of available models for a provider."""
    llm_type = llm_type.lower()

    if llm_type == 'gemini':
        return ['models/gemini-2.5-flash-lite', 'models/gemini-2.5-pro']
    elif llm_type == 'claude':
        return ['claude-opus-4-20250514', 'claude-sonnet-4-20250514']
    elif llm_type == 'openrouter':
        return OpenRouterAdapter.FREE_MODELS
    elif llm_type == 'cerebras':
        return CerebrasAdapter.MODELS
    elif llm_type == 'cloudflare':
        return CloudflareAdapter.MODELS
    else:
        return []


def check_provider_available(llm_type: str) -> bool:
    """
    Check if a provider is available (API key is set).

    Args:
        llm_type: Provider type

    Returns:
        True if provider can be used
    """
    llm_type = llm_type.lower()

    if llm_type == 'gemini':
        return bool(os.getenv('GOOGLE_API_KEY'))
    elif llm_type == 'claude':
        return bool(os.getenv('ANTHROPIC_API_KEY'))
    elif llm_type == 'openrouter':
        return bool(os.getenv('OPENROUTER_API_KEY'))
    elif llm_type == 'cerebras':
        return bool(os.getenv('CEREBRAS_API_KEY'))
    elif llm_type == 'cloudflare':
        return bool(os.getenv('CLOUDFLARE_API_TOKEN') and os.getenv('CLOUDFLARE_ACCOUNT_ID'))

    return False


def get_available_providers() -> list:
    """Get list of providers with configured API keys."""
    return [p for p in SUPPORTED_PROVIDERS if check_provider_available(p)]
