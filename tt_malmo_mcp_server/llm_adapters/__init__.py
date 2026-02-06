"""
LLM Adapters - Interfaces to different LLM providers.

Supports:
- Gemini (Google AI API) - Free tier with gemini-2.5-flash-lite
- Claude (Anthropic API) - Paid tier with claude-opus-4
- OpenRouter (Gateway) - Access to many free models
- Cerebras (Ultra-fast) - Free tier, fastest inference
- Cloudflare (Workers AI) - Free tier, edge deployment
- Local (MLX) - On-device inference for Apple Silicon, no API needed
- vLLM (NVIDIA GPU) - High-performance local inference with role-based routing
- llama.cpp (Hybrid CPU+GPU) - Run massive models (405B+) with RAM offloading
- Ollama (Easy local LLM) - Recommended for Windows, no compilation needed
"""

from .base_adapter import BaseLLMAdapter
from .claude_adapter import ClaudeAdapter
from .gemini_adapter import GeminiAdapter
from .openrouter_adapter import OpenRouterAdapter
from .cerebras_adapter import CerebrasAdapter
from .cloudflare_adapter import CloudflareAdapter
from .local_adapter import LocalAdapter, check_local_available
from .vllm_adapter import VLLMAdapter, check_vllm_available, get_vllm_models
from .llamacpp_adapter import LlamaCppAdapter, check_llamacpp_available, get_llamacpp_models
from .ollama_adapter import OllamaAdapter, check_ollama_available, get_ollama_models
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
    # Cloud Adapters
    'ClaudeAdapter',
    'GeminiAdapter',
    'OpenRouterAdapter',
    'CerebrasAdapter',
    'CloudflareAdapter',
    # Local Adapters
    'LocalAdapter',
    'VLLMAdapter',
    'LlamaCppAdapter',
    'OllamaAdapter',
    # Availability checks
    'check_local_available',
    'check_vllm_available',
    'check_llamacpp_available',
    'check_ollama_available',
    # Model info
    'get_vllm_models',
    'get_llamacpp_models',
    'get_ollama_models',
    # Factory functions
    'create_adapter',
    'list_providers',
    'get_default_model',
    'get_available_models',
    'check_provider_available',
    'get_available_providers',
    'SUPPORTED_PROVIDERS',
]
