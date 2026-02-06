"""
LLM Adapter Factory - Create adapters for different providers.

This factory pattern simplifies adapter creation and allows
easy switching between providers for A/B testing and benchmarking.

Supports:
- Cloud APIs: Gemini, Claude, OpenRouter, Cerebras, Cloudflare
- Local (Apple Silicon): MLX-based inference
- Local (NVIDIA GPU): vLLM with role-based model routing
- Local (Hybrid CPU+GPU): llama.cpp for massive models
"""

from typing import Optional
import os

from .base_adapter import BaseLLMAdapter
from .gemini_adapter import GeminiAdapter
from .claude_adapter import ClaudeAdapter
from .openrouter_adapter import OpenRouterAdapter
from .cerebras_adapter import CerebrasAdapter
from .cloudflare_adapter import CloudflareAdapter
from .local_adapter import LocalAdapter, check_local_available, get_local_models
from .vllm_adapter import VLLMAdapter, check_vllm_available, get_vllm_models, VLLM_MODELS
from .llamacpp_adapter import LlamaCppAdapter, check_llamacpp_available, get_llamacpp_models
from .ollama_adapter import OllamaAdapter, check_ollama_available, get_ollama_models


# Supported provider types
# vLLM supports role-based routing: vllm, vllm-coder, vllm-reasoning, vllm-creative, vllm-fast
# Ollama is recommended for Windows as it doesn't require compilation
SUPPORTED_PROVIDERS = [
    'gemini', 'claude', 'openrouter', 'cerebras', 'cloudflare', 'local',
    'vllm', 'vllm-coder', 'vllm-reasoning', 'vllm-creative', 'vllm-fast',
    'llamacpp', 'ollama'
]

# Default models per provider
DEFAULT_MODELS = {
    'gemini': 'models/gemini-2.5-flash-lite',
    'claude': 'claude-opus-4-20250514',
    'openrouter': 'nvidia/nemotron-nano-9b-v2:free',
    'cerebras': 'llama3.1-8b',
    'cloudflare': '@cf/meta/llama-3.1-8b-instruct',
    'local': 'mlx-community/Qwen2.5-1.5B-Instruct-4bit',
    # vLLM defaults (AWQ quantized for efficient VRAM usage)
    'vllm': 'Qwen/Qwen2.5-Coder-32B-Instruct-AWQ',
    'vllm-coder': 'Qwen/Qwen2.5-Coder-32B-Instruct-AWQ',
    'vllm-reasoning': 'casperhansen/deepseek-r1-distill-llama-70b-awq',
    'vllm-creative': 'casperhansen/mistral-small-24b-instruct-2501-awq',
    'vllm-fast': 'hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4',
    # llama.cpp defaults (GGUF for hybrid CPU+GPU)
    'llamacpp': 'DeepSeek-R1-Q4_K_M',
    # Ollama (easy local LLM, recommended for Windows)
    'ollama': 'qwen2.5-coder:32b',
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

    elif llm_type == 'local':
        if not check_local_available():
            raise ValueError(
                "Local MLX inference not available. "
                "Requires Apple Silicon Mac with MLX installed: pip install mlx mlx-lm"
            )

        return LocalAdapter(
            model=model,
            max_tokens=max_tokens
        )

    elif llm_type.startswith('vllm'):
        # Parse role from llm_type (e.g., 'vllm-coder' -> 'coder')
        if '-' in llm_type:
            role = llm_type.split('-', 1)[1]
        else:
            role = 'coder'  # Default role

        # Validate role
        valid_roles = ['coder', 'reasoning', 'creative', 'fast']
        if role not in valid_roles:
            raise ValueError(
                f"Unknown vLLM role: {role}. "
                f"Valid roles: {', '.join(valid_roles)}"
            )

        return VLLMAdapter(
            role=role,
            model=model,
            max_tokens=max_tokens,
            **kwargs
        )

    elif llm_type == 'llamacpp':
        return LlamaCppAdapter(
            model=model,
            max_tokens=max_tokens,
            **kwargs
        )

    elif llm_type == 'ollama':
        return OllamaAdapter(
            model=model,
            max_tokens=max_tokens,
            **kwargs
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
    elif llm_type == 'local':
        return get_local_models()
    elif llm_type.startswith('vllm'):
        # Return model IDs for all vLLM roles
        return [config['model'] for config in VLLM_MODELS.values()]
    elif llm_type == 'llamacpp':
        return list(get_llamacpp_models().keys())
    elif llm_type == 'ollama':
        return list(get_ollama_models().keys())
    else:
        return []


def check_provider_available(llm_type: str) -> bool:
    """
    Check if a provider is available (API key is set or local requirements met).

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
    elif llm_type == 'local':
        return check_local_available()
    elif llm_type.startswith('vllm'):
        # Parse role from llm_type
        if '-' in llm_type:
            role = llm_type.split('-', 1)[1]
        else:
            role = 'coder'
        return check_vllm_available(role)
    elif llm_type == 'llamacpp':
        return check_llamacpp_available()
    elif llm_type == 'ollama':
        return check_ollama_available()

    return False


def get_available_providers() -> list:
    """Get list of providers with configured API keys."""
    return [p for p in SUPPORTED_PROVIDERS if check_provider_available(p)]
