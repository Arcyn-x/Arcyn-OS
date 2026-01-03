"""
Base Provider Interface for LLM Gateway.

All LLM providers must implement this interface.
No provider-specific code should leak outside this abstraction.

Design Intent:
    - Provider-agnostic interface
    - Consistent response format
    - Health checking capability
    - Clean error handling
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime


class ProviderStatus(Enum):
    """Provider health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class ProviderResponse:
    """
    Standardized response from any LLM provider.
    
    All providers must return this format, regardless of their native response.
    This ensures agents never need to know which provider was used.
    """
    success: bool
    content: str
    model: str
    provider: str
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    latency_ms: float = 0.0
    finish_reason: str = "completed"
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "tokens": {
                "input": self.tokens_input,
                "output": self.tokens_output,
                "total": self.tokens_total
            },
            "latency_ms": self.latency_ms,
            "finish_reason": self.finish_reason,
            "error": self.error,
            "error_code": self.error_code,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@dataclass
class EmbeddingResponse:
    """Standardized embedding response."""
    success: bool
    embeddings: List[List[float]]
    model: str
    provider: str
    dimensions: int = 0
    latency_ms: float = 0.0
    error: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ProviderConfig:
    """Configuration for provider requests."""
    max_tokens: int = 8192
    temperature: float = 0.7
    top_p: float = 1.0
    top_k: int = 40
    timeout_seconds: int = 60
    system_instruction: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "timeout_seconds": self.timeout_seconds,
            "system_instruction": self.system_instruction
        }


class BaseProvider(ABC):
    """
    Abstract base class for all LLM providers.
    
    Every provider (Gemini, OpenAI, Claude, etc.) must implement this interface.
    The gateway only interacts with providers through this abstraction.
    
    Design Rules:
        - No provider-specific exceptions should propagate
        - All responses must be ProviderResponse objects
        - Health checks must be fast and non-blocking
        - API keys are passed at initialization, never stored in logs
    """
    
    def __init__(self, api_key: str, model: str):
        """
        Initialize the provider.
        
        Args:
            api_key: API key for the provider (never log this)
            model: Model identifier to use
        """
        self._api_key = api_key
        self._model = model
        self._status = ProviderStatus.UNKNOWN
        self._last_health_check: Optional[datetime] = None
    
    @property
    def model(self) -> str:
        """Get the model identifier."""
        return self._model
    
    @property
    def status(self) -> ProviderStatus:
        """Get current provider status."""
        return self._status
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'gemini', 'openai')."""
        pass
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        config: ProviderConfig
    ) -> ProviderResponse:
        """
        Generate a completion.
        
        Args:
            prompt: The prompt text
            config: Generation configuration
            
        Returns:
            ProviderResponse with result or error
        """
        pass
    
    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        config: ProviderConfig,
        schema: Optional[Dict[str, Any]] = None
    ) -> ProviderResponse:
        """
        Generate structured JSON output.
        
        Args:
            prompt: The prompt text
            config: Generation configuration
            schema: Expected JSON schema (optional, for validation hints)
            
        Returns:
            ProviderResponse with JSON content or error
        """
        pass
    
    @abstractmethod
    def generate_embedding(
        self,
        texts: List[str]
    ) -> EmbeddingResponse:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            EmbeddingResponse with vectors or error
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the provider is healthy.
        
        This should be fast and lightweight.
        
        Returns:
            True if provider is operational
        """
        pass
    
    def _set_status(self, status: ProviderStatus):
        """Update provider status."""
        self._status = status
        self._last_health_check = datetime.now()


class ProviderError(Exception):
    """Base exception for provider errors."""
    
    def __init__(self, message: str, code: str = "PROVIDER_ERROR", provider: str = "unknown"):
        super().__init__(message)
        self.code = code
        self.provider = provider


class ProviderRateLimitError(ProviderError):
    """Provider rate limit exceeded."""
    
    def __init__(self, message: str, provider: str, retry_after: Optional[int] = None):
        super().__init__(message, "RATE_LIMIT", provider)
        self.retry_after = retry_after


class ProviderTimeoutError(ProviderError):
    """Provider request timed out."""
    
    def __init__(self, message: str, provider: str):
        super().__init__(message, "TIMEOUT", provider)


class ProviderAuthError(ProviderError):
    """Provider authentication failed."""
    
    def __init__(self, message: str, provider: str):
        super().__init__(message, "AUTH_ERROR", provider)
