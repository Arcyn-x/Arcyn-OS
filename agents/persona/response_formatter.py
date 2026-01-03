"""
Response Formatter module for Persona Agent.

Converts raw JSON outputs into human-readable responses.
"""

from typing import Dict, Any, List, Optional


class ResponseFormatter:
    """
    Formats system outputs for human consumption.
    
    Responsibilities:
    - Convert raw JSON outputs into human-readable responses
    - Preserve technical clarity
    - Avoid verbosity
    - Highlight warnings and blockers
    
    Must support: summary mode, verbose mode
    
    TODO: Add markdown formatting
    TODO: Implement color coding for terminals
    TODO: Add progress indicators
    TODO: Support different output formats (JSON, YAML, table)
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the response formatter.
        
        Args:
            verbose: Whether to use verbose output mode
        """
        self.verbose = verbose
    
    def format(self, output: Dict[str, Any], intent: Optional[str] = None) -> str:
        """
        Format system output into human-readable text.
        
        Args:
            output: System output dictionary
            intent: Optional intent that generated this output
        
        Returns:
            Formatted string
        """
        if not output:
            return "No output received."
        
        # Route to appropriate formatter based on output structure
        if "status" in output and "violations" in output:
            # Integration result
            return self._format_integration_result(output)
        elif "goal" in output and "tasks" in output:
            # Architect plan
            return self._format_architect_plan(output)
        elif "architecture" in output:
            # System design
            return self._format_system_design(output)
        elif "action" in output and "files_changed" in output:
            # Builder output
            return self._format_builder_output(output)
        elif "state" in output:
            # Status output
            return self._format_status(output)
        elif "error" in output:
            # Error output
            return self._format_error(output)
        else:
            # Generic output
            return self._format_generic(output)
    
    def _format_integration_result(self, result: Dict[str, Any]) -> str:
        """Format Integrator Agent result."""
        lines = []
        
        status = result.get("status", "unknown").upper()
        lines.append(f"Integration Status: {status}")
        lines.append("")
        
        violations = result.get("violations", [])
        warnings = result.get("warnings", [])
        
        if violations:
            lines.append(f"Violations ({len(violations)}):")
            for violation in violations[:5]:  # Show first 5
                lines.append(f"  - {violation}")
            if len(violations) > 5:
                lines.append(f"  ... and {len(violations) - 5} more")
            lines.append("")
        
        if warnings:
            lines.append(f"Warnings ({len(warnings)}):")
            for warning in warnings[:5]:  # Show first 5
                lines.append(f"  - {warning}")
            if len(warnings) > 5:
                lines.append(f"  ... and {len(warnings) - 5} more")
            lines.append("")
        
        summary = result.get("integration_summary", "")
        if summary:
            lines.append(f"Summary: {summary}")
        
        return "\n".join(lines)
    
    def _format_architect_plan(self, plan: Dict[str, Any]) -> str:
        """Format Architect Agent plan."""
        lines = []
        
        goal = plan.get("goal", "")
        lines.append(f"Plan: {goal}")
        lines.append("")
        
        milestones = plan.get("milestones", [])
        tasks = plan.get("tasks", [])
        
        lines.append(f"Milestones: {len(milestones)}")
        lines.append(f"Tasks: {len(tasks)}")
        lines.append("")
        
        if self.verbose and milestones:
            lines.append("Milestones:")
            for milestone in milestones[:3]:  # Show first 3
                lines.append(f"  - {milestone.get('name', 'Unknown')}")
            if len(milestones) > 3:
                lines.append(f"  ... and {len(milestones) - 3} more")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_system_design(self, design: Dict[str, Any]) -> str:
        """Format System Designer Agent output."""
        lines = []
        
        architecture = design.get("architecture", {})
        goal = architecture.get("goal", "")
        lines.append(f"Architecture: {goal}")
        lines.append("")
        
        modules = design.get("modules", [])
        lines.append(f"Modules: {len(modules)}")
        
        if self.verbose and modules:
            lines.append("")
            lines.append("Modules:")
            for module in modules[:5]:  # Show first 5
                name = module.get("name", "Unknown")
                layer = module.get("layer", "unknown")
                lines.append(f"  - {name} ({layer})")
            if len(modules) > 5:
                lines.append(f"  ... and {len(modules) - 5} more")
        
        return "\n".join(lines)
    
    def _format_builder_output(self, output: Dict[str, Any]) -> str:
        """Format Builder Agent output."""
        lines = []
        
        action = output.get("action", "unknown")
        summary = output.get("summary", "")
        lines.append(f"Build {action}: {summary}")
        lines.append("")
        
        files_changed = output.get("files_changed", [])
        if files_changed:
            lines.append(f"Files changed ({len(files_changed)}):")
            for file_path in files_changed[:5]:  # Show first 5
                lines.append(f"  - {file_path}")
            if len(files_changed) > 5:
                lines.append(f"  ... and {len(files_changed) - 5} more")
        
        warnings = output.get("warnings", [])
        if warnings:
            lines.append("")
            lines.append(f"Warnings ({len(warnings)}):")
            for warning in warnings[:3]:  # Show first 3
                lines.append(f"  - {warning}")
        
        return "\n".join(lines)
    
    def _format_status(self, status: Dict[str, Any]) -> str:
        """Format status output."""
        lines = []
        
        agent_id = status.get("agent_id", "unknown")
        state = status.get("state", "unknown")
        
        lines.append(f"Agent: {agent_id}")
        lines.append(f"State: {state}")
        
        if self.verbose:
            context = status.get("context", {})
            if context:
                lines.append("")
                lines.append("Context:")
                for key, value in list(context.items())[:5]:  # Show first 5
                    if isinstance(value, (str, int, bool)):
                        lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)
    
    def _format_error(self, error: Dict[str, Any]) -> str:
        """Format error output."""
        error_msg = error.get("error", "Unknown error")
        return f"Error: {error_msg}"
    
    def _format_generic(self, output: Dict[str, Any]) -> str:
        """Format generic output."""
        if self.verbose:
            import json
            return json.dumps(output, indent=2)
        else:
            # Try to extract a summary
            if "summary" in output:
                return output["summary"]
            elif "message" in output:
                return output["message"]
            else:
                return "Operation completed."
    
    def format_help(self, commands: List[Dict[str, str]]) -> str:
        """
        Format help output.
        
        Args:
            commands: List of available commands
        
        Returns:
            Formatted help text
        """
        lines = []
        lines.append("Available Commands:")
        lines.append("")
        
        for cmd in commands:
            intent = cmd.get("intent", "")
            description = cmd.get("description", "")
            agent = cmd.get("agent", "")
            lines.append(f"  {intent:12} - {description} ({agent} agent)")
        
        lines.append("")
        lines.append("Examples:")
        lines.append('  build "Create a memory module"')
        lines.append('  design "Design Arcyn OS kernel"')
        lines.append("  status")
        lines.append("  help")
        
        return "\n".join(lines)
    
    def format_explain(self, topic: str) -> str:
        """
        Format explanation output.
        
        Args:
            topic: Topic to explain
        
        Returns:
            Explanation text
        """
        explanations = {
            "architect": "The Architect Agent (A-1) plans development work by breaking goals into tasks and milestones.",
            "builder": "The Builder Agent (F-1) scaffolds and writes code files based on plans.",
            "system_designer": "The System Designer Agent (F-2) designs system architecture and standards.",
            "integrator": "The Integrator Agent (F-3) validates and enforces integration rules.",
            "persona": "The Persona Agent (S-1) is the human interface to Arcyn OS."
        }
        
        topic_lower = topic.lower()
        for key, explanation in explanations.items():
            if key in topic_lower:
                return explanation
        
        return f"I can explain: architect, builder, system_designer, integrator, persona"
    
    def set_verbose(self, verbose: bool) -> None:
        """
        Set verbose mode.
        
        Args:
            verbose: Whether to use verbose output
        """
        self.verbose = verbose

