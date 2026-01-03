"""
Policy Engine for LLM Gateway.

Enforces system-wide constraints on all LLM requests.
This is the gatekeeper - requests must pass policy before execution.

Design Intent:
    - Rule-based enforcement (no ML guessing)
    - Explicit, auditable policies
    - Fail-closed (block on uncertainty)
    - Agent-specific overrides where needed
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum
from datetime import datetime


class PolicyDecision(Enum):
    """Policy enforcement decision."""
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"
    MODIFY = "modify"  # Allow but modify request


class PolicyViolationType(Enum):
    """Types of policy violations."""
    TOKEN_LIMIT_EXCEEDED = "token_limit_exceeded"
    TEMPERATURE_OUT_OF_BOUNDS = "temperature_out_of_bounds"
    PROMPT_TOO_LONG = "prompt_too_long"
    PROMPT_EMPTY = "prompt_empty"
    AGENT_NOT_AUTHORIZED = "agent_not_authorized"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    COST_LIMIT_EXCEEDED = "cost_limit_exceeded"
    MALFORMED_REQUEST = "malformed_request"
    BLOCKED_CONTENT = "blocked_content"


@dataclass
class PolicyViolation:
    """Represents a policy violation."""
    violation_type: PolicyViolationType
    message: str
    severity: str = "error"  # error, warning
    suggested_fix: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.violation_type.value,
            "message": self.message,
            "severity": self.severity,
            "suggested_fix": self.suggested_fix
        }


@dataclass
class PolicyResult:
    """Result of policy evaluation."""
    decision: PolicyDecision
    violations: List[PolicyViolation] = field(default_factory=list)
    modified_config: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    
    @property
    def allowed(self) -> bool:
        return self.decision in (PolicyDecision.ALLOW, PolicyDecision.WARN, PolicyDecision.MODIFY)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "allowed": self.allowed,
            "violations": [v.to_dict() for v in self.violations],
            "modified_config": self.modified_config,
            "warnings": self.warnings
        }


@dataclass
class Policy:
    """
    Policy configuration for the gateway.
    
    These are the system-wide defaults. Agent-specific overrides
    can be configured per-agent.
    """
    # Token limits
    max_tokens_per_request: int = 8192
    max_prompt_length: int = 100000  # characters
    min_prompt_length: int = 1
    
    # Temperature bounds
    min_temperature: float = 0.0
    max_temperature: float = 1.0
    default_temperature: float = 0.7
    
    # Rate limits (per agent)
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    max_requests_per_task: int = 50
    
    # Cost limits (per session)
    max_tokens_per_session: int = 1_000_000
    max_cost_per_session_usd: float = 10.0
    
    # Timeout
    max_timeout_seconds: int = 120
    default_timeout_seconds: int = 60
    
    # Authorized agents
    authorized_agents: Set[str] = field(default_factory=lambda: {
        "Persona", "S-1",
        "Architect", "A-1",
        "Builder", "Forge", "F-1", "F-2", "F-3",
        "Integrator", "I-1",
        "Knowledge", "KnowledgeEngine", "S-2",
        "Evolution", "S-3",
        "SystemDesigner", "D-1",
        "Gateway",  # Internal
        "Test",     # Testing
    })
    
    # Deterministic mode (for reproducibility)
    enforce_deterministic: bool = False
    deterministic_temperature: float = 0.0
    deterministic_top_k: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_tokens_per_request": self.max_tokens_per_request,
            "max_prompt_length": self.max_prompt_length,
            "temperature_bounds": [self.min_temperature, self.max_temperature],
            "rate_limits": {
                "per_minute": self.max_requests_per_minute,
                "per_hour": self.max_requests_per_hour,
                "per_task": self.max_requests_per_task
            },
            "cost_limits": {
                "tokens_per_session": self.max_tokens_per_session,
                "usd_per_session": self.max_cost_per_session_usd
            },
            "authorized_agents": list(self.authorized_agents)
        }


class PolicyEngine:
    """
    Policy enforcement engine for LLM Gateway.
    
    All requests must pass through policy evaluation before execution.
    The engine is strict by default - when in doubt, deny.
    
    Design Rules:
        - No ML or fuzzy matching
        - Explicit, auditable rules
        - Fail-closed on errors
        - Log all violations
    """
    
    def __init__(self, policy: Optional[Policy] = None):
        """
        Initialize the policy engine.
        
        Args:
            policy: Policy configuration (uses defaults if None)
        """
        self.policy = policy or Policy()
        self._agent_overrides: Dict[str, Dict[str, Any]] = {}
    
    def set_agent_override(self, agent: str, overrides: Dict[str, Any]):
        """
        Set agent-specific policy overrides.
        
        Args:
            agent: Agent name
            overrides: Dictionary of policy overrides
        """
        self._agent_overrides[agent] = overrides
    
    def evaluate(
        self,
        agent: str,
        task_id: str,
        prompt: str,
        config: Dict[str, Any],
        session_tokens_used: int = 0,
        task_request_count: int = 0
    ) -> PolicyResult:
        """
        Evaluate a request against all policies.
        
        Args:
            agent: Requesting agent name
            task_id: Task identifier
            prompt: The prompt text
            config: Request configuration
            session_tokens_used: Tokens already used this session
            task_request_count: Requests already made for this task
            
        Returns:
            PolicyResult with decision and any violations
        """
        violations = []
        warnings = []
        modified_config = dict(config)
        
        # Get effective policy (with agent overrides)
        effective_policy = self._get_effective_policy(agent)
        
        # Check agent authorization
        if not self._is_agent_authorized(agent, effective_policy):
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.AGENT_NOT_AUTHORIZED,
                message=f"Agent '{agent}' is not authorized to make LLM requests",
                severity="error"
            ))
            return PolicyResult(decision=PolicyDecision.DENY, violations=violations)
        
        # Check prompt validity
        prompt_violations = self._check_prompt(prompt, effective_policy)
        violations.extend(prompt_violations)
        
        # Check token limits
        token_violations, token_warnings, modified_tokens = self._check_tokens(
            config.get("max_tokens", effective_policy.max_tokens_per_request),
            session_tokens_used,
            effective_policy
        )
        violations.extend(token_violations)
        warnings.extend(token_warnings)
        if modified_tokens is not None:
            modified_config["max_tokens"] = modified_tokens
        
        # Check temperature bounds
        temp_violations, modified_temp = self._check_temperature(
            config.get("temperature", effective_policy.default_temperature),
            effective_policy
        )
        violations.extend(temp_violations)
        if modified_temp is not None:
            modified_config["temperature"] = modified_temp
        
        # Check task request limits
        if task_request_count >= effective_policy.max_requests_per_task:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.RATE_LIMIT_EXCEEDED,
                message=f"Task '{task_id}' has exceeded max requests ({effective_policy.max_requests_per_task})",
                severity="error",
                suggested_fix="Break task into subtasks or increase limit"
            ))
        
        # Check timeout
        timeout = config.get("timeout_seconds", effective_policy.default_timeout_seconds)
        if timeout > effective_policy.max_timeout_seconds:
            warnings.append(f"Timeout {timeout}s exceeds max {effective_policy.max_timeout_seconds}s, capping")
            modified_config["timeout_seconds"] = effective_policy.max_timeout_seconds
        
        # Enforce deterministic mode if enabled
        if effective_policy.enforce_deterministic:
            modified_config["temperature"] = effective_policy.deterministic_temperature
            modified_config["top_k"] = effective_policy.deterministic_top_k
            warnings.append("Deterministic mode enforced")
        
        # Determine final decision
        error_violations = [v for v in violations if v.severity == "error"]
        
        if error_violations:
            return PolicyResult(
                decision=PolicyDecision.DENY,
                violations=violations,
                warnings=warnings
            )
        elif modified_config != config:
            return PolicyResult(
                decision=PolicyDecision.MODIFY,
                violations=violations,
                modified_config=modified_config,
                warnings=warnings
            )
        elif warnings:
            return PolicyResult(
                decision=PolicyDecision.WARN,
                violations=violations,
                warnings=warnings
            )
        else:
            return PolicyResult(decision=PolicyDecision.ALLOW)
    
    def _get_effective_policy(self, agent: str) -> Policy:
        """Get policy with agent-specific overrides applied."""
        if agent not in self._agent_overrides:
            return self.policy
        
        # Clone policy and apply overrides
        # TODO: Implement proper override merging
        return self.policy
    
    def _is_agent_authorized(self, agent: str, policy: Policy) -> bool:
        """Check if agent is authorized."""
        return agent in policy.authorized_agents
    
    def _check_prompt(self, prompt: str, policy: Policy) -> List[PolicyViolation]:
        """Check prompt validity."""
        violations = []
        
        if not prompt or len(prompt.strip()) < policy.min_prompt_length:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.PROMPT_EMPTY,
                message="Prompt is empty or too short",
                severity="error"
            ))
        
        if len(prompt) > policy.max_prompt_length:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.PROMPT_TOO_LONG,
                message=f"Prompt length ({len(prompt)}) exceeds max ({policy.max_prompt_length})",
                severity="error",
                suggested_fix="Reduce prompt length or summarize context"
            ))
        
        return violations
    
    def _check_tokens(
        self,
        requested_tokens: int,
        session_tokens_used: int,
        policy: Policy
    ) -> tuple:
        """Check token limits."""
        violations = []
        warnings = []
        modified = None
        
        # Check per-request limit
        if requested_tokens > policy.max_tokens_per_request:
            warnings.append(f"Requested tokens ({requested_tokens}) exceeds max ({policy.max_tokens_per_request}), capping")
            modified = policy.max_tokens_per_request
        
        # Check session limit
        remaining_session_tokens = policy.max_tokens_per_session - session_tokens_used
        if remaining_session_tokens <= 0:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.COST_LIMIT_EXCEEDED,
                message=f"Session token limit ({policy.max_tokens_per_session}) exceeded",
                severity="error"
            ))
        elif requested_tokens > remaining_session_tokens:
            warnings.append(f"Capping tokens to remaining session budget ({remaining_session_tokens})")
            modified = remaining_session_tokens
        
        return violations, warnings, modified
    
    def _check_temperature(
        self,
        temperature: float,
        policy: Policy
    ) -> tuple:
        """Check temperature bounds."""
        violations = []
        modified = None
        
        if temperature < policy.min_temperature:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.TEMPERATURE_OUT_OF_BOUNDS,
                message=f"Temperature ({temperature}) below minimum ({policy.min_temperature})",
                severity="warning",
                suggested_fix=f"Using minimum temperature {policy.min_temperature}"
            ))
            modified = policy.min_temperature
        elif temperature > policy.max_temperature:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.TEMPERATURE_OUT_OF_BOUNDS,
                message=f"Temperature ({temperature}) above maximum ({policy.max_temperature})",
                severity="warning",
                suggested_fix=f"Using maximum temperature {policy.max_temperature}"
            ))
            modified = policy.max_temperature
        
        return violations, modified
