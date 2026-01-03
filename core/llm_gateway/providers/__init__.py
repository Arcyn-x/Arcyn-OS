"""
Providers Package for LLM Gateway.

Contains all LLM provider implementations.
Each provider must implement the BaseProvider interface.

Current Providers:
    - GeminiProvider: Google Gemini (primary)

Future Providers (TODO):
    - OpenAIProvider: OpenAI GPT models
    - ClaudeProvider: Anthropic Claude
    - OllamaProvider: Local Ollama models
"""

from .base import (
    BaseProvider,
    ProviderResponse,
    EmbeddingResponse,
    ProviderConfig,
    ProviderStatus,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderAuthError,
)
from .gemini import GeminiProvider

__all__ = [
    'BaseProvider',
    'ProviderResponse',
    'EmbeddingResponse',
    'ProviderConfig',
    'ProviderStatus',
    'ProviderError',
    'ProviderRateLimitError',
    'ProviderTimeoutError',
    'ProviderAuthError',
    'GeminiProvider',
]
