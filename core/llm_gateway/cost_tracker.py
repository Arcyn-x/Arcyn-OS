"""
Cost Tracker for LLM Gateway.

Tracks token usage and estimates costs for all LLM operations.
Provides session-level and agent-level cost monitoring.

Design Intent:
    - Accurate token counting
    - Cost estimation by provider/model
    - Budget enforcement
    - Trend analysis for Evolution Agent
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from threading import Lock
import json


# Approximate costs per 1M tokens (as of 2026)
# These should be updated based on actual provider pricing
MODEL_COSTS = {
    # Gemini 3 (Preview)
    "gemini-3-pro-preview": {"input": 1.50, "output": 6.00},
    "gemini-3-flash-preview": {"input": 0.10, "output": 0.40},
    
    # Gemini 2.5
    "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-2.5-flash-lite": {"input": 0.0375, "output": 0.15},
    
    # Gemini 2.0
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.0-flash-lite": {"input": 0.05, "output": 0.20},
    
    # Embeddings
    "text-embedding-004": {"input": 0.025, "output": 0.0},
    
    # Default fallback
    "default": {"input": 0.10, "output": 0.40}
}


@dataclass
class UsageRecord:
    """Single usage record."""
    timestamp: datetime
    agent: str
    task_id: str
    model: str
    provider: str
    tokens_input: int
    tokens_output: int
    estimated_cost_usd: float
    latency_ms: float
    success: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "agent": self.agent,
            "task_id": self.task_id,
            "model": self.model,
            "provider": self.provider,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "estimated_cost_usd": self.estimated_cost_usd,
            "latency_ms": self.latency_ms,
            "success": self.success
        }


@dataclass
class CostSummary:
    """Cost summary for a period or scope."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    average_latency_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "tokens": {
                "input": self.total_tokens_input,
                "output": self.total_tokens_output,
                "total": self.total_tokens
            },
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "average_latency_ms": round(self.average_latency_ms, 2)
        }


class CostTracker:
    """
    Cost tracker for LLM Gateway.
    
    Tracks:
        - Per-request token usage
        - Per-agent cumulative costs
        - Per-session budgets
        - Cost trends over time
    
    Design Rules:
        - Thread-safe operations
        - Persistent storage optional (TODO)
        - No external API calls
        - Estimation when exact costs unknown
    """
    
    def __init__(
        self,
        session_id: Optional[str] = None,
        session_budget_usd: float = 10.0,
        session_token_budget: int = 1_000_000
    ):
        """
        Initialize the cost tracker.
        
        Args:
            session_id: Session identifier
            session_budget_usd: Maximum USD budget for session
            session_token_budget: Maximum tokens for session
        """
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_budget_usd = session_budget_usd
        self.session_token_budget = session_token_budget
        self.session_start = datetime.now()
        
        # Usage tracking
        self._records: List[UsageRecord] = []
        self._agent_totals: Dict[str, CostSummary] = defaultdict(CostSummary)
        self._task_totals: Dict[str, CostSummary] = defaultdict(CostSummary)
        self._session_total = CostSummary()
        
        self._lock = Lock()
    
    def estimate_cost(
        self,
        model: str,
        tokens_input: int,
        tokens_output: int
    ) -> float:
        """
        Estimate cost for a request.
        
        Args:
            model: Model identifier
            tokens_input: Input token count
            tokens_output: Output token count
            
        Returns:
            Estimated cost in USD
        """
        costs = MODEL_COSTS.get(model, MODEL_COSTS["default"])
        
        input_cost = (tokens_input / 1_000_000) * costs["input"]
        output_cost = (tokens_output / 1_000_000) * costs["output"]
        
        return input_cost + output_cost
    
    def record_usage(
        self,
        agent: str,
        task_id: str,
        model: str,
        provider: str,
        tokens_input: int,
        tokens_output: int,
        latency_ms: float,
        success: bool
    ):
        """
        Record a usage event.
        
        Args:
            agent: Agent name
            task_id: Task identifier
            model: Model used
            provider: Provider used
            tokens_input: Input tokens
            tokens_output: Output tokens
            latency_ms: Request latency
            success: Whether request succeeded
        """
        estimated_cost = self.estimate_cost(model, tokens_input, tokens_output)
        
        record = UsageRecord(
            timestamp=datetime.now(),
            agent=agent,
            task_id=task_id,
            model=model,
            provider=provider,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            estimated_cost_usd=estimated_cost,
            latency_ms=latency_ms,
            success=success
        )
        
        with self._lock:
            self._records.append(record)
            self._update_totals(record)
    
    def _update_totals(self, record: UsageRecord):
        """Update running totals from a record."""
        # Update agent total
        agent_total = self._agent_totals[record.agent]
        self._add_to_summary(agent_total, record)
        
        # Update task total
        task_total = self._task_totals[record.task_id]
        self._add_to_summary(task_total, record)
        
        # Update session total
        self._add_to_summary(self._session_total, record)
    
    def _add_to_summary(self, summary: CostSummary, record: UsageRecord):
        """Add a record to a summary."""
        summary.total_requests += 1
        if record.success:
            summary.successful_requests += 1
        else:
            summary.failed_requests += 1
        
        summary.total_tokens_input += record.tokens_input
        summary.total_tokens_output += record.tokens_output
        summary.total_tokens += record.tokens_input + record.tokens_output
        summary.estimated_cost_usd += record.estimated_cost_usd
        
        # Update average latency
        if summary.total_requests > 0:
            # Incremental average update
            summary.average_latency_ms += (
                record.latency_ms - summary.average_latency_ms
            ) / summary.total_requests
    
    def check_budget(self) -> Dict[str, Any]:
        """
        Check current budget status.
        
        Returns:
            Dictionary with budget status
        """
        with self._lock:
            remaining_usd = self.session_budget_usd - self._session_total.estimated_cost_usd
            remaining_tokens = self.session_token_budget - self._session_total.total_tokens
            
            return {
                "session_id": self.session_id,
                "budget_usd": {
                    "limit": self.session_budget_usd,
                    "used": round(self._session_total.estimated_cost_usd, 6),
                    "remaining": round(max(0, remaining_usd), 6),
                    "exhausted": remaining_usd <= 0
                },
                "budget_tokens": {
                    "limit": self.session_token_budget,
                    "used": self._session_total.total_tokens,
                    "remaining": max(0, remaining_tokens),
                    "exhausted": remaining_tokens <= 0
                },
                "within_budget": remaining_usd > 0 and remaining_tokens > 0
            }
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary for current session."""
        with self._lock:
            duration = datetime.now() - self.session_start
            
            return {
                "session_id": self.session_id,
                "session_start": self.session_start.isoformat(),
                "duration_seconds": duration.total_seconds(),
                "summary": self._session_total.to_dict(),
                "budget": self.check_budget()
            }
    
    def get_agent_summary(self, agent: str) -> Dict[str, Any]:
        """Get summary for a specific agent."""
        with self._lock:
            if agent not in self._agent_totals:
                return {"agent": agent, "summary": CostSummary().to_dict()}
            
            return {
                "agent": agent,
                "summary": self._agent_totals[agent].to_dict()
            }
    
    def get_task_summary(self, task_id: str) -> Dict[str, Any]:
        """Get summary for a specific task."""
        with self._lock:
            if task_id not in self._task_totals:
                return {"task_id": task_id, "summary": CostSummary().to_dict()}
            
            return {
                "task_id": task_id,
                "summary": self._task_totals[task_id].to_dict()
            }
    
    def get_all_agent_summaries(self) -> Dict[str, Any]:
        """Get summaries for all agents."""
        with self._lock:
            return {
                agent: summary.to_dict()
                for agent, summary in self._agent_totals.items()
            }
    
    def get_recent_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent usage records."""
        with self._lock:
            return [r.to_dict() for r in self._records[-limit:]]
    
    def get_session_tokens_used(self) -> int:
        """Get total tokens used this session."""
        with self._lock:
            return self._session_total.total_tokens
    
    def export_to_json(self) -> str:
        """Export all tracking data to JSON."""
        with self._lock:
            return json.dumps({
                "session": self.get_session_summary(),
                "agents": self.get_all_agent_summaries(),
                "records": [r.to_dict() for r in self._records]
            }, indent=2)
