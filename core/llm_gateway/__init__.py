"""
LLM Gateway Package for Arcyn OS.

This is the SINGLE POINT OF ACCESS for all LLM operations.
No agent may call LLM providers directly - all requests route through here.

Architecture:
    Agent -> Gateway -> Policy -> Rate Limiter -> Provider -> LLM

Design Principles:
    - Centralized control over all LLM access
    - Provider-agnostic interface
    - Strict policy enforcement
    - Cost and rate control
    - Full observability
    - Fail-safe operation

Usage:
    from core.llm_gateway import request
    
    response = request(
        agent="Architect",
        task_id="T5",
        prompt="Design a REST API",
        config={"max_tokens": 800}
    )
"""

from .gateway import LLMGateway, request, request_structured, request_embedding
from .policy import PolicyEngine, Policy
from .rate_limiter import RateLimiter
from .cost_tracker import CostTracker
from .logger import GatewayLogger

__all__ = [
    'LLMGateway',
    'request',
    'request_structured',
    'request_embedding',
    'PolicyEngine',
    'Policy',
    'RateLimiter',
    'CostTracker',
    'GatewayLogger',
]
