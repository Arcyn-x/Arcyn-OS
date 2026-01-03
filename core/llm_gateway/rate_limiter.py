"""
Rate Limiter for LLM Gateway.

Controls the rate of LLM requests per agent, per task, and system-wide.
Uses a sliding window algorithm for accurate rate limiting.

Design Intent:
    - Prevent runaway costs
    - Fair resource distribution
    - Graceful degradation under load
    - No external dependencies (in-memory)
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from threading import Lock
from datetime import datetime


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    tokens_per_minute: int = 100000
    tokens_per_hour: int = 1000000
    
    # Per-task limits
    requests_per_task: int = 50
    tokens_per_task: int = 50000


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    wait_seconds: float = 0.0
    reason: Optional[str] = None
    remaining_requests: int = 0
    remaining_tokens: int = 0
    reset_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "wait_seconds": self.wait_seconds,
            "reason": self.reason,
            "remaining_requests": self.remaining_requests,
            "remaining_tokens": self.remaining_tokens,
            "reset_time": self.reset_time
        }


class SlidingWindowCounter:
    """
    Sliding window rate counter.
    
    Uses a sub-window approach for accurate rate limiting
    without storing every request timestamp.
    """
    
    def __init__(self, window_seconds: int, max_count: int, sub_windows: int = 10):
        """
        Initialize the counter.
        
        Args:
            window_seconds: Total window size in seconds
            max_count: Maximum allowed count in window
            sub_windows: Number of sub-windows for precision
        """
        self.window_seconds = window_seconds
        self.max_count = max_count
        self.sub_window_seconds = window_seconds / sub_windows
        self.sub_windows = sub_windows
        
        self._counts: Dict[int, int] = defaultdict(int)
        self._lock = Lock()
    
    def _get_current_window(self) -> int:
        """Get current sub-window index."""
        return int(time.time() / self.sub_window_seconds)
    
    def _clean_old_windows(self, current_window: int):
        """Remove expired sub-windows."""
        cutoff = current_window - self.sub_windows
        expired = [w for w in self._counts if w <= cutoff]
        for w in expired:
            del self._counts[w]
    
    def get_count(self) -> int:
        """Get current count in the sliding window."""
        with self._lock:
            current_window = self._get_current_window()
            self._clean_old_windows(current_window)
            
            # Sum counts from all valid sub-windows
            total = 0
            for window_id, count in self._counts.items():
                if window_id > current_window - self.sub_windows:
                    total += count
            
            return total
    
    def increment(self, amount: int = 1) -> bool:
        """
        Increment the counter.
        
        Args:
            amount: Amount to increment
            
        Returns:
            True if increment was allowed
        """
        with self._lock:
            current_window = self._get_current_window()
            self._clean_old_windows(current_window)
            
            current_count = sum(
                count for window_id, count in self._counts.items()
                if window_id > current_window - self.sub_windows
            )
            
            if current_count + amount > self.max_count:
                return False
            
            self._counts[current_window] += amount
            return True
    
    def get_remaining(self) -> int:
        """Get remaining capacity."""
        return max(0, self.max_count - self.get_count())
    
    def get_reset_time(self) -> float:
        """Get time until oldest sub-window expires."""
        current_window = self._get_current_window()
        oldest_window = current_window - self.sub_windows + 1
        reset_time = oldest_window * self.sub_window_seconds + self.window_seconds
        return max(0, reset_time - time.time())


class RateLimiter:
    """
    Rate limiter for LLM Gateway.
    
    Tracks and enforces rate limits per:
        - Agent (requests and tokens)
        - Task (requests and tokens)
        - System-wide (aggregate)
    
    Design Rules:
        - Thread-safe operations
        - Efficient memory usage
        - Accurate sliding window
        - Clear limit messaging
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize the rate limiter.
        
        Args:
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()
        
        # Per-agent counters
        self._agent_requests_per_minute: Dict[str, SlidingWindowCounter] = {}
        self._agent_requests_per_hour: Dict[str, SlidingWindowCounter] = {}
        self._agent_tokens_per_minute: Dict[str, SlidingWindowCounter] = {}
        
        # Per-task counters
        self._task_requests: Dict[str, int] = defaultdict(int)
        self._task_tokens: Dict[str, int] = defaultdict(int)
        
        # System-wide counter (use self.config, not config)
        self._system_requests_per_minute = SlidingWindowCounter(60, self.config.requests_per_minute * 10)
        
        self._lock = Lock()
    
    def _get_agent_counters(self, agent: str) -> Tuple[SlidingWindowCounter, SlidingWindowCounter, SlidingWindowCounter]:
        """Get or create counters for an agent."""
        with self._lock:
            if agent not in self._agent_requests_per_minute:
                self._agent_requests_per_minute[agent] = SlidingWindowCounter(
                    60, self.config.requests_per_minute
                )
            if agent not in self._agent_requests_per_hour:
                self._agent_requests_per_hour[agent] = SlidingWindowCounter(
                    3600, self.config.requests_per_hour
                )
            if agent not in self._agent_tokens_per_minute:
                self._agent_tokens_per_minute[agent] = SlidingWindowCounter(
                    60, self.config.tokens_per_minute
                )
            
            return (
                self._agent_requests_per_minute[agent],
                self._agent_requests_per_hour[agent],
                self._agent_tokens_per_minute[agent]
            )
    
    def check_limit(
        self,
        agent: str,
        task_id: str,
        estimated_tokens: int = 0
    ) -> RateLimitResult:
        """
        Check if a request is within rate limits.
        
        Args:
            agent: Agent name
            task_id: Task identifier
            estimated_tokens: Estimated tokens for this request
            
        Returns:
            RateLimitResult with decision
        """
        req_per_min, req_per_hour, tok_per_min = self._get_agent_counters(agent)
        
        # Check requests per minute
        if req_per_min.get_remaining() <= 0:
            return RateLimitResult(
                allowed=False,
                wait_seconds=req_per_min.get_reset_time(),
                reason=f"Agent '{agent}' rate limit exceeded (requests/minute)",
                remaining_requests=0,
                reset_time=time.time() + req_per_min.get_reset_time()
            )
        
        # Check requests per hour
        if req_per_hour.get_remaining() <= 0:
            return RateLimitResult(
                allowed=False,
                wait_seconds=req_per_hour.get_reset_time(),
                reason=f"Agent '{agent}' rate limit exceeded (requests/hour)",
                remaining_requests=0,
                reset_time=time.time() + req_per_hour.get_reset_time()
            )
        
        # Check tokens per minute
        if estimated_tokens > 0 and tok_per_min.get_remaining() < estimated_tokens:
            return RateLimitResult(
                allowed=False,
                wait_seconds=tok_per_min.get_reset_time(),
                reason=f"Agent '{agent}' token limit exceeded (tokens/minute)",
                remaining_tokens=tok_per_min.get_remaining(),
                reset_time=time.time() + tok_per_min.get_reset_time()
            )
        
        # Check task limits
        if self._task_requests[task_id] >= self.config.requests_per_task:
            return RateLimitResult(
                allowed=False,
                reason=f"Task '{task_id}' has exceeded request limit ({self.config.requests_per_task})",
                remaining_requests=0
            )
        
        if self._task_tokens[task_id] + estimated_tokens > self.config.tokens_per_task:
            return RateLimitResult(
                allowed=False,
                reason=f"Task '{task_id}' would exceed token limit ({self.config.tokens_per_task})",
                remaining_tokens=max(0, self.config.tokens_per_task - self._task_tokens[task_id])
            )
        
        # All checks passed
        return RateLimitResult(
            allowed=True,
            remaining_requests=min(req_per_min.get_remaining(), req_per_hour.get_remaining()),
            remaining_tokens=tok_per_min.get_remaining()
        )
    
    def record_request(
        self,
        agent: str,
        task_id: str,
        tokens_used: int = 0
    ):
        """
        Record a completed request.
        
        Args:
            agent: Agent name
            task_id: Task identifier
            tokens_used: Actual tokens used
        """
        req_per_min, req_per_hour, tok_per_min = self._get_agent_counters(agent)
        
        req_per_min.increment(1)
        req_per_hour.increment(1)
        
        if tokens_used > 0:
            tok_per_min.increment(tokens_used)
        
        with self._lock:
            self._task_requests[task_id] += 1
            self._task_tokens[task_id] += tokens_used
            self._system_requests_per_minute.increment(1)
    
    def get_agent_stats(self, agent: str) -> Dict[str, Any]:
        """Get rate limit stats for an agent."""
        req_per_min, req_per_hour, tok_per_min = self._get_agent_counters(agent)
        
        return {
            "agent": agent,
            "requests_per_minute": {
                "used": req_per_min.get_count(),
                "limit": self.config.requests_per_minute,
                "remaining": req_per_min.get_remaining()
            },
            "requests_per_hour": {
                "used": req_per_hour.get_count(),
                "limit": self.config.requests_per_hour,
                "remaining": req_per_hour.get_remaining()
            },
            "tokens_per_minute": {
                "used": tok_per_min.get_count(),
                "limit": self.config.tokens_per_minute,
                "remaining": tok_per_min.get_remaining()
            }
        }
    
    def get_task_stats(self, task_id: str) -> Dict[str, Any]:
        """Get rate limit stats for a task."""
        return {
            "task_id": task_id,
            "requests": {
                "used": self._task_requests[task_id],
                "limit": self.config.requests_per_task,
                "remaining": max(0, self.config.requests_per_task - self._task_requests[task_id])
            },
            "tokens": {
                "used": self._task_tokens[task_id],
                "limit": self.config.tokens_per_task,
                "remaining": max(0, self.config.tokens_per_task - self._task_tokens[task_id])
            }
        }
    
    def reset_task(self, task_id: str):
        """Reset counters for a task."""
        with self._lock:
            self._task_requests[task_id] = 0
            self._task_tokens[task_id] = 0
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide rate limit stats."""
        return {
            "requests_per_minute": {
                "used": self._system_requests_per_minute.get_count(),
                "limit": self.config.requests_per_minute * 10
            },
            "active_agents": len(self._agent_requests_per_minute),
            "active_tasks": len([t for t, c in self._task_requests.items() if c > 0])
        }
