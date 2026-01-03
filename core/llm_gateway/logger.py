"""
Gateway Logger for LLM Gateway.

Structured logging for all LLM operations.
Provides observability into gateway behavior.

Design Intent:
    - Structured log format
    - Request/response correlation
    - Performance metrics
    - Error tracking
    - Security (no API keys logged)
"""

import logging
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock


@dataclass
class RequestLog:
    """Log entry for an LLM request."""
    request_id: str
    timestamp: str
    agent: str
    task_id: str
    session_id: str
    provider: str
    model: str
    tokens_input: int
    tokens_output: int
    latency_ms: float
    success: bool
    error: Optional[str] = None
    error_code: Optional[str] = None
    policy_decision: Optional[str] = None
    rate_limit_remaining: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "agent": self.agent,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "provider": self.provider,
            "model": self.model,
            "tokens": {
                "input": self.tokens_input,
                "output": self.tokens_output,
                "total": self.tokens_input + self.tokens_output
            },
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error": self.error,
            "error_code": self.error_code,
            "policy_decision": self.policy_decision,
            "rate_limit_remaining": self.rate_limit_remaining
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class GatewayLogger:
    """
    Structured logger for LLM Gateway.
    
    Provides:
        - Request/response logging
        - Error tracking
        - Performance metrics
        - Audit trail
    
    Design Rules:
        - Never log API keys or secrets
        - Structured format for parsing
        - Configurable output (file, console)
        - Request ID correlation
    """
    
    def __init__(
        self,
        name: str = "LLMGateway",
        log_level: int = logging.INFO,
        log_file: Optional[str] = None,
        log_to_console: bool = True,
        max_recent_logs: int = 1000
    ):
        """
        Initialize the gateway logger.
        
        Args:
            name: Logger name
            log_level: Logging level
            log_file: Optional file path for logging
            log_to_console: Whether to log to console
            max_recent_logs: Maximum recent logs to keep in memory
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # Clear existing handlers
        self.logger.handlers = []
        
        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
        
        # In-memory recent logs for quick access
        self._recent_logs: List[RequestLog] = []
        self._max_recent = max_recent_logs
        self._lock = Lock()
        
        # Request counter for IDs
        self._request_counter = 0
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        self._request_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"req_{timestamp}_{self._request_counter:06d}"
    
    def log_request_start(
        self,
        agent: str,
        task_id: str,
        session_id: str,
        prompt_length: int,
        config: Dict[str, Any]
    ) -> str:
        """
        Log the start of a request.
        
        Args:
            agent: Agent name
            task_id: Task identifier
            session_id: Session identifier
            prompt_length: Length of prompt (not content for security)
            config: Request configuration
            
        Returns:
            Request ID for correlation
        """
        request_id = self._generate_request_id()
        
        self.logger.info(
            f"REQUEST_START | id={request_id} | agent={agent} | task={task_id} | "
            f"prompt_chars={prompt_length} | max_tokens={config.get('max_tokens')} | "
            f"temp={config.get('temperature')}"
        )
        
        return request_id
    
    def log_request_complete(
        self,
        request_id: str,
        agent: str,
        task_id: str,
        session_id: str,
        provider: str,
        model: str,
        tokens_input: int,
        tokens_output: int,
        latency_ms: float,
        success: bool,
        error: Optional[str] = None,
        error_code: Optional[str] = None,
        policy_decision: Optional[str] = None,
        rate_limit_remaining: Optional[int] = None
    ):
        """
        Log completion of a request.
        
        Args:
            request_id: Request ID from log_request_start
            agent: Agent name
            task_id: Task identifier
            session_id: Session identifier
            provider: Provider used
            model: Model used
            tokens_input: Input tokens
            tokens_output: Output tokens
            latency_ms: Total latency
            success: Whether request succeeded
            error: Error message if failed
            error_code: Error code if failed
            policy_decision: Policy decision made
            rate_limit_remaining: Remaining rate limit
        """
        log_entry = RequestLog(
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            agent=agent,
            task_id=task_id,
            session_id=session_id,
            provider=provider,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=latency_ms,
            success=success,
            error=error,
            error_code=error_code,
            policy_decision=policy_decision,
            rate_limit_remaining=rate_limit_remaining
        )
        
        # Store in memory
        with self._lock:
            self._recent_logs.append(log_entry)
            if len(self._recent_logs) > self._max_recent:
                self._recent_logs = self._recent_logs[-self._max_recent:]
        
        # Log based on success
        if success:
            self.logger.info(
                f"REQUEST_COMPLETE | id={request_id} | agent={agent} | "
                f"provider={provider} | model={model} | "
                f"tokens_in={tokens_input} | tokens_out={tokens_output} | "
                f"latency_ms={latency_ms:.1f}"
            )
        else:
            self.logger.error(
                f"REQUEST_FAILED | id={request_id} | agent={agent} | "
                f"provider={provider} | error_code={error_code} | "
                f"error={error}"
            )
    
    def log_policy_violation(
        self,
        agent: str,
        task_id: str,
        violation_type: str,
        message: str,
        severity: str = "error"
    ):
        """Log a policy violation."""
        log_level = logging.ERROR if severity == "error" else logging.WARNING
        self.logger.log(
            log_level,
            f"POLICY_VIOLATION | agent={agent} | task={task_id} | "
            f"type={violation_type} | severity={severity} | message={message}"
        )
    
    def log_rate_limit(
        self,
        agent: str,
        task_id: str,
        reason: str,
        wait_seconds: float
    ):
        """Log a rate limit event."""
        self.logger.warning(
            f"RATE_LIMIT | agent={agent} | task={task_id} | "
            f"reason={reason} | wait_seconds={wait_seconds:.1f}"
        )
    
    def log_provider_health(
        self,
        provider: str,
        status: str,
        details: Optional[str] = None
    ):
        """Log provider health status."""
        self.logger.info(
            f"PROVIDER_HEALTH | provider={provider} | status={status} | "
            f"details={details or 'none'}"
        )
    
    def log_session_start(self, session_id: str, config: Dict[str, Any]):
        """Log session start."""
        self.logger.info(
            f"SESSION_START | session_id={session_id} | "
            f"budget_usd={config.get('budget_usd')} | "
            f"budget_tokens={config.get('budget_tokens')}"
        )
    
    def log_session_end(self, session_id: str, summary: Dict[str, Any]):
        """Log session end with summary."""
        self.logger.info(
            f"SESSION_END | session_id={session_id} | "
            f"total_requests={summary.get('total_requests')} | "
            f"total_tokens={summary.get('total_tokens')} | "
            f"total_cost_usd={summary.get('estimated_cost_usd')}"
        )
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent log entries."""
        with self._lock:
            return [log.to_dict() for log in self._recent_logs[-limit:]]
    
    def get_error_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent error logs."""
        with self._lock:
            errors = [log for log in self._recent_logs if not log.success]
            return [log.to_dict() for log in errors[-limit:]]
    
    def get_agent_logs(self, agent: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs for a specific agent."""
        with self._lock:
            agent_logs = [log for log in self._recent_logs if log.agent == agent]
            return [log.to_dict() for log in agent_logs[-limit:]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        with self._lock:
            if not self._recent_logs:
                return {"total_logs": 0, "success_rate": 0.0}
            
            total = len(self._recent_logs)
            successful = sum(1 for log in self._recent_logs if log.success)
            
            total_latency = sum(log.latency_ms for log in self._recent_logs)
            avg_latency = total_latency / total if total > 0 else 0
            
            return {
                "total_logs": total,
                "successful": successful,
                "failed": total - successful,
                "success_rate": successful / total if total > 0 else 0.0,
                "average_latency_ms": round(avg_latency, 2)
            }
