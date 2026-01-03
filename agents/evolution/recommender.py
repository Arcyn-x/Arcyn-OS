"""
Recommender module for Evolution Agent (S-3).

Proposes improvements, refactors, deprecations, and new modules.
All recommendations include: scope, risk, estimated effort, dependencies.

This module is ADVISORY-ONLY. It never directly modifies code.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum


class RecommendationType(Enum):
    REFACTOR = "refactor"
    OPTIMIZATION = "optimization"
    DEPRECATION = "deprecation"
    NEW_MODULE = "new_module"
    NEW_AGENT = "new_agent"
    CONFIGURATION = "configuration"
    ARCHITECTURE = "architecture"
    SECURITY = "security"


class RiskLevel(Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EffortEstimate(Enum):
    TRIVIAL = "trivial"      # < 1 hour
    LOW = "low"              # 1-4 hours
    MEDIUM = "medium"        # 1-2 days
    HIGH = "high"            # 3-5 days
    SIGNIFICANT = "significant"  # > 1 week


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Recommendation:
    """A single improvement recommendation."""
    rec_id: str
    title: str
    description: str
    recommendation_type: str
    scope: str
    risk: str
    effort: str
    priority: str
    confidence: float
    rationale: str
    affected_components: List[str]
    dependencies: List[str]
    prerequisites: List[str]
    expected_benefits: List[str]
    implementation_hints: List[str]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Recommender:
    """
    Recommendation engine for Evolution Agent.
    
    Takes analysis results and produces actionable recommendations
    with proper scoping, risk assessment, and effort estimates.
    
    Example:
        >>> recommender = Recommender()
        >>> analysis = {"issues": [...], "bottlenecks": [...]}
        >>> recs = recommender.recommend(analysis)
        >>> print(recs["recommendations"])
    """
    
    # Templates for common recommendations
    RECOMMENDATION_TEMPLATES = {
        "high_failure_rate": {
            "type": RecommendationType.REFACTOR,
            "title_template": "Improve reliability of {component}",
            "risk": RiskLevel.MEDIUM,
            "effort": EffortEstimate.MEDIUM,
            "hints": [
                "Add comprehensive error handling",
                "Implement retry logic with exponential backoff",
                "Add circuit breaker pattern",
                "Improve input validation"
            ]
        },
        "high_latency": {
            "type": RecommendationType.OPTIMIZATION,
            "title_template": "Optimize performance of {component}",
            "risk": RiskLevel.LOW,
            "effort": EffortEstimate.MEDIUM,
            "hints": [
                "Profile execution to find bottlenecks",
                "Consider caching frequently accessed data",
                "Optimize database queries if applicable",
                "Consider async processing for heavy tasks"
            ]
        },
        "missing_tests": {
            "type": RecommendationType.REFACTOR,
            "title_template": "Add test coverage for {component}",
            "risk": RiskLevel.MINIMAL,
            "effort": EffortEstimate.MEDIUM,
            "hints": [
                "Start with unit tests for core functions",
                "Add integration tests for agent interactions",
                "Set up CI to run tests automatically"
            ]
        },
        "missing_docs": {
            "type": RecommendationType.REFACTOR,
            "title_template": "Document {component}",
            "risk": RiskLevel.MINIMAL,
            "effort": EffortEstimate.LOW,
            "hints": [
                "Add README.md with usage examples",
                "Document public API with docstrings",
                "Add architecture decision records if needed"
            ]
        },
        "cascade_failure": {
            "type": RecommendationType.ARCHITECTURE,
            "title_template": "Implement failure isolation",
            "risk": RiskLevel.MEDIUM,
            "effort": EffortEstimate.HIGH,
            "hints": [
                "Add bulkhead pattern between agents",
                "Implement graceful degradation",
                "Add health checks and circuit breakers"
            ]
        }
    }
    
    def __init__(self):
        self._rec_counter = 0
        self._previous_recommendations: List[Dict] = []
    
    def recommend(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate recommendations from analysis results.
        
        Args:
            analysis: Analysis result from Analyzer
                Expected keys: issues, bottlenecks, technical_debt, patterns
                
        Returns:
            Dictionary containing:
            {
                "recommendations": [...],
                "risks": [...],
                "inefficiencies": [...],
                "suggested_changes": [...],
                "priority": "low|medium|high",
                "confidence": float,
                "summary": {...}
            }
        """
        timestamp = datetime.now().isoformat()
        recommendations: List[Recommendation] = []
        
        # Generate recommendations from issues
        for issue in analysis.get("issues", []):
            rec = self._recommendation_from_issue(issue)
            if rec:
                recommendations.append(rec)
        
        # Generate recommendations from bottlenecks
        for bottleneck in analysis.get("bottlenecks", []):
            rec = self._recommendation_from_bottleneck(bottleneck)
            if rec:
                recommendations.append(rec)
        
        # Generate recommendations from technical debt
        for debt_item in analysis.get("technical_debt", []):
            rec = self._recommendation_from_debt(debt_item)
            if rec:
                recommendations.append(rec)
        
        # Generate recommendations from patterns
        for pattern_name, pattern_data in analysis.get("patterns", {}).items():
            if pattern_data.get("detected"):
                rec = self._recommendation_from_pattern(pattern_name, pattern_data)
                if rec:
                    recommendations.append(rec)
        
        # Deduplicate and prioritize
        recommendations = self._deduplicate_recommendations(recommendations)
        recommendations = self._prioritize_recommendations(recommendations)
        
        # Build output in specified format
        risks = [r.to_dict() for r in recommendations 
                 if r.risk in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]]
        
        inefficiencies = [r.to_dict() for r in recommendations 
                         if r.recommendation_type == RecommendationType.OPTIMIZATION.value]
        
        suggested_changes = [r.to_dict() for r in recommendations]
        
        # Calculate overall priority and confidence
        if any(r.priority == Priority.HIGH.value for r in recommendations):
            overall_priority = Priority.HIGH.value
        elif any(r.priority == Priority.MEDIUM.value for r in recommendations):
            overall_priority = Priority.MEDIUM.value
        else:
            overall_priority = Priority.LOW.value
        
        confidences = [r.confidence for r in recommendations]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        result = {
            "recommendations": [r.to_dict() for r in recommendations],
            "risks": risks,
            "inefficiencies": inefficiencies,
            "suggested_changes": suggested_changes,
            "priority": overall_priority,
            "confidence": round(overall_confidence, 2),
            "summary": {
                "total_recommendations": len(recommendations),
                "by_type": self._count_by_type(recommendations),
                "by_priority": self._count_by_priority(recommendations),
                "high_risk_count": len(risks),
                "quick_wins": len([r for r in recommendations 
                                  if r.effort in [EffortEstimate.TRIVIAL.value, EffortEstimate.LOW.value]
                                  and r.risk in [RiskLevel.MINIMAL.value, RiskLevel.LOW.value]])
            },
            "timestamp": timestamp
        }
        
        self._previous_recommendations.append(result)
        if len(self._previous_recommendations) > 50:
            self._previous_recommendations = self._previous_recommendations[-50:]
        
        return result
    
    def _recommendation_from_issue(self, issue: Dict[str, Any]) -> Optional[Recommendation]:
        """Generate recommendation from an issue."""
        severity = issue.get("severity", "low")
        category = issue.get("category", "")
        affected = issue.get("affected_components", [])
        
        self._rec_counter += 1
        rec_id = f"rec_{self._rec_counter:05d}"
        
        # Map severity to priority
        if severity in ["critical", "high"]:
            priority = Priority.HIGH.value
        elif severity == "medium":
            priority = Priority.MEDIUM.value
        else:
            priority = Priority.LOW.value
        
        # Determine recommendation based on issue
        if "failure" in issue.get("title", "").lower():
            template = self.RECOMMENDATION_TEMPLATES.get("high_failure_rate", {})
            rec_type = RecommendationType.REFACTOR.value
            title = f"Improve reliability of {', '.join(affected)}"
            hints = template.get("hints", [])
            risk = RiskLevel.MEDIUM.value
            effort = EffortEstimate.MEDIUM.value
        elif "latency" in issue.get("title", "").lower() or "performance" in category:
            template = self.RECOMMENDATION_TEMPLATES.get("high_latency", {})
            rec_type = RecommendationType.OPTIMIZATION.value
            title = f"Optimize performance of {', '.join(affected)}"
            hints = template.get("hints", [])
            risk = RiskLevel.LOW.value
            effort = EffortEstimate.MEDIUM.value
        else:
            rec_type = RecommendationType.REFACTOR.value
            title = f"Address: {issue.get('title', 'Unknown issue')}"
            hints = ["Review and fix the identified issue", "Add tests to prevent regression"]
            risk = RiskLevel.LOW.value
            effort = EffortEstimate.LOW.value
        
        return Recommendation(
            rec_id=rec_id,
            title=title,
            description=f"Address issue: {issue.get('description', '')}",
            recommendation_type=rec_type,
            scope=f"Affects {len(affected)} component(s): {', '.join(affected[:3])}",
            risk=risk,
            effort=effort,
            priority=priority,
            confidence=0.8 if severity in ["critical", "high"] else 0.6,
            rationale=f"Issue severity: {severity}. Evidence: {issue.get('evidence', [])}",
            affected_components=affected,
            dependencies=[],
            prerequisites=[],
            expected_benefits=["Improved reliability", "Reduced failure rate"],
            implementation_hints=hints
        )
    
    def _recommendation_from_bottleneck(self, bottleneck: Dict[str, Any]) -> Optional[Recommendation]:
        """Generate recommendation from a bottleneck."""
        self._rec_counter += 1
        rec_id = f"rec_{self._rec_counter:05d}"
        component = bottleneck.get("component", "unknown")
        
        return Recommendation(
            rec_id=rec_id,
            title=f"Optimize {component} for better throughput",
            description=bottleneck.get("recommendation", f"Address performance bottleneck in {component}"),
            recommendation_type=RecommendationType.OPTIMIZATION.value,
            scope=f"Performance bottleneck rank #{bottleneck.get('rank', '?')}",
            risk=RiskLevel.LOW.value,
            effort=EffortEstimate.MEDIUM.value,
            priority=Priority.MEDIUM.value if bottleneck.get("rank", 99) <= 2 else Priority.LOW.value,
            confidence=0.75,
            rationale=f"Avg duration: {bottleneck.get('avg_duration_ms', 0):.0f}ms",
            affected_components=[component],
            dependencies=[],
            prerequisites=["Performance profiling"],
            expected_benefits=["Reduced latency", "Improved throughput"],
            implementation_hints=self.RECOMMENDATION_TEMPLATES.get("high_latency", {}).get("hints", [])
        )
    
    def _recommendation_from_debt(self, debt_item: Dict[str, Any]) -> Optional[Recommendation]:
        """Generate recommendation from technical debt."""
        self._rec_counter += 1
        rec_id = f"rec_{self._rec_counter:05d}"
        debt_type = debt_item.get("type", "unknown")
        component = debt_item.get("component", "unknown")
        
        if debt_type == "missing_tests":
            template = self.RECOMMENDATION_TEMPLATES["missing_tests"]
            title = f"Add test coverage for {component}"
            hints = template["hints"]
            priority = Priority.MEDIUM.value
        elif debt_type in ["missing_docs", "missing_documentation"]:
            template = self.RECOMMENDATION_TEMPLATES["missing_docs"]
            title = f"Document {component}"
            hints = template["hints"]
            priority = Priority.LOW.value
        else:
            title = f"Address technical debt in {component}"
            hints = ["Review and refactor as needed"]
            priority = Priority.LOW.value
        
        return Recommendation(
            rec_id=rec_id,
            title=title,
            description=debt_item.get("description", f"Reduce technical debt: {debt_type}"),
            recommendation_type=RecommendationType.REFACTOR.value,
            scope=f"Technical debt in {component}",
            risk=RiskLevel.MINIMAL.value,
            effort=debt_item.get("effort", EffortEstimate.MEDIUM.value),
            priority=priority,
            confidence=0.9,
            rationale=f"Identified debt type: {debt_type}",
            affected_components=[component],
            dependencies=[],
            prerequisites=[],
            expected_benefits=["Improved maintainability", "Better developer experience"],
            implementation_hints=hints
        )
    
    def _recommendation_from_pattern(self, pattern_name: str, pattern_data: Dict) -> Optional[Recommendation]:
        """Generate recommendation from detected pattern."""
        self._rec_counter += 1
        rec_id = f"rec_{self._rec_counter:05d}"
        
        if pattern_name == "cascade_failure":
            template = self.RECOMMENDATION_TEMPLATES["cascade_failure"]
            return Recommendation(
                rec_id=rec_id,
                title="Implement failure isolation between agents",
                description=pattern_data.get("description", "Prevent cascade failures"),
                recommendation_type=RecommendationType.ARCHITECTURE.value,
                scope="System-wide failure isolation",
                risk=RiskLevel.MEDIUM.value,
                effort=EffortEstimate.HIGH.value,
                priority=Priority.HIGH.value,
                confidence=0.85,
                rationale=f"Detected {pattern_data.get('count', 0)} related failures",
                affected_components=pattern_data.get("affected_agents", []),
                dependencies=["circuit_breaker_library"],
                prerequisites=["Architecture review"],
                expected_benefits=["Improved fault tolerance", "Faster recovery"],
                implementation_hints=template["hints"]
            )
        else:
            return Recommendation(
                rec_id=rec_id,
                title=f"Address pattern: {pattern_name}",
                description=pattern_data.get("description", ""),
                recommendation_type=RecommendationType.REFACTOR.value,
                scope="Pattern mitigation",
                risk=RiskLevel.LOW.value,
                effort=EffortEstimate.MEDIUM.value,
                priority=Priority.MEDIUM.value,
                confidence=0.7,
                rationale=f"Pattern detected with {pattern_data.get('count', 0)} occurrences",
                affected_components=pattern_data.get("affected_agents", []),
                dependencies=[],
                prerequisites=[],
                expected_benefits=["Pattern addressed"],
                implementation_hints=[]
            )
    
    def _deduplicate_recommendations(self, recs: List[Recommendation]) -> List[Recommendation]:
        """Remove duplicate recommendations based on affected components and type."""
        seen = set()
        unique = []
        for rec in recs:
            key = (tuple(sorted(rec.affected_components)), rec.recommendation_type)
            if key not in seen:
                seen.add(key)
                unique.append(rec)
        return unique
    
    def _prioritize_recommendations(self, recs: List[Recommendation]) -> List[Recommendation]:
        """Sort recommendations by priority and confidence."""
        priority_order = {Priority.HIGH.value: 0, Priority.MEDIUM.value: 1, Priority.LOW.value: 2}
        return sorted(recs, key=lambda r: (priority_order.get(r.priority, 99), -r.confidence))
    
    def _count_by_type(self, recs: List[Recommendation]) -> Dict[str, int]:
        counts = {}
        for rec in recs:
            counts[rec.recommendation_type] = counts.get(rec.recommendation_type, 0) + 1
        return counts
    
    def _count_by_priority(self, recs: List[Recommendation]) -> Dict[str, int]:
        counts = {}
        for rec in recs:
            counts[rec.priority] = counts.get(rec.priority, 0) + 1
        return counts
    
    def suggest_new_agent(self, gap_description: str, use_cases: List[str]) -> Recommendation:
        """Suggest creation of a new agent to fill a capability gap."""
        self._rec_counter += 1
        rec_id = f"rec_{self._rec_counter:05d}"
        
        return Recommendation(
            rec_id=rec_id,
            title=f"New Agent: {gap_description[:50]}",
            description=f"Propose new agent to address: {gap_description}",
            recommendation_type=RecommendationType.NEW_AGENT.value,
            scope="System capability expansion",
            risk=RiskLevel.MEDIUM.value,
            effort=EffortEstimate.SIGNIFICANT.value,
            priority=Priority.MEDIUM.value,
            confidence=0.6,
            rationale=f"Gap identified. Use cases: {use_cases}",
            affected_components=["agents"],
            dependencies=["core.memory", "core.logger", "core.context_manager"],
            prerequisites=["Design review", "Architecture approval"],
            expected_benefits=["New capability", "Address gap"],
            implementation_hints=[
                "Follow existing agent patterns",
                "Create in agents/{agent_name}/ directory",
                "Include run.py for CLI access",
                "Add comprehensive tests"
            ]
        )
    
    def suggest_deprecation(self, component: str, reason: str, replacement: Optional[str] = None) -> Recommendation:
        """Suggest deprecation of a component."""
        self._rec_counter += 1
        rec_id = f"rec_{self._rec_counter:05d}"
        
        return Recommendation(
            rec_id=rec_id,
            title=f"Deprecate: {component}",
            description=f"Recommend deprecating {component}. Reason: {reason}",
            recommendation_type=RecommendationType.DEPRECATION.value,
            scope=f"Deprecation of {component}",
            risk=RiskLevel.MEDIUM.value,
            effort=EffortEstimate.MEDIUM.value,
            priority=Priority.LOW.value,
            confidence=0.7,
            rationale=reason,
            affected_components=[component],
            dependencies=[],
            prerequisites=["Impact analysis", "Migration plan"] + ([f"Replacement: {replacement}"] if replacement else []),
            expected_benefits=["Reduced complexity", "Cleaner codebase"],
            implementation_hints=[
                "Mark as deprecated with warning",
                "Create migration guide",
                "Set removal timeline",
                "Update dependent code"
            ]
        )
