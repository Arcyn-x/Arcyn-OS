"""
System Monitor module for Evolution Agent (S-3).

Responsible for collecting system snapshots, gathering agent activity logs,
and tracking execution/failure metrics. Uses BATCH SNAPSHOTS only —
no real-time monitoring required.

This module is READ-ONLY. It observes but never modifies.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json
import os


@dataclass
class AgentActivity:
    """Record of agent activity."""
    agent_id: str
    agent_type: str
    action: str
    status: str  # "success", "failure", "pending", "timeout"
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SystemSnapshot:
    """Point-in-time snapshot of system state."""
    snapshot_id: str
    timestamp: str
    agents: Dict[str, Dict[str, Any]]
    metrics: Dict[str, Any]
    recent_activities: List[Dict[str, Any]]
    warnings: List[str]
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class SystemMonitor:
    """
    System monitoring component for Evolution Agent.
    
    Collects batch snapshots of:
    - Agent states and health
    - Execution metrics
    - Failure rates
    - Activity logs
    
    This monitor is PASSIVE — it reads state but never writes to
    production systems.
    
    Example:
        >>> monitor = SystemMonitor()
        >>> monitor.record_activity("architect_agent", "architect", "plan", "success", 150)
        >>> snapshot = monitor.take_snapshot()
        >>> print(snapshot["agents"])
    """
    
    # Known agent types for discovery
    KNOWN_AGENT_TYPES = [
        "architect",
        "builder", 
        "integrator",
        "knowledge_engine",
        "persona",
        "system_designer",
        "evolution"  # Self-reference
    ]
    
    def __init__(
        self,
        agents_path: Optional[str] = None,
        activity_limit: int = 500
    ):
        """
        Initialize the system monitor.
        
        Args:
            agents_path: Path to agents directory (for discovery)
            activity_limit: Maximum activities to keep in memory
        """
        self.agents_path = Path(agents_path) if agents_path else None
        self.activity_limit = activity_limit
        
        self._activities: List[AgentActivity] = []
        self._snapshots: List[SystemSnapshot] = []
        self._agent_registry: Dict[str, Dict[str, Any]] = {}
        self._execution_stats: Dict[str, Dict[str, Any]] = {}
        self._snapshot_counter = 0
    
    def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register an agent for monitoring.
        
        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent (architect, builder, etc.)
            metadata: Optional additional metadata
        """
        self._agent_registry[agent_id] = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "registered_at": datetime.now().isoformat(),
            "last_activity": None,
            "status": "registered",
            "metadata": metadata or {}
        }
        
        # Initialize execution stats
        if agent_id not in self._execution_stats:
            self._execution_stats[agent_id] = {
                "total_executions": 0,
                "successful": 0,
                "failed": 0,
                "total_duration_ms": 0,
                "last_failure": None,
                "last_success": None
            }
    
    def record_activity(
        self,
        agent_id: str,
        agent_type: str,
        action: str,
        status: str,
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentActivity:
        """
        Record an agent activity.
        
        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent
            action: Action performed (e.g., "plan", "build", "analyze")
            status: Result status ("success", "failure", "pending", "timeout")
            duration_ms: Execution duration in milliseconds
            error_message: Error message if failed
            metadata: Additional activity metadata
            
        Returns:
            Recorded AgentActivity
        """
        # Auto-register if not known
        if agent_id not in self._agent_registry:
            self.register_agent(agent_id, agent_type)
        
        activity = AgentActivity(
            agent_id=agent_id,
            agent_type=agent_type,
            action=action,
            status=status,
            duration_ms=duration_ms,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        self._activities.append(activity)
        
        # Trim if over limit
        if len(self._activities) > self.activity_limit:
            self._activities = self._activities[-self.activity_limit:]
        
        # Update agent registry
        self._agent_registry[agent_id]["last_activity"] = activity.timestamp
        self._agent_registry[agent_id]["status"] = "active"
        
        # Update execution stats
        stats = self._execution_stats[agent_id]
        stats["total_executions"] += 1
        
        if status == "success":
            stats["successful"] += 1
            stats["last_success"] = activity.timestamp
        elif status == "failure":
            stats["failed"] += 1
            stats["last_failure"] = activity.timestamp
        
        if duration_ms is not None:
            stats["total_duration_ms"] += duration_ms
        
        return activity
    
    def get_agent_stats(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get execution statistics for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Statistics dictionary or None if not found
        """
        stats = self._execution_stats.get(agent_id)
        if not stats:
            return None
        
        result = stats.copy()
        
        # Calculate derived metrics
        total = result["total_executions"]
        if total > 0:
            result["failure_rate"] = result["failed"] / total
            result["success_rate"] = result["successful"] / total
            result["avg_duration_ms"] = result["total_duration_ms"] / total
        else:
            result["failure_rate"] = 0.0
            result["success_rate"] = 0.0
            result["avg_duration_ms"] = 0.0
        
        return result
    
    def get_all_agent_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all registered agents."""
        return {
            agent_id: self.get_agent_stats(agent_id)
            for agent_id in self._execution_stats
            if self.get_agent_stats(agent_id) is not None
        }
    
    def get_recent_activities(
        self,
        limit: Optional[int] = None,
        agent_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent activities with optional filtering.
        
        Args:
            limit: Maximum number of activities to return
            agent_id: Filter by specific agent
            status_filter: Filter by status
            
        Returns:
            List of activity dictionaries, most recent first
        """
        activities = list(reversed(self._activities))
        
        if agent_id:
            activities = [a for a in activities if a.agent_id == agent_id]
        
        if status_filter:
            activities = [a for a in activities if a.status == status_filter]
        
        if limit:
            activities = activities[:limit]
        
        return [a.to_dict() for a in activities]
    
    def get_failure_summary(
        self,
        hours: float = 24.0
    ) -> Dict[str, Any]:
        """
        Get summary of failures within a time window.
        
        Args:
            hours: Time window in hours
            
        Returns:
            Dictionary with failure summary
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        failures = []
        
        for activity in self._activities:
            if activity.status == "failure":
                try:
                    ts = datetime.fromisoformat(activity.timestamp)
                    if ts >= cutoff:
                        failures.append(activity)
                except (ValueError, TypeError):
                    continue
        
        # Group by agent and action
        by_agent: Dict[str, int] = {}
        by_action: Dict[str, int] = {}
        error_patterns: Dict[str, int] = {}
        
        for f in failures:
            by_agent[f.agent_id] = by_agent.get(f.agent_id, 0) + 1
            by_action[f.action] = by_action.get(f.action, 0) + 1
            if f.error_message:
                # Extract first 50 chars as pattern
                pattern = f.error_message[:50]
                error_patterns[pattern] = error_patterns.get(pattern, 0) + 1
        
        return {
            "total_failures": len(failures),
            "time_window_hours": hours,
            "failures_by_agent": by_agent,
            "failures_by_action": by_action,
            "common_error_patterns": dict(
                sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "failure_rate": len(failures) / max(len(self._activities), 1)
        }
    
    def discover_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover agents from filesystem.
        
        Returns:
            Dictionary of discovered agents
        """
        discovered = {}
        
        if not self.agents_path or not self.agents_path.exists():
            return discovered
        
        for agent_type in self.KNOWN_AGENT_TYPES:
            agent_dir = self.agents_path / agent_type
            if agent_dir.exists() and agent_dir.is_dir():
                # Look for main agent file
                agent_file = agent_dir / f"{agent_type}_agent.py"
                init_file = agent_dir / "__init__.py"
                
                discovered[agent_type] = {
                    "type": agent_type,
                    "path": str(agent_dir),
                    "has_main_file": agent_file.exists(),
                    "has_init": init_file.exists(),
                    "files": [f.name for f in agent_dir.iterdir() if f.is_file()],
                    "subdirs": [d.name for d in agent_dir.iterdir() if d.is_dir()]
                }
        
        return discovered
    
    def take_snapshot(self) -> Dict[str, Any]:
        """
        Take a complete system snapshot.
        
        Returns:
            SystemSnapshot as dictionary
        """
        self._snapshot_counter += 1
        timestamp = datetime.now().isoformat()
        
        # Collect agent states
        agents = {}
        for agent_id, registry_data in self._agent_registry.items():
            stats = self.get_agent_stats(agent_id)
            agents[agent_id] = {
                **registry_data,
                "stats": stats
            }
        
        # Add discovered agents not in registry
        discovered = self.discover_agents()
        for agent_type, info in discovered.items():
            if agent_type not in [a.get("agent_type") for a in agents.values()]:
                agents[f"discovered_{agent_type}"] = {
                    "agent_id": f"discovered_{agent_type}",
                    "agent_type": agent_type,
                    "status": "discovered_not_active",
                    **info
                }
        
        # Calculate aggregate metrics
        all_stats = self.get_all_agent_stats()
        total_executions = sum(s.get("total_executions", 0) for s in all_stats.values())
        total_failures = sum(s.get("failed", 0) for s in all_stats.values())
        
        metrics = {
            "total_registered_agents": len(self._agent_registry),
            "total_discovered_agents": len(discovered),
            "total_executions": total_executions,
            "total_failures": total_failures,
            "overall_failure_rate": total_failures / max(total_executions, 1),
            "active_agents": sum(
                1 for a in self._agent_registry.values() 
                if a.get("status") == "active"
            ),
            "activities_in_memory": len(self._activities)
        }
        
        # Collect warnings and errors
        warnings = []
        errors = []
        
        # Check for agents with high failure rates
        for agent_id, stats in all_stats.items():
            if stats and stats.get("failure_rate", 0) > 0.1:
                warnings.append(f"Agent {agent_id} has high failure rate: {stats['failure_rate']:.1%}")
            if stats and stats.get("failure_rate", 0) > 0.3:
                errors.append(f"Agent {agent_id} has critical failure rate: {stats['failure_rate']:.1%}")
        
        # Check for inactive agents
        now = datetime.now()
        for agent_id, data in self._agent_registry.items():
            last_activity = data.get("last_activity")
            if last_activity:
                try:
                    last_ts = datetime.fromisoformat(last_activity)
                    if (now - last_ts) > timedelta(hours=24):
                        warnings.append(f"Agent {agent_id} inactive for >24 hours")
                except (ValueError, TypeError):
                    pass
        
        snapshot = SystemSnapshot(
            snapshot_id=f"snapshot_{self._snapshot_counter:05d}",
            timestamp=timestamp,
            agents=agents,
            metrics=metrics,
            recent_activities=self.get_recent_activities(limit=50),
            warnings=warnings,
            errors=errors
        )
        
        # Store snapshot (in memory only)
        self._snapshots.append(snapshot)
        if len(self._snapshots) > 100:
            self._snapshots = self._snapshots[-100:]
        
        return snapshot.to_dict()
    
    def get_snapshots(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical snapshots.
        
        Args:
            limit: Maximum number of snapshots to return
            
        Returns:
            List of snapshots, most recent first
        """
        snapshots = list(reversed(self._snapshots))
        if limit:
            snapshots = snapshots[:limit]
        return [s.to_dict() for s in snapshots]
    
    def clear_data(self) -> None:
        """Clear all monitored data (for testing/reset)."""
        self._activities.clear()
        self._snapshots.clear()
        self._agent_registry.clear()
        self._execution_stats.clear()
        self._snapshot_counter = 0
