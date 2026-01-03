"""
Integration Report module for Integrator Agent.

Generates human-readable integration summaries and machine-readable integration reports.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class IntegrationReport:
    """
    Generates integration reports.
    
    Responsibilities:
    - Generate human-readable integration summaries
    - Generate machine-readable integration reports (JSON)
    - Highlight risks and required actions
    
    TODO: Add HTML report generation
    TODO: Add PDF export
    TODO: Implement report templates
    TODO: Add historical report tracking
    """
    
    def __init__(self):
        """Initialize the integration report generator."""
        pass
    
    def generate_report(self, integration_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete integration report.
        
        Args:
            integration_result: Result from IntegratorAgent.integrate()
        
        Returns:
            Complete report dictionary
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": integration_result.get("status", "unknown"),
            "summary": self._generate_summary(integration_result),
            "violations": integration_result.get("violations", []),
            "warnings": integration_result.get("warnings", []),
            "actions_required": integration_result.get("actions_required", []),
            "risks": self._identify_risks(integration_result),
            "recommendations": self._generate_recommendations(integration_result),
            "details": integration_result.get("validation_details", {})
        }
        
        return report
    
    def _generate_summary(self, result: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary.
        
        Args:
            result: Integration result dictionary
        
        Returns:
            Summary string
        """
        status = result.get("status", "unknown")
        violations_count = len(result.get("violations", []))
        warnings_count = len(result.get("warnings", []))
        
        if status == "approved":
            summary = f"Integration APPROVED. "
            if warnings_count > 0:
                summary += f"{warnings_count} warning(s) present but non-blocking."
            else:
                summary += "No issues detected."
        
        elif status == "blocked":
            summary = f"Integration BLOCKED. {violations_count} violation(s) detected that prevent integration."
        
        else:  # warnings
            summary = f"Integration has WARNINGS. {warnings_count} warning(s) require attention before proceeding."
        
        return summary
    
    def _identify_risks(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Identify risks in the integration.
        
        Args:
            result: Integration result dictionary
        
        Returns:
            List of risk dictionaries
        """
        risks = []
        
        violations = result.get("violations", [])
        if violations:
            risks.append({
                "level": "high",
                "category": "violations",
                "description": f"{len(violations)} violation(s) detected",
                "impact": "Integration blocked"
            })
        
        warnings = result.get("warnings", [])
        if len(warnings) > 5:
            risks.append({
                "level": "medium",
                "category": "warnings",
                "description": f"{len(warnings)} warning(s) may indicate systemic issues",
                "impact": "May cause problems in production"
            })
        
        # Check for circular dependencies
        details = result.get("validation_details", {})
        if details.get("dependency_check", {}).get("has_circular_dependencies"):
            risks.append({
                "level": "high",
                "category": "dependencies",
                "description": "Circular dependencies detected",
                "impact": "System may deadlock or fail to initialize"
            })
        
        # Check for layer violations
        if details.get("dependency_check", {}).get("layer_violations"):
            risks.append({
                "level": "high",
                "category": "architecture",
                "description": "Layer dependency violations detected",
                "impact": "Architectural integrity compromised"
            })
        
        return risks
    
    def _generate_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on integration result.
        
        Args:
            result: Integration result dictionary
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        status = result.get("status", "unknown")
        
        if status == "blocked":
            recommendations.append("Fix all violations before attempting integration")
            recommendations.append("Review architectural constraints and standards")
        
        violations = result.get("violations", [])
        if violations:
            recommendations.append(f"Address {len(violations)} violation(s) to proceed")
        
        warnings = result.get("warnings", [])
        if warnings:
            recommendations.append(f"Review {len(warnings)} warning(s) before production deployment")
        
        actions = result.get("actions_required", [])
        if actions:
            recommendations.append("Complete required actions before integration")
        
        if status == "approved":
            recommendations.append("Integration ready for deployment")
            recommendations.append("Monitor system after integration")
        
        return recommendations
    
    def to_json(self, report: Dict[str, Any]) -> str:
        """
        Export report as JSON.
        
        Args:
            report: Report dictionary
        
        Returns:
            JSON string representation
        """
        return json.dumps(report, indent=2)
    
    def to_markdown(self, report: Dict[str, Any]) -> str:
        """
        Export report as Markdown.
        
        Args:
            report: Report dictionary
        
        Returns:
            Markdown string representation
        """
        md = []
        
        # Header
        md.append(f"# Integration Report")
        md.append(f"**Generated**: {report.get('timestamp', 'Unknown')}")
        md.append(f"**Status**: {report.get('status', 'unknown').upper()}\n")
        
        # Summary
        md.append("## Summary\n")
        md.append(f"{report.get('summary', 'No summary available')}\n")
        
        # Violations
        violations = report.get("violations", [])
        if violations:
            md.append("## Violations\n")
            for i, violation in enumerate(violations, 1):
                md.append(f"{i}. {violation}")
            md.append("")
        
        # Warnings
        warnings = report.get("warnings", [])
        if warnings:
            md.append("## Warnings\n")
            for i, warning in enumerate(warnings, 1):
                md.append(f"{i}. {warning}")
            md.append("")
        
        # Risks
        risks = report.get("risks", [])
        if risks:
            md.append("## Risks\n")
            for risk in risks:
                md.append(f"### {risk.get('category', 'Unknown')} - {risk.get('level', 'unknown').upper()}")
                md.append(f"- **Description**: {risk.get('description')}")
                md.append(f"- **Impact**: {risk.get('impact')}\n")
        
        # Actions Required
        actions = report.get("actions_required", [])
        if actions:
            md.append("## Actions Required\n")
            for i, action in enumerate(actions, 1):
                md.append(f"{i}. {action}")
            md.append("")
        
        # Recommendations
        recommendations = report.get("recommendations", [])
        if recommendations:
            md.append("## Recommendations\n")
            for i, rec in enumerate(recommendations, 1):
                md.append(f"{i}. {rec}")
            md.append("")
        
        # Details
        details = report.get("details", {})
        if details:
            md.append("## Validation Details\n")
            md.append("```json")
            md.append(json.dumps(details, indent=2))
            md.append("```\n")
        
        return "\n".join(md)
    
    def generate_summary_report(self, integration_result: Dict[str, Any]) -> str:
        """
        Generate a brief summary report.
        
        Args:
            integration_result: Integration result dictionary
        
        Returns:
            Summary string
        """
        status = integration_result.get("status", "unknown")
        violations = len(integration_result.get("violations", []))
        warnings = len(integration_result.get("warnings", []))
        
        summary = f"Integration Status: {status.upper()}\n"
        summary += f"Violations: {violations}\n"
        summary += f"Warnings: {warnings}\n"
        
        if violations > 0:
            summary += "\nBlocking Violations:\n"
            for violation in integration_result.get("violations", [])[:5]:
                summary += f"  - {violation}\n"
        
        return summary

