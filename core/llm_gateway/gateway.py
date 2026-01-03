"""
LLM Gateway for Arcyn OS.

THE SINGLE POINT OF ACCESS FOR ALL LLM OPERATIONS.

No agent may call LLM providers directly. All requests route through this gateway.
This is OS infrastructure, not an app helper.

Architecture:
    Agent Request -> Policy Check -> Rate Limit Check -> Provider -> Response

Design Principles:
    - Centralized control
    - Provider agnostic
    - Fail-safe operation
    - Full observability
    - Cost control
    - No exceptions to bypass

Usage:
    from core.llm_gateway import request
    
    response = request(
        agent="Architect",
        task_id="T5",
        prompt="Design a REST API",
        config={"max_tokens": 800}
    )
"""

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from .providers import (
    BaseProvider,
    ProviderResponse,
    EmbeddingResponse,
    ProviderConfig,
    ProviderStatus,
    GeminiProvider,
)
from .policy import PolicyEngine, Policy, PolicyResult, PolicyDecision
from .rate_limiter import RateLimiter, RateLimitConfig
from .cost_tracker import CostTracker
from .logger import GatewayLogger


@dataclass
class GatewayResponse:
    """
    Standardized response from the LLM Gateway.
    
    All gateway responses use this format, regardless of provider.
    Agents receive this - never raw provider responses.
    """
    success: bool
    content: str
    request_id: str
    agent: str
    task_id: str
    model: str
    provider: str
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0
    error: Optional[str] = None
    error_code: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "content": self.content,
            "request_id": self.request_id,
            "agent": self.agent,
            "task_id": self.task_id,
            "model": self.model,
            "provider": self.provider,
            "tokens": {
                "input": self.tokens_input,
                "output": self.tokens_output,
                "total": self.tokens_total
            },
            "latency_ms": self.latency_ms,
            "estimated_cost_usd": self.estimated_cost_usd,
            "error": self.error,
            "error_code": self.error_code,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    @property
    def parsed_json(self) -> Optional[Dict[str, Any]]:
        """Get parsed JSON if this was a structured request."""
        return self.metadata.get("parsed_json")


class LLMGateway:
    """
    Central LLM Gateway for Arcyn OS.
    
    This is the ONLY authorized path to LLM providers.
    All agents must use this gateway - no exceptions.
    
    Responsibilities:
        - API key management (env-only, never exposed)
        - Provider routing
        - Policy enforcement
        - Rate limiting
        - Cost tracking
        - Logging and observability
        - Fail-safe operation
    
    Design Rules:
        - Single instance per session
        - No direct provider access
        - All requests tagged and logged
        - Fail gracefully, never crash
    """
    
    # Singleton instance
    _instance: Optional['LLMGateway'] = None
    _instance_lock = Lock()
    
    def __new__(cls, *args, **kwargs):
        """Ensure singleton pattern."""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        session_id: Optional[str] = None,
        policy: Optional[Policy] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
        log_file: Optional[str] = None,
        log_to_console: bool = False
    ):
        """
        Initialize the LLM Gateway.
        
        Args:
            api_key: API key (uses GEMINI_API_KEY env var if not provided)
            model: Default model to use
            session_id: Session identifier (auto-generated if None)
            policy: Policy configuration
            rate_limit_config: Rate limit configuration
            log_file: Optional log file path
            log_to_console: Whether to log to console
        """
        # Only initialize once
        if self._initialized:
            return
        
        # Get API key from environment
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set environment variable or pass api_key."
            )
        
        self._default_model = model
        self._session_id = session_id or datetime.now().strftime("session_%Y%m%d_%H%M%S")
        
        # Initialize components
        self._policy_engine = PolicyEngine(policy)
        self._rate_limiter = RateLimiter(rate_limit_config)
        self._cost_tracker = CostTracker(
            session_id=self._session_id,
            session_budget_usd=policy.max_cost_per_session_usd if policy else 10.0,
            session_token_budget=policy.max_tokens_per_session if policy else 1_000_000
        )
        self._logger = GatewayLogger(
            log_file=log_file,
            log_to_console=log_to_console
        )
        
        # Initialize provider
        self._provider: Optional[BaseProvider] = None
        self._init_provider()
        
        # Task request counters (for per-task limits)
        self._task_request_counts: Dict[str, int] = {}
        self._lock = Lock()
        
        self._initialized = True
        
        # Log session start
        self._logger.log_session_start(self._session_id, {
            "budget_usd": self._cost_tracker.session_budget_usd,
            "budget_tokens": self._cost_tracker.session_token_budget
        })
    
    def _init_provider(self):
        """Initialize the LLM provider."""
        try:
            self._provider = GeminiProvider(
                api_key=self._api_key,
                model=self._default_model
            )
            self._logger.log_provider_health("gemini", "initialized")
        except Exception as e:
            self._logger.log_provider_health("gemini", "failed", str(e))
            raise
    
    def request(
        self,
        agent: str,
        task_id: str,
        prompt: str,
        config: Optional[Dict[str, Any]] = None
    ) -> GatewayResponse:
        """
        Make an LLM request through the gateway.
        
        This is the PRIMARY interface for all agents.
        
        Args:
            agent: Agent name (e.g., "Architect", "Builder")
            task_id: Task identifier
            prompt: The prompt text
            config: Optional configuration:
                - max_tokens: Maximum output tokens
                - temperature: Sampling temperature
                - system: System instruction
                
        Returns:
            GatewayResponse with result or error
        """
        config = config or {}
        
        # Generate request ID
        request_id = self._logger.log_request_start(
            agent=agent,
            task_id=task_id,
            session_id=self._session_id,
            prompt_length=len(prompt),
            config=config
        )
        
        try:
            return self._execute_request(
                request_id=request_id,
                agent=agent,
                task_id=task_id,
                prompt=prompt,
                config=config,
                structured=False
            )
        except Exception as e:
            # Catch-all: gateway should NEVER crash
            return self._create_error_response(
                request_id=request_id,
                agent=agent,
                task_id=task_id,
                error=str(e),
                error_code="GATEWAY_ERROR"
            )
    
    def request_structured(
        self,
        agent: str,
        task_id: str,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> GatewayResponse:
        """
        Make a structured (JSON) LLM request.
        
        Args:
            agent: Agent name
            task_id: Task identifier
            prompt: The prompt text
            schema: Expected JSON schema
            config: Optional configuration
            
        Returns:
            GatewayResponse with JSON content
        """
        config = config or {}
        config["_schema"] = schema
        
        request_id = self._logger.log_request_start(
            agent=agent,
            task_id=task_id,
            session_id=self._session_id,
            prompt_length=len(prompt),
            config=config
        )
        
        try:
            return self._execute_request(
                request_id=request_id,
                agent=agent,
                task_id=task_id,
                prompt=prompt,
                config=config,
                structured=True
            )
        except Exception as e:
            return self._create_error_response(
                request_id=request_id,
                agent=agent,
                task_id=task_id,
                error=str(e),
                error_code="GATEWAY_ERROR"
            )
    
    def request_embedding(
        self,
        agent: str,
        task_id: str,
        texts: Union[str, List[str]]
    ) -> GatewayResponse:
        """
        Generate embeddings through the gateway.
        
        Args:
            agent: Agent name
            task_id: Task identifier
            texts: Text or list of texts to embed
            
        Returns:
            GatewayResponse with embeddings in metadata
        """
        if isinstance(texts, str):
            texts = [texts]
        
        request_id = self._logger.log_request_start(
            agent=agent,
            task_id=task_id,
            session_id=self._session_id,
            prompt_length=sum(len(t) for t in texts),
            config={"type": "embedding", "count": len(texts)}
        )
        
        try:
            # Policy check (minimal for embeddings)
            policy_result = self._policy_engine.evaluate(
                agent=agent,
                task_id=task_id,
                prompt=texts[0],  # Just check first for authorization
                config={},
                session_tokens_used=self._cost_tracker.get_session_tokens_used(),
                task_request_count=self._get_task_request_count(task_id)
            )
            
            if not policy_result.allowed:
                return self._create_error_response(
                    request_id=request_id,
                    agent=agent,
                    task_id=task_id,
                    error=policy_result.violations[0].message if policy_result.violations else "Policy denied",
                    error_code="POLICY_DENIED"
                )
            
            # Rate limit check
            rate_result = self._rate_limiter.check_limit(agent, task_id)
            if not rate_result.allowed:
                self._logger.log_rate_limit(agent, task_id, rate_result.reason or "", rate_result.wait_seconds)
                return self._create_error_response(
                    request_id=request_id,
                    agent=agent,
                    task_id=task_id,
                    error=rate_result.reason or "Rate limit exceeded",
                    error_code="RATE_LIMIT"
                )
            
            # Execute embedding request
            response = self._provider.generate_embedding(texts)
            
            # Record usage
            self._rate_limiter.record_request(agent, task_id, 0)
            self._increment_task_request_count(task_id)
            
            # Log completion
            self._logger.log_request_complete(
                request_id=request_id,
                agent=agent,
                task_id=task_id,
                session_id=self._session_id,
                provider=response.provider,
                model=response.model,
                tokens_input=0,
                tokens_output=0,
                latency_ms=response.latency_ms,
                success=response.success,
                error=response.error,
                error_code=response.error_code
            )
            
            if response.success:
                return GatewayResponse(
                    success=True,
                    content="",
                    request_id=request_id,
                    agent=agent,
                    task_id=task_id,
                    model=response.model,
                    provider=response.provider,
                    latency_ms=response.latency_ms,
                    metadata={
                        "embeddings": response.embeddings,
                        "dimensions": response.dimensions
                    }
                )
            else:
                return self._create_error_response(
                    request_id=request_id,
                    agent=agent,
                    task_id=task_id,
                    error=response.error or "Embedding failed",
                    error_code=response.error_code or "EMBEDDING_ERROR"
                )
                
        except Exception as e:
            return self._create_error_response(
                request_id=request_id,
                agent=agent,
                task_id=task_id,
                error=str(e),
                error_code="GATEWAY_ERROR"
            )
    
    def _execute_request(
        self,
        request_id: str,
        agent: str,
        task_id: str,
        prompt: str,
        config: Dict[str, Any],
        structured: bool
    ) -> GatewayResponse:
        """Execute a request through the full pipeline."""
        
        warnings = []
        
        # 1. Policy check
        policy_result = self._policy_engine.evaluate(
            agent=agent,
            task_id=task_id,
            prompt=prompt,
            config=config,
            session_tokens_used=self._cost_tracker.get_session_tokens_used(),
            task_request_count=self._get_task_request_count(task_id)
        )
        
        if not policy_result.allowed:
            # Log violation
            if policy_result.violations:
                for v in policy_result.violations:
                    self._logger.log_policy_violation(
                        agent, task_id, v.violation_type.value, v.message, v.severity
                    )
            
            return self._create_error_response(
                request_id=request_id,
                agent=agent,
                task_id=task_id,
                error=policy_result.violations[0].message if policy_result.violations else "Policy denied",
                error_code="POLICY_DENIED"
            )
        
        # Apply any policy modifications
        if policy_result.modified_config:
            config.update(policy_result.modified_config)
        
        warnings.extend(policy_result.warnings)
        
        # 2. Rate limit check
        rate_result = self._rate_limiter.check_limit(
            agent, task_id, config.get("max_tokens", 8192)
        )
        
        if not rate_result.allowed:
            self._logger.log_rate_limit(
                agent, task_id, rate_result.reason or "", rate_result.wait_seconds
            )
            return self._create_error_response(
                request_id=request_id,
                agent=agent,
                task_id=task_id,
                error=rate_result.reason or "Rate limit exceeded",
                error_code="RATE_LIMIT"
            )
        
        # 3. Budget check
        budget_status = self._cost_tracker.check_budget()
        if not budget_status["within_budget"]:
            return self._create_error_response(
                request_id=request_id,
                agent=agent,
                task_id=task_id,
                error="Session budget exhausted",
                error_code="BUDGET_EXHAUSTED"
            )
        
        # 4. Build provider config
        provider_config = ProviderConfig(
            max_tokens=config.get("max_tokens", 8192),
            temperature=config.get("temperature", 0.7),
            top_p=config.get("top_p", 1.0),
            top_k=config.get("top_k", 40),
            timeout_seconds=config.get("timeout_seconds", 60),
            system_instruction=config.get("system")
        )
        
        # 5. Execute request
        if structured:
            schema = config.get("_schema")
            response = self._provider.generate_structured(prompt, provider_config, schema)
        else:
            response = self._provider.generate(prompt, provider_config)
        
        # 6. Record usage
        self._rate_limiter.record_request(agent, task_id, response.tokens_total)
        self._increment_task_request_count(task_id)
        
        self._cost_tracker.record_usage(
            agent=agent,
            task_id=task_id,
            model=response.model,
            provider=response.provider,
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            latency_ms=response.latency_ms,
            success=response.success
        )
        
        # 7. Log completion
        self._logger.log_request_complete(
            request_id=request_id,
            agent=agent,
            task_id=task_id,
            session_id=self._session_id,
            provider=response.provider,
            model=response.model,
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            latency_ms=response.latency_ms,
            success=response.success,
            error=response.error,
            error_code=response.error_code,
            policy_decision=policy_result.decision.value,
            rate_limit_remaining=rate_result.remaining_requests
        )
        
        # 8. Build response
        if response.success:
            estimated_cost = self._cost_tracker.estimate_cost(
                response.model, response.tokens_input, response.tokens_output
            )
            
            return GatewayResponse(
                success=True,
                content=response.content,
                request_id=request_id,
                agent=agent,
                task_id=task_id,
                model=response.model,
                provider=response.provider,
                tokens_input=response.tokens_input,
                tokens_output=response.tokens_output,
                tokens_total=response.tokens_total,
                latency_ms=response.latency_ms,
                estimated_cost_usd=estimated_cost,
                warnings=warnings,
                metadata=response.metadata
            )
        else:
            return self._create_error_response(
                request_id=request_id,
                agent=agent,
                task_id=task_id,
                error=response.error or "Request failed",
                error_code=response.error_code or "PROVIDER_ERROR"
            )
    
    def _create_error_response(
        self,
        request_id: str,
        agent: str,
        task_id: str,
        error: str,
        error_code: str
    ) -> GatewayResponse:
        """Create a standardized error response."""
        return GatewayResponse(
            success=False,
            content="",
            request_id=request_id,
            agent=agent,
            task_id=task_id,
            model=self._default_model,
            provider=self._provider.name if self._provider else "unknown",
            error=error,
            error_code=error_code
        )
    
    def _get_task_request_count(self, task_id: str) -> int:
        """Get request count for a task."""
        with self._lock:
            return self._task_request_counts.get(task_id, 0)
    
    def _increment_task_request_count(self, task_id: str):
        """Increment request count for a task."""
        with self._lock:
            self._task_request_counts[task_id] = self._task_request_counts.get(task_id, 0) + 1
    
    # =========================================================================
    # Observability Methods
    # =========================================================================
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        return {
            "session_id": self._session_id,
            "cost": self._cost_tracker.get_session_summary(),
            "rate_limits": self._rate_limiter.get_system_stats(),
            "logging": self._logger.get_stats()
        }
    
    def get_agent_stats(self, agent: str) -> Dict[str, Any]:
        """Get statistics for an agent."""
        return {
            "agent": agent,
            "cost": self._cost_tracker.get_agent_summary(agent),
            "rate_limits": self._rate_limiter.get_agent_stats(agent),
            "logs": self._logger.get_agent_logs(agent, limit=10)
        }
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent gateway logs."""
        return self._logger.get_recent_logs(limit)
    
    def get_error_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent error logs."""
        return self._logger.get_error_logs(limit)
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status."""
        return self._cost_tracker.check_budget()
    
    def provider_health_check(self) -> Dict[str, Any]:
        """Check provider health."""
        if self._provider is None:
            return {"provider": "none", "healthy": False}
        
        healthy = self._provider.health_check()
        status = self._provider.status.value
        
        self._logger.log_provider_health(self._provider.name, status)
        
        return {
            "provider": self._provider.name,
            "model": self._provider.model,
            "status": status,
            "healthy": healthy
        }


# =============================================================================
# Module-Level Convenience Functions
# =============================================================================

_gateway: Optional[LLMGateway] = None


def _get_gateway() -> LLMGateway:
    """Get or create the gateway instance."""
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway()
    return _gateway


def request(
    agent: str,
    task_id: str,
    prompt: str,
    config: Optional[Dict[str, Any]] = None
) -> GatewayResponse:
    """
    Make an LLM request through the gateway.
    
    This is THE interface for all agents.
    
    Args:
        agent: Agent name (e.g., "Architect", "Builder")
        task_id: Task identifier
        prompt: The prompt text
        config: Optional configuration
        
    Returns:
        GatewayResponse with result or error
        
    Example:
        from core.llm_gateway import request
        
        response = request(
            agent="Architect",
            task_id="T5",
            prompt="Design a REST API",
            config={"max_tokens": 800}
        )
        
        if response.success:
            print(response.content)
        else:
            print(f"Error: {response.error}")
    """
    return _get_gateway().request(agent, task_id, prompt, config)


def request_structured(
    agent: str,
    task_id: str,
    prompt: str,
    schema: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> GatewayResponse:
    """
    Make a structured (JSON) LLM request.
    
    Args:
        agent: Agent name
        task_id: Task identifier
        prompt: The prompt text
        schema: Expected JSON schema
        config: Optional configuration
        
    Returns:
        GatewayResponse with JSON content
        
    Example:
        response = request_structured(
            agent="Architect",
            task_id="T5",
            prompt="Create a development plan",
            schema={"milestones": [], "tasks": []}
        )
        
        if response.success:
            plan = response.parsed_json
    """
    return _get_gateway().request_structured(agent, task_id, prompt, schema, config)


def request_embedding(
    agent: str,
    task_id: str,
    texts: Union[str, List[str]]
) -> GatewayResponse:
    """
    Generate embeddings through the gateway.
    
    Args:
        agent: Agent name
        task_id: Task identifier
        texts: Text or list of texts to embed
        
    Returns:
        GatewayResponse with embeddings in metadata
        
    Example:
        response = request_embedding(
            agent="Knowledge",
            task_id="K1",
            texts=["Hello world", "Foo bar"]
        )
        
        if response.success:
            embeddings = response.metadata["embeddings"]
    """
    return _get_gateway().request_embedding(agent, task_id, texts)
