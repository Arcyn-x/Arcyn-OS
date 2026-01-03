"""
Analyzer module for Evolution Agent (S-3).

Identifies recurring failures, bottlenecks, architecture deviations, and technical debt.
Uses RULE-BASED analysis. LLM integration stubbed as TODOs.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum


class IssueSeverity(Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueCategory(Enum):
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    ARCHITECTURE = "architecture"
    MAINTAINABILITY = "maintainability"
    TECHNICAL_DEBT = "technical_debt"


@dataclass
class AnalysisIssue:
    """Identified issue from analysis."""
    issue_id: str
    title: str
    description: str
    category: str
    severity: str
    evidence: List[str]
    affected_components: List[str]
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Analyzer:
    """
    System analyzer for Evolution Agent.
    
    Analyzes observations to identify issues and improvement opportunities.
    Rule-based with hooks for future LLM enhancement.
    """
    
    ARCHITECTURE_STANDARDS = {
        "agent_structure": {
            "required_files": ["__init__.py", "{agent_type}_agent.py", "run.py"],
            "max_file_count": 15
        },
        "performance_thresholds": {
            "max_avg_response_ms": 1000,
            "max_failure_rate": 0.05
        }
    }
    
    FAILURE_PATTERNS = [
        {"name": "cascade_failure", "description": "Multiple agents failing in sequence", "threshold": 3, "window_minutes": 5},
        {"name": "repeated_failure", "description": "Same agent failing repeatedly", "threshold": 5, "window_minutes": 15}
    ]
    
    def __init__(self):
        self._analysis_counter = 0
        self._previous_analyses: List[Dict] = []
    
    def analyze(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive analysis on observations."""
        self._analysis_counter += 1
        timestamp = datetime.now().isoformat()
        analysis_id = f"analysis_{self._analysis_counter:05d}"
        
        issues: List[AnalysisIssue] = []
        issues.extend(self._analyze_failures(observations, analysis_id))
        issues.extend(self._analyze_performance(observations, analysis_id))
        issues.extend(self._analyze_architecture(observations, analysis_id))
        
        patterns = self._detect_patterns(observations)
        bottlenecks = self._identify_bottlenecks(observations)
        technical_debt = self._assess_technical_debt(observations)
        compliance = self._check_standards_compliance(observations)
        summary = self._generate_summary(issues, bottlenecks, technical_debt)
        
        result = {
            "analysis_id": analysis_id,
            "timestamp": timestamp,
            "issues": [i.to_dict() for i in issues],
            "patterns": patterns,
            "bottlenecks": bottlenecks,
            "technical_debt": technical_debt,
            "standards_compliance": compliance,
            "summary": summary
        }
        
        self._previous_analyses.append(result)
        if len(self._previous_analyses) > 50:
            self._previous_analyses = self._previous_analyses[-50:]
        
        return result
    
    def _analyze_failures(self, observations: Dict[str, Any], analysis_id: str) -> List[AnalysisIssue]:
        issues = []
        counter = 0
        agents = observations.get("agents", {})
        
        for agent_id, agent_data in agents.items():
            stats = agent_data.get("stats", {})
            failure_rate = stats.get("failure_rate", 0)
            
            if failure_rate > 0.3:
                counter += 1
                issues.append(AnalysisIssue(
                    issue_id=f"{analysis_id}_fail_{counter}",
                    title=f"Critical failure rate: {agent_id}",
                    description=f"Failure rate {failure_rate:.1%} exceeds critical threshold",
                    category=IssueCategory.RELIABILITY.value,
                    severity=IssueSeverity.CRITICAL.value,
                    evidence=[f"Failure rate: {failure_rate:.1%}", f"Failures: {stats.get('failed', 0)}"],
                    affected_components=[agent_id]
                ))
            elif failure_rate > 0.1:
                counter += 1
                issues.append(AnalysisIssue(
                    issue_id=f"{analysis_id}_fail_{counter}",
                    title=f"High failure rate: {agent_id}",
                    description=f"Failure rate {failure_rate:.1%} exceeds warning threshold",
                    category=IssueCategory.RELIABILITY.value,
                    severity=IssueSeverity.HIGH.value,
                    evidence=[f"Failure rate: {failure_rate:.1%}"],
                    affected_components=[agent_id]
                ))
        return issues
    
    def _analyze_performance(self, observations: Dict[str, Any], analysis_id: str) -> List[AnalysisIssue]:
        issues = []
        counter = 0
        threshold = self.ARCHITECTURE_STANDARDS["performance_thresholds"]["max_avg_response_ms"]
        
        for agent_id, agent_data in observations.get("agents", {}).items():
            stats = agent_data.get("stats", {})
            avg_duration = stats.get("avg_duration_ms", 0)
            
            if avg_duration > threshold * 2:
                counter += 1
                issues.append(AnalysisIssue(
                    issue_id=f"{analysis_id}_perf_{counter}",
                    title=f"Severe latency: {agent_id}",
                    description=f"Avg response {avg_duration:.0f}ms exceeds 2x threshold",
                    category=IssueCategory.PERFORMANCE.value,
                    severity=IssueSeverity.HIGH.value,
                    evidence=[f"Avg: {avg_duration:.0f}ms", f"Threshold: {threshold}ms"],
                    affected_components=[agent_id]
                ))
            elif avg_duration > threshold:
                counter += 1
                issues.append(AnalysisIssue(
                    issue_id=f"{analysis_id}_perf_{counter}",
                    title=f"High latency: {agent_id}",
                    description=f"Avg response {avg_duration:.0f}ms exceeds threshold",
                    category=IssueCategory.PERFORMANCE.value,
                    severity=IssueSeverity.MEDIUM.value,
                    evidence=[f"Avg: {avg_duration:.0f}ms"],
                    affected_components=[agent_id]
                ))
        return issues
    
    def _analyze_architecture(self, observations: Dict[str, Any], analysis_id: str) -> List[AnalysisIssue]:
        issues = []
        counter = 0
        standards = self.ARCHITECTURE_STANDARDS["agent_structure"]
        
        for agent_id, agent_data in observations.get("agents", {}).items():
            agent_type = agent_data.get("agent_type", "unknown")
            files = agent_data.get("files", [])
            
            for req_file in standards["required_files"]:
                expected = req_file.replace("{agent_type}", agent_type)
                if expected not in files:
                    counter += 1
                    issues.append(AnalysisIssue(
                        issue_id=f"{analysis_id}_arch_{counter}",
                        title=f"Missing file: {expected}",
                        description=f"Agent {agent_id} missing required file",
                        category=IssueCategory.ARCHITECTURE.value,
                        severity=IssueSeverity.LOW.value,
                        evidence=[f"Missing: {expected}"],
                        affected_components=[agent_id]
                    ))
        return issues
    
    def _detect_patterns(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        patterns = {}
        activities = observations.get("recent_activities", [])
        now = datetime.now()
        
        for pattern_def in self.FAILURE_PATTERNS:
            cutoff = now - timedelta(minutes=pattern_def["window_minutes"])
            failures = []
            for act in activities:
                if act.get("status") == "failure":
                    try:
                        ts = datetime.fromisoformat(act.get("timestamp", ""))
                        if ts >= cutoff:
                            failures.append(act)
                    except (ValueError, TypeError):
                        continue
            
            patterns[pattern_def["name"]] = {
                "detected": len(failures) >= pattern_def["threshold"],
                "description": pattern_def["description"],
                "count": len(failures),
                "threshold": pattern_def["threshold"],
                "affected_agents": list(set(f.get("agent_id", "") for f in failures))
            }
        return patterns
    
    def _identify_bottlenecks(self, observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        bottlenecks = []
        agents = observations.get("agents", {})
        
        agent_durations = []
        for agent_id, agent_data in agents.items():
            stats = agent_data.get("stats", {})
            avg_dur = stats.get("avg_duration_ms", 0)
            total_exec = stats.get("total_executions", 0)
            if avg_dur > 0 and total_exec > 0:
                agent_durations.append({"agent_id": agent_id, "avg_duration_ms": avg_dur, 
                                        "total_executions": total_exec, "impact": avg_dur * total_exec})
        
        agent_durations.sort(key=lambda x: x["impact"], reverse=True)
        
        for i, ad in enumerate(agent_durations[:3]):
            if ad["avg_duration_ms"] > 200:
                bottlenecks.append({
                    "rank": i + 1, "component": ad["agent_id"], "type": "high_latency",
                    "avg_duration_ms": ad["avg_duration_ms"], "recommendation": f"Optimize {ad['agent_id']}"
                })
        return bottlenecks
    
    def _assess_technical_debt(self, observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        debt = []
        for agent_id, agent_data in observations.get("agents", {}).items():
            files = agent_data.get("files", [])
            if "README.md" not in files:
                debt.append({"type": "missing_docs", "component": agent_id, "effort": "low", "priority": "medium"})
            if not any(f.startswith("test_") or f.endswith("_test.py") for f in files):
                debt.append({"type": "missing_tests", "component": agent_id, "effort": "medium", "priority": "high"})
        return debt
    
    def _check_standards_compliance(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        total, passed = 0, 0
        violations = []
        
        for agent_id, agent_data in observations.get("agents", {}).items():
            stats = agent_data.get("stats", {})
            total += 1
            if stats.get("failure_rate", 0) <= 0.05:
                passed += 1
            else:
                violations.append({"agent": agent_id, "type": "failure_rate"})
        
        return {"score": passed / max(total, 1), "violations": violations, "timestamp": datetime.now().isoformat()}
    
    def _generate_summary(self, issues: List[AnalysisIssue], bottlenecks: List, debt: List) -> Dict[str, Any]:
        severity_counts = {}
        for issue in issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        if severity_counts.get("critical", 0) > 0:
            health = "critical"
        elif severity_counts.get("high", 0) > 2:
            health = "degraded"
        else:
            health = "healthy"
        
        return {
            "total_issues": len(issues), "by_severity": severity_counts,
            "bottlenecks": len(bottlenecks), "debt_items": len(debt), "health": health
        }
    
    # TODO: LLM Hooks (GATED - requires explicit approval)
    def _llm_analyze_patterns(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """TODO: LLM-based pattern detection."""
        return {}
    
    def _llm_suggest_root_causes(self, issues: List) -> List[Dict[str, Any]]:
        """TODO: LLM-based root cause analysis."""
        return []
