"""
Health Metrics module for Evolution Agent (S-3).

Defines system health indicators, tracks trends over time, and produces
a system health score. This is INFORMATIONAL, not authoritative.

The health score is a composite metric based on:
- Agent performance metrics
- System stability indicators
- Code quality signals
- Resource utilization trends
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import statistics


class HealthStatus(Enum):
    """Health status levels."""
    CRITICAL = "critical"
    DEGRADED = "degraded"
    HEALTHY = "healthy"
    OPTIMAL = "optimal"
    UNKNOWN = "unknown"


@dataclass
class HealthIndicator:
    """Individual health indicator."""
    name: str
    value: float
    threshold_warning: float
    threshold_critical: float
    unit: str = ""
    description: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def status(self) -> HealthStatus:
        """Determine status based on thresholds."""
        if self.value >= self.threshold_critical:
            return HealthStatus.CRITICAL
        elif self.value >= self.threshold_warning:
            return HealthStatus.DEGRADED
        elif self.value <= self.threshold_warning * 0.5:
            return HealthStatus.OPTIMAL
        else:
            return HealthStatus.HEALTHY
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['status'] = self.status.value
        return result


@dataclass
class HealthTrend:
    """Tracks trend direction and magnitude."""
    indicator_name: str
    direction: str  # "improving", "stable", "degrading"
    magnitude: float  # 0.0 to 1.0
    samples: int
    period_hours: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class HealthMetrics:
    """
    System health metrics tracker.
    
    Tracks health indicators over time and produces composite health scores.
    This module is INFORMATIONAL ONLY — it provides visibility, not control.
    
    Example:
        >>> metrics = HealthMetrics()
        >>> metrics.record_indicator("agent_failure_rate", 0.02, 0.05, 0.10)
        >>> metrics.record_indicator("avg_response_time", 150, 500, 1000)
        >>> score = metrics.get_health_score()
        >>> print(f"System health: {score['overall_status']}")
    """
    
    # Standard health indicators with their thresholds
    STANDARD_INDICATORS = {
        "agent_failure_rate": {
            "threshold_warning": 0.05,
            "threshold_critical": 0.15,
            "unit": "ratio",
            "description": "Proportion of agent tasks that fail"
        },
        "avg_response_time_ms": {
            "threshold_warning": 500,
            "threshold_critical": 2000,
            "unit": "ms",
            "description": "Average task response time"
        },
        "memory_utilization": {
            "threshold_warning": 0.75,
            "threshold_critical": 0.90,
            "unit": "ratio",
            "description": "Memory usage ratio"
        },
        "error_rate": {
            "threshold_warning": 0.03,
            "threshold_critical": 0.10,
            "unit": "ratio",
            "description": "System-wide error rate"
        },
        "task_queue_depth": {
            "threshold_warning": 100,
            "threshold_critical": 500,
            "unit": "count",
            "description": "Pending tasks in queue"
        },
        "context_switch_frequency": {
            "threshold_warning": 50,
            "threshold_critical": 100,
            "unit": "per_minute",
            "description": "Agent context switches per minute"
        },
        "stale_data_ratio": {
            "threshold_warning": 0.10,
            "threshold_critical": 0.30,
            "unit": "ratio",
            "description": "Proportion of stale/outdated cached data"
        },
        "dependency_health": {
            "threshold_warning": 0.85,
            "threshold_critical": 0.70,
            "unit": "score",
            "description": "Health score of external dependencies (inverted: lower is worse)"
        }
    }
    
    def __init__(self, history_limit: int = 1000):
        """
        Initialize health metrics tracker.
        
        Args:
            history_limit: Maximum number of historical records to keep per indicator
        """
        self._current_indicators: Dict[str, HealthIndicator] = {}
        self._history: Dict[str, List[HealthIndicator]] = {}
        self._history_limit = history_limit
        self._trends: Dict[str, HealthTrend] = {}
        self._last_calculation: Optional[str] = None
    
    def record_indicator(
        self,
        name: str,
        value: float,
        threshold_warning: Optional[float] = None,
        threshold_critical: Optional[float] = None,
        unit: str = "",
        description: str = ""
    ) -> HealthIndicator:
        """
        Record a health indicator value.
        
        Args:
            name: Indicator name (use standard names when possible)
            value: Current value
            threshold_warning: Warning threshold (uses standard if available)
            threshold_critical: Critical threshold (uses standard if available)
            unit: Unit of measurement
            description: Human-readable description
            
        Returns:
            The recorded HealthIndicator
        """
        # Use standard thresholds if available and not provided
        if name in self.STANDARD_INDICATORS:
            standard = self.STANDARD_INDICATORS[name]
            threshold_warning = threshold_warning or standard["threshold_warning"]
            threshold_critical = threshold_critical or standard["threshold_critical"]
            unit = unit or standard["unit"]
            description = description or standard["description"]
        else:
            # Default thresholds if not provided
            threshold_warning = threshold_warning if threshold_warning is not None else value * 1.5
            threshold_critical = threshold_critical if threshold_critical is not None else value * 2.0
        
        indicator = HealthIndicator(
            name=name,
            value=value,
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical,
            unit=unit,
            description=description
        )
        
        # Update current
        self._current_indicators[name] = indicator
        
        # Append to history
        if name not in self._history:
            self._history[name] = []
        self._history[name].append(indicator)
        
        # Trim history if needed
        if len(self._history[name]) > self._history_limit:
            self._history[name] = self._history[name][-self._history_limit:]
        
        # Update trend
        self._update_trend(name)
        
        return indicator
    
    def _update_trend(self, name: str) -> None:
        """Update trend calculation for an indicator."""
        history = self._history.get(name, [])
        if len(history) < 3:
            return
        
        # Get recent samples (last 24 hours or all if less)
        now = datetime.now()
        recent = []
        for indicator in reversed(history):
            try:
                ts = datetime.fromisoformat(indicator.timestamp)
                if (now - ts) <= timedelta(hours=24):
                    recent.append(indicator.value)
                else:
                    break
            except (ValueError, TypeError):
                recent.append(indicator.value)
        
        if len(recent) < 3:
            return
        
        # Calculate trend
        recent = list(reversed(recent))  # Chronological order
        first_half = recent[:len(recent)//2]
        second_half = recent[len(recent)//2:]
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        if avg_first == 0:
            change_ratio = 0.0
        else:
            change_ratio = (avg_second - avg_first) / avg_first
        
        # Determine direction
        if abs(change_ratio) < 0.05:
            direction = "stable"
        elif change_ratio > 0:
            # For most metrics, increase is bad (degrading)
            # Exception: dependency_health where higher is better
            if name == "dependency_health":
                direction = "improving"
            else:
                direction = "degrading"
        else:
            if name == "dependency_health":
                direction = "degrading"
            else:
                direction = "improving"
        
        self._trends[name] = HealthTrend(
            indicator_name=name,
            direction=direction,
            magnitude=min(abs(change_ratio), 1.0),
            samples=len(recent),
            period_hours=24.0
        )
    
    def get_indicator(self, name: str) -> Optional[HealthIndicator]:
        """Get current value of an indicator."""
        return self._current_indicators.get(name)
    
    def get_all_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Get all current indicators as dictionaries."""
        return {
            name: indicator.to_dict()
            for name, indicator in self._current_indicators.items()
        }
    
    def get_trend(self, name: str) -> Optional[HealthTrend]:
        """Get trend for an indicator."""
        return self._trends.get(name)
    
    def get_all_trends(self) -> Dict[str, Dict[str, Any]]:
        """Get all trends as dictionaries."""
        return {
            name: trend.to_dict()
            for name, trend in self._trends.items()
        }
    
    def get_health_score(self) -> Dict[str, Any]:
        """
        Calculate and return composite health score.
        
        Returns:
            Dictionary containing:
            {
                "overall_score": float (0.0 to 1.0),
                "overall_status": str,
                "indicator_scores": {...},
                "trend_summary": str,
                "critical_issues": [...],
                "warnings": [...],
                "timestamp": str
            }
        """
        if not self._current_indicators:
            return {
                "overall_score": 1.0,
                "overall_status": HealthStatus.UNKNOWN.value,
                "indicator_scores": {},
                "trend_summary": "No data available",
                "critical_issues": [],
                "warnings": [],
                "timestamp": datetime.now().isoformat()
            }
        
        indicator_scores = {}
        critical_issues = []
        warnings = []
        
        for name, indicator in self._current_indicators.items():
            # Calculate score (1.0 = optimal, 0.0 = critical)
            if indicator.value <= 0:
                score = 1.0
            elif indicator.value >= indicator.threshold_critical:
                score = 0.0
            elif indicator.value >= indicator.threshold_warning:
                # Linear interpolation between warning and critical
                range_size = indicator.threshold_critical - indicator.threshold_warning
                position = indicator.value - indicator.threshold_warning
                score = 0.5 - (0.5 * position / range_size) if range_size > 0 else 0.25
            else:
                # Below warning threshold
                score = 0.5 + (0.5 * (1 - indicator.value / indicator.threshold_warning))
            
            # Special handling for dependency_health (inverted logic)
            if name == "dependency_health":
                score = 1.0 - score if score < 1.0 else 1.0
            
            indicator_scores[name] = {
                "score": round(score, 3),
                "status": indicator.status.value,
                "value": indicator.value,
                "unit": indicator.unit
            }
            
            # Collect issues
            if indicator.status == HealthStatus.CRITICAL:
                critical_issues.append({
                    "indicator": name,
                    "value": indicator.value,
                    "threshold": indicator.threshold_critical,
                    "description": indicator.description
                })
            elif indicator.status == HealthStatus.DEGRADED:
                warnings.append({
                    "indicator": name,
                    "value": indicator.value,
                    "threshold": indicator.threshold_warning,
                    "description": indicator.description
                })
        
        # Calculate overall score (weighted average)
        scores = [s["score"] for s in indicator_scores.values()]
        overall_score = statistics.mean(scores) if scores else 1.0
        
        # Determine overall status
        if critical_issues:
            overall_status = HealthStatus.CRITICAL
        elif warnings:
            overall_status = HealthStatus.DEGRADED
        elif overall_score >= 0.9:
            overall_status = HealthStatus.OPTIMAL
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Summarize trends
        degrading_count = sum(1 for t in self._trends.values() if t.direction == "degrading")
        improving_count = sum(1 for t in self._trends.values() if t.direction == "improving")
        
        if degrading_count > improving_count:
            trend_summary = f"System trending negatively ({degrading_count} degrading indicators)"
        elif improving_count > degrading_count:
            trend_summary = f"System trending positively ({improving_count} improving indicators)"
        else:
            trend_summary = "System is stable"
        
        self._last_calculation = datetime.now().isoformat()
        
        return {
            "overall_score": round(overall_score, 3),
            "overall_status": overall_status.value,
            "indicator_scores": indicator_scores,
            "trend_summary": trend_summary,
            "critical_issues": critical_issues,
            "warnings": warnings,
            "trends": self.get_all_trends(),
            "timestamp": self._last_calculation
        }
    
    def get_history(
        self,
        indicator_name: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical values for an indicator.
        
        Args:
            indicator_name: Name of the indicator
            limit: Maximum number of records to return
            
        Returns:
            List of indicator dictionaries, oldest first
        """
        history = self._history.get(indicator_name, [])
        if limit:
            history = history[-limit:]
        return [indicator.to_dict() for indicator in history]
    
    def clear_history(self, indicator_name: Optional[str] = None) -> None:
        """
        Clear historical data.
        
        Args:
            indicator_name: Specific indicator to clear, or None for all
        """
        if indicator_name:
            self._history.pop(indicator_name, None)
            self._trends.pop(indicator_name, None)
        else:
            self._history.clear()
            self._trends.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all metrics data as dictionary."""
        return {
            "current_indicators": self.get_all_indicators(),
            "trends": self.get_all_trends(),
            "health_score": self.get_health_score(),
            "history_depth": {
                name: len(history)
                for name, history in self._history.items()
            }
        }
