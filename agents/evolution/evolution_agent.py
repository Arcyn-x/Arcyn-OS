"""
Evolution Agent (S-3) for Arcyn OS.

The Evolution Agent is the system's senior reviewer. It monitors, analyzes,
and recommends improvements across the entire OS architecture.

CRITICAL CONSTRAINTS:
- ADVISORY-ONLY by default
- Does NOT directly modify production code
- Does NOT override other agents
- Does NOT act autonomously without approval
- Observes → Analyzes → Recommends

This agent behaves like a senior reviewer, not an auto-rewriter.
"""

from typing import Any, Dict, Optional
from pathlib import Path
import sys

# Add project root for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import Logger
from core.context_manager import ContextManager
from core.memory import Memory

from .system_monitor import SystemMonitor
from .analyzer import Analyzer
from .recommender import Recommender
from .health_metrics import HealthMetrics


class EvolutionAgent:
    """
    Main Evolution Agent class (S-3).
    
    The Evolution Agent is responsible for:
    - Monitoring system performance
    - Analyzing agent behavior
    - Detecting inefficiencies and risks
    - Suggesting architectural improvements
    - Proposing refactors and upgrades
    - Tracking system health over time
    
    It is ADVISORY-ONLY. It produces recommendations, not actions.
    
    Example:
        >>> agent = EvolutionAgent()
        >>> snapshot = agent.observe()
        >>> analysis = agent.analyze(snapshot)
        >>> recommendations = agent.recommend(analysis)
        >>> print(recommendations["priority"])
    
    Output Format:
        {
            "risks": [],
            "inefficiencies": [],
            "suggested_changes": [],
            "priority": "low | medium | high",
            "confidence": 0.0
        }
    """
    
    # Agent metadata
    AGENT_ID_PREFIX = "evolution_agent"
    AGENT_TYPE = "evolution"
    AGENT_DESIGNATION = "S-3"
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        log_level: int = 20,
        agents_path: Optional[str] = None,
        storage_path: Optional[str] = None
    ):
        """
        Initialize the Evolution Agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            log_level: Logging level (default: 20 = INFO)
            agents_path: Path to agents directory for discovery
            storage_path: Path for memory storage
        """
        self.agent_id = agent_id or f"{self.AGENT_ID_PREFIX}_{self.AGENT_DESIGNATION}"
        
        # Initialize core integrations
        self.logger = Logger(
            f"EvolutionAgent-{self.agent_id}",
            log_level=log_level,
            log_file=f"./logs/evolution_{self.agent_id}.log"
        )
        self.context = ContextManager(self.agent_id)
        self.memory = Memory(storage_path)
        
        # Determine agents path
        if agents_path:
            self._agents_path = Path(agents_path)
        else:
            self._agents_path = Path(__file__).parent.parent
        
        # Initialize sub-components
        self.monitor = SystemMonitor(
            agents_path=str(self._agents_path),
            activity_limit=500
        )
        self.analyzer = Analyzer()
        self.recommender = Recommender()
        self.health_metrics = HealthMetrics(history_limit=1000)
        
        # State
        self._last_observation: Optional[Dict[str, Any]] = None
        self._last_analysis: Optional[Dict[str, Any]] = None
        self._last_recommendation: Optional[Dict[str, Any]] = None
        
        self.logger.info(f"Evolution Agent {self.agent_id} ({self.AGENT_DESIGNATION}) initialized")
        self.context.set_state('idle')
        self.context.add_history('initialized', {'agent_id': self.agent_id})
    
    def observe(self, snapshot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Observe system state and collect a snapshot.
        
        If no snapshot is provided, takes a fresh snapshot from the system.
        
        Args:
            snapshot: Optional pre-collected snapshot
            
        Returns:
            System snapshot dictionary containing:
            - agents: Agent states and statistics
            - metrics: Aggregate system metrics
            - recent_activities: Recent agent activities
            - warnings: Detected warning conditions
            - errors: Detected error conditions
        """
        self.logger.info("Starting observation phase")
        self.context.set_state('observing')
        self.context.add_history('observe_started')
        
        try:
            if snapshot is not None:
                # Use provided snapshot
                observation = snapshot
                self.logger.debug("Using provided snapshot")
            else:
                # Take fresh snapshot
                observation = self.monitor.take_snapshot()
                self.logger.debug("Took fresh system snapshot")
            
            # Update health metrics from observation
            metrics = observation.get("metrics", {})
            if "overall_failure_rate" in metrics:
                self.health_metrics.record_indicator(
                    "agent_failure_rate",
                    metrics["overall_failure_rate"]
                )
            
            # Store observation
            self._last_observation = observation
            obs_key = f"observation_{self.agent_id}_{observation.get('timestamp', '')}"
            self.memory.write(obs_key, observation)
            
            self.context.add_history('observe_completed', {
                'agents_count': len(observation.get("agents", {})),
                'activities_count': len(observation.get("recent_activities", []))
            })
            self.context.set_state('idle')
            
            self.logger.info(f"Observation complete: {len(observation.get('agents', {}))} agents observed")
            return observation
            
        except Exception as e:
            self.logger.error(f"Observation failed: {str(e)}")
            self.context.set_state('error')
            self.context.add_history('observe_failed', {'error': str(e)})
            raise
    
    def analyze(self, observations: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze observations to identify issues and patterns.
        
        If no observations provided, uses the last observation.
        
        Args:
            observations: System observations to analyze
            
        Returns:
            Analysis result containing:
            - issues: Identified issues with severity
            - patterns: Detected failure/behavior patterns
            - bottlenecks: Performance bottlenecks
            - technical_debt: Technical debt items
            - standards_compliance: Compliance report
            - summary: Analysis summary
        """
        self.logger.info("Starting analysis phase")
        self.context.set_state('analyzing')
        self.context.add_history('analyze_started')
        
        try:
            # Use provided or last observations
            if observations is not None:
                obs_to_analyze = observations
            elif self._last_observation is not None:
                obs_to_analyze = self._last_observation
                self.logger.debug("Using cached observation")
            else:
                raise ValueError("No observations available. Call observe() first.")
            
            # Perform analysis
            analysis = self.analyzer.analyze(obs_to_analyze)
            
            # Update health metrics with analysis results
            summary = analysis.get("summary", {})
            if summary.get("total_issues", 0) > 0:
                # Record issues as a health indicator
                self.health_metrics.record_indicator(
                    "analysis_issue_count",
                    summary["total_issues"],
                    threshold_warning=10,
                    threshold_critical=25,
                    unit="count",
                    description="Number of issues from analysis"
                )
            
            # Store analysis
            self._last_analysis = analysis
            analysis_key = f"analysis_{self.agent_id}_{analysis.get('timestamp', '')}"
            self.memory.write(analysis_key, analysis)
            
            self.context.add_history('analyze_completed', {
                'issues_count': summary.get("total_issues", 0),
                'health': summary.get("health", "unknown")
            })
            self.context.set_state('idle')
            
            self.logger.info(f"Analysis complete: {summary.get('total_issues', 0)} issues, health={summary.get('health', 'unknown')}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            self.context.set_state('error')
            self.context.add_history('analyze_failed', {'error': str(e)})
            raise
    
    def recommend(self, analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate recommendations based on analysis.
        
        If no analysis provided, uses the last analysis.
        
        Args:
            analysis: Analysis results to base recommendations on
            
        Returns:
            Recommendations in the specified format:
            {
                "risks": [],
                "inefficiencies": [],
                "suggested_changes": [],
                "priority": "low | medium | high",
                "confidence": 0.0
            }
        """
        self.logger.info("Starting recommendation phase")
        self.context.set_state('recommending')
        self.context.add_history('recommend_started')
        
        try:
            # Use provided or last analysis
            if analysis is not None:
                analysis_to_use = analysis
            elif self._last_analysis is not None:
                analysis_to_use = self._last_analysis
                self.logger.debug("Using cached analysis")
            else:
                raise ValueError("No analysis available. Call analyze() first.")
            
            # Generate recommendations
            recommendations = self.recommender.recommend(analysis_to_use)
            
            # Store recommendations
            self._last_recommendation = recommendations
            rec_key = f"recommendation_{self.agent_id}_{recommendations.get('timestamp', '')}"
            self.memory.write(rec_key, recommendations)
            
            self.context.add_history('recommend_completed', {
                'recommendations_count': len(recommendations.get("recommendations", [])),
                'priority': recommendations.get("priority", "unknown")
            })
            self.context.set_state('idle')
            
            self.logger.info(
                f"Recommendations complete: {len(recommendations.get('recommendations', []))} recommendations, "
                f"priority={recommendations.get('priority', 'unknown')}"
            )
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Recommendation failed: {str(e)}")
            self.context.set_state('error')
            self.context.add_history('recommend_failed', {'error': str(e)})
            raise
    
    def run_full_cycle(self) -> Dict[str, Any]:
        """
        Run a complete observe → analyze → recommend cycle.
        
        Convenience method that chains all three phases.
        
        Returns:
            Complete result with observation, analysis, and recommendations
        """
        self.logger.info("Starting full evolution cycle")
        
        observation = self.observe()
        analysis = self.analyze(observation)
        recommendations = self.recommend(analysis)
        
        return {
            "observation": observation,
            "analysis": analysis,
            "recommendations": recommendations,
            "health_score": self.health_metrics.get_health_score()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.
        
        Returns:
            Status dictionary with agent state and cached data info
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.AGENT_TYPE,
            "designation": self.AGENT_DESIGNATION,
            "state": self.context.get_state(),
            "has_observation": self._last_observation is not None,
            "has_analysis": self._last_analysis is not None,
            "has_recommendations": self._last_recommendation is not None,
            "health_score": self.health_metrics.get_health_score(),
            "context": self.context.get_context()
        }
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report.
        
        Returns:
            Health metrics and scores
        """
        return self.health_metrics.to_dict()
    
    def record_agent_activity(
        self,
        agent_id: str,
        agent_type: str,
        action: str,
        status: str,
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Record activity from another agent for monitoring.
        
        This allows other agents to report their activities to the
        Evolution Agent for centralized monitoring.
        
        Args:
            agent_id: ID of the reporting agent
            agent_type: Type of agent
            action: Action performed
            status: Result status
            duration_ms: Execution duration
            error_message: Error message if failed
        """
        self.monitor.record_activity(
            agent_id=agent_id,
            agent_type=agent_type,
            action=action,
            status=status,
            duration_ms=duration_ms,
            error_message=error_message
        )
        self.logger.debug(f"Recorded activity: {agent_id}.{action} = {status}")
    
    # ------------------------------------------------------------------
    # Autonomy Hooks (EXPLICITLY GATED)
    # ------------------------------------------------------------------

    def _auto_remediate(
        self,
        recommendation: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a remediation plan from a recommendation.

        GATED: This feature requires `explicit_approval=True` in config.
        Even when enabled, it only produces a remediation plan — it does
        NOT apply changes directly. All patches are queued for human review.

        Args:
            recommendation: A single recommendation dict with at least:
                - type: e.g. "refactor", "fix", "upgrade"
                - description: What needs to change
                - target: File or module path
                - priority: low | medium | high
            config: Optional config overriding defaults. Keys:
                - explicit_approval: bool (must be True)
                - dry_run: bool (default True)
                - max_patches: int (default 5)

        Returns:
            Dictionary containing:
            {
                "approved": bool,
                "plan": List[Dict],   # ordered remediation steps
                "patches_queued": int,
                "status": str,        # "queued" | "rejected" | "disabled"
                "reason": str
            }
        """
        config = config or {}
        result = {
            "approved": False,
            "plan": [],
            "patches_queued": 0,
            "status": "disabled",
            "reason": ""
        }

        # Gate check
        if not config.get("explicit_approval", False):
            result["reason"] = "Auto-remediation requires explicit_approval=True in config"
            self.logger.warning(result["reason"])
            return result

        self.logger.info("Auto-remediation approved — generating plan")
        self.context.set_state('remediating')

        try:
            rec_type = recommendation.get("type", "unknown")
            target = recommendation.get("target", "unknown")
            description = recommendation.get("description", "")
            priority = recommendation.get("priority", "low")

            # Build remediation plan based on recommendation type
            plan_steps = []

            if rec_type == "refactor":
                plan_steps = [
                    {
                        "step": 1,
                        "action": "backup",
                        "description": f"Create backup of {target}",
                        "reversible": True
                    },
                    {
                        "step": 2,
                        "action": "analyze",
                        "description": f"AST-analyze {target} for refactoring opportunities",
                        "reversible": True
                    },
                    {
                        "step": 3,
                        "action": "generate_patch",
                        "description": f"Generate refactoring patch: {description}",
                        "reversible": True
                    },
                    {
                        "step": 4,
                        "action": "validate",
                        "description": "Run syntax validation and tests on patch",
                        "reversible": True
                    },
                    {
                        "step": 5,
                        "action": "queue_for_review",
                        "description": "Submit patch for human review",
                        "reversible": True
                    }
                ]
            elif rec_type == "fix":
                plan_steps = [
                    {
                        "step": 1,
                        "action": "diagnose",
                        "description": f"Identify root cause in {target}",
                        "reversible": True
                    },
                    {
                        "step": 2,
                        "action": "generate_fix",
                        "description": f"Generate fix: {description}",
                        "reversible": True
                    },
                    {
                        "step": 3,
                        "action": "test",
                        "description": "Run regression tests against fix",
                        "reversible": True
                    },
                    {
                        "step": 4,
                        "action": "queue_for_review",
                        "description": "Submit fix for human review",
                        "reversible": True
                    }
                ]
            elif rec_type == "upgrade":
                plan_steps = [
                    {
                        "step": 1,
                        "action": "compatibility_check",
                        "description": f"Check upgrade compatibility for {target}",
                        "reversible": True
                    },
                    {
                        "step": 2,
                        "action": "generate_migration",
                        "description": f"Generate migration plan: {description}",
                        "reversible": True
                    },
                    {
                        "step": 3,
                        "action": "queue_for_review",
                        "description": "Submit migration for human review",
                        "reversible": True
                    }
                ]
            else:
                plan_steps = [
                    {
                        "step": 1,
                        "action": "evaluate",
                        "description": f"Evaluate recommendation: {description}",
                        "reversible": True
                    },
                    {
                        "step": 2,
                        "action": "queue_for_review",
                        "description": "Submit evaluation for human review",
                        "reversible": True
                    }
                ]

            # Enforce max patches
            max_patches = config.get("max_patches", 5)
            plan_steps = plan_steps[:max_patches]

            result["approved"] = True
            result["plan"] = plan_steps
            result["patches_queued"] = len(plan_steps)
            result["status"] = "queued"
            result["reason"] = f"Plan generated for {rec_type} on {target} (priority: {priority})"

            # Store in memory for tracking
            self.memory.write(f"remediation_plan_{target}", {
                "recommendation": recommendation,
                "plan": plan_steps,
                "status": "awaiting_review"
            })

            self.context.add_history('auto_remediate_completed', {
                'target': target,
                'type': rec_type,
                'steps': len(plan_steps)
            })
            self.context.set_state('idle')

            self.logger.info(f"Remediation plan created: {len(plan_steps)} steps for {target}")
            return result

        except Exception as e:
            error_msg = f"Auto-remediation failed: {str(e)}"
            self.logger.error(error_msg)
            result["status"] = "error"
            result["reason"] = error_msg
            self.context.set_state('error')
            return result

    def _continuous_monitoring(
        self,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a single iteration of continuous monitoring.

        GATED: Requires `explicit_approval=True` in config.
        Designed to be called periodically by an external scheduler
        rather than running an internal loop.

        Each iteration:
        1. Takes a system snapshot
        2. Analyzes for issues
        3. Records health metrics
        4. Returns alerts if thresholds are exceeded

        Args:
            config: Optional config overriding defaults. Keys:
                - explicit_approval: bool (must be True)
                - alert_threshold: float (default 0.5)
                - max_consecutive_errors: int (default 3)

        Returns:
            Dictionary containing:
            {
                "monitoring_active": bool,
                "alerts": List[Dict],
                "health_score": float,
                "issues_detected": int,
                "status": str
            }
        """
        config = config or {}
        result = {
            "monitoring_active": False,
            "alerts": [],
            "health_score": 0.0,
            "issues_detected": 0,
            "status": "disabled"
        }

        # Gate check
        if not config.get("explicit_approval", False):
            self.logger.warning("Continuous monitoring requires explicit_approval=True in config")
            result["status"] = "disabled"
            return result

        self.logger.info("Continuous monitoring iteration started")
        self.context.set_state('monitoring')

        alert_threshold = config.get("alert_threshold", 0.5)
        max_errors = config.get("max_consecutive_errors", 3)

        try:
            # 1. Observe
            observation = self.observe()

            # 2. Analyze
            analysis = self.analyze(observation)

            # 3. Health score
            health_score = self.health_metrics.get_health_score()
            result["health_score"] = health_score
            result["monitoring_active"] = True
            result["status"] = "active"

            # 4. Count issues
            summary = analysis.get("summary", {})
            issues_count = summary.get("total_issues", 0)
            result["issues_detected"] = issues_count

            # 5. Generate alerts based on thresholds
            alerts = []

            # Health score alert
            if health_score < alert_threshold:
                alerts.append({
                    "type": "health_degradation",
                    "severity": "high" if health_score < 0.3 else "medium",
                    "message": f"System health score dropped to {health_score:.2f}",
                    "threshold": alert_threshold,
                    "value": health_score
                })

            # Issue count alert
            if issues_count > 10:
                alerts.append({
                    "type": "issue_spike",
                    "severity": "high" if issues_count > 25 else "medium",
                    "message": f"Detected {issues_count} issues in analysis",
                    "threshold": 10,
                    "value": issues_count
                })

            # Error rate alert
            metrics = observation.get("metrics", {})
            error_rate = metrics.get("overall_failure_rate", 0.0)
            if error_rate > 0.1:
                alerts.append({
                    "type": "error_rate",
                    "severity": "critical" if error_rate > 0.3 else "high",
                    "message": f"Agent failure rate at {error_rate:.1%}",
                    "threshold": 0.1,
                    "value": error_rate
                })

            result["alerts"] = alerts

            # Record monitoring health indicator
            self.health_metrics.record_indicator(
                "monitoring_iteration",
                1.0,  # success
                unit="bool",
                description="Monitoring iteration completed"
            )

            self.context.add_history('monitoring_iteration_completed', {
                'health_score': health_score,
                'issues': issues_count,
                'alerts': len(alerts)
            })
            self.context.set_state('idle')

            if alerts:
                self.logger.warning(f"Monitoring: {len(alerts)} alerts raised")
            else:
                self.logger.info("Monitoring iteration complete — no alerts")

            return result

        except Exception as e:
            error_msg = f"Monitoring iteration failed: {str(e)}"
            self.logger.error(error_msg)
            result["status"] = "error"

            # Record failure for circuit breaker tracking
            self.health_metrics.record_indicator(
                "monitoring_iteration",
                0.0,  # failure
                unit="bool",
                description="Monitoring iteration failed"
            )

            self.context.set_state('error')
            return result

