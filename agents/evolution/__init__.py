"""
Evolution Agent (S-3) for Arcyn OS.

The Evolution Agent is the system's senior reviewer — it observes, analyzes,
and recommends improvements across the entire OS architecture.

IMPORTANT: This agent is ADVISORY-ONLY by default.
It does NOT:
- Directly modify production code
- Override other agents
- Act autonomously without approval

It observes → analyzes → recommends.

Components:
    - EvolutionAgent: Main agent class with observe/analyze/recommend pipeline
    - SystemMonitor: Collects system snapshots and agent activity logs
    - Analyzer: Identifies failures, bottlenecks, and technical debt
    - Recommender: Proposes improvements with scope, risk, and effort estimates
    - HealthMetrics: Tracks system health indicators and trends

Usage:
    >>> from agents.evolution import EvolutionAgent
    >>> agent = EvolutionAgent()
    >>> snapshot = agent.observe()
    >>> analysis = agent.analyze(snapshot)
    >>> recommendations = agent.recommend(analysis)
"""

from .evolution_agent import EvolutionAgent
from .system_monitor import SystemMonitor
from .analyzer import Analyzer
from .recommender import Recommender
from .health_metrics import HealthMetrics

__all__ = [
    'EvolutionAgent',
    'SystemMonitor',
    'Analyzer',
    'Recommender',
    'HealthMetrics'
]

__version__ = "0.1.0"
__agent_id__ = "S-3"
__agent_type__ = "advisory"
