"""
Integrator Agent (F-3) for Arcyn OS.

The Integrator Agent is responsible for validation, enforcement, and coordination
between agents and modules.

It ensures that all outputs from Architect Agent (A-1), System Designer Agent (F-2),
and Builder Agent (F-1) are compatible, consistent, and safe to integrate.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from .contract_validator import ContractValidator
from .dependency_checker import DependencyChecker
from .standards_enforcer import StandardsEnforcer
from .integration_report import IntegrationReport
from core.logger import Logger
from core.context_manager import ContextManager
from core.memory import Memory


class IntegratorAgent:
    """
    Main Integrator Agent class.
    
    The Integrator Agent does not write production code, design architecture, or generate plans.
    It is an enforcer, not a creator.
    
    Example:
        >>> agent = IntegratorAgent(agent_id="integrator_001")
        >>> payload = {
        ...     "architect_plan": {...},
        ...     "system_design": {...},
        ...     "builder_output": {...}
        ... }
        >>> result = agent.integrate(payload)
    """
    
    def __init__(self, agent_id: str = "integrator_agent", log_level: int = 20):
        """
        Initialize the Integrator Agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            log_level: Logging level (default: 20 = INFO)
        """
        self.agent_id = agent_id
        self.logger = Logger(f"IntegratorAgent-{agent_id}", log_level=log_level)
        self.context = ContextManager(agent_id)
        self.memory = Memory()
        
        # Initialize sub-components
        self.contract_validator = ContractValidator()
        self.dependency_checker = DependencyChecker()
        self.standards_enforcer = StandardsEnforcer()
        self.report_generator = IntegrationReport()
        
        self.logger.info(f"Integrator Agent {agent_id} initialized")
        self.context.set_state('idle')
    
    def integrate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate outputs from multiple agents and validate compatibility.
        
        Args:
            payload: Dictionary containing:
                - architect_plan: Plan from Architect Agent (optional)
                - system_design: Design from System Designer Agent (optional)
                - builder_output: Output from Builder Agent (optional)
                - messages: List of agent messages (optional)
        
        Returns:
            Dictionary containing:
            {
                "status": "approved | blocked | warnings",
                "violations": [],
                "warnings": [],
                "actions_required": [],
                "integration_summary": "",
                "validation_details": {}
            }
        """
        self.logger.info("Starting integration validation")
        self.context.set_state('integrating')
        self.context.add_history('integration_started', {'payload_keys': list(payload.keys())})
        
        result = {
            "status": "approved",
            "violations": [],
            "warnings": [],
            "actions_required": [],
            "integration_summary": "",
            "validation_details": {}
        }
        
        try:
            # Step 1: Contract validation
            contract_valid, contract_errors, contract_details = self.contract_validator.validate_payload(payload)
            result["validation_details"]["contract_validation"] = contract_details
            
            if not contract_valid:
                result["violations"].extend(contract_errors)
                result["status"] = "blocked"
            
            # Step 2: Dependency checking
            dependency_results = {}
            if "system_design" in payload:
                design = payload["system_design"]
                architecture = design.get("architecture", {})
                dep_result = self.dependency_checker.validate_architecture_dependencies(architecture)
                dependency_results["architecture"] = dep_result
                
                if not dep_result.get("valid", True):
                    result["violations"].extend(dep_result.get("layer_violations", []))
                    if dep_result.get("circular_dependencies"):
                        result["violations"].append(f"Circular dependencies: {dep_result['circular_dependencies']}")
                    result["status"] = "blocked"
            
            # Also check dependencies from architect plan
            if "architect_plan" in payload:
                plan = payload["architect_plan"]
                task_graph = plan.get("task_graph", {})
                if task_graph:
                    # Extract dependencies from task graph
                    edges = task_graph.get("edges", [])
                    dependencies = {}
                    for edge in edges:
                        from_task = edge.get("from")
                        to_task = edge.get("to")
                        if from_task not in dependencies:
                            dependencies[from_task] = []
                        dependencies[from_task].append(to_task)
                    
                    if dependencies:
                        dep_result = self.dependency_checker.validate_dependency_graph(dependencies)
                        dependency_results["task_graph"] = dep_result
                        
                        if not dep_result.get("valid", True):
                            result["warnings"].extend(dep_result.get("layer_violations", []))
                            if dep_result.get("circular_dependencies"):
                                result["warnings"].append(f"Task graph circular dependencies: {dep_result['circular_dependencies']}")
            
            result["validation_details"]["dependency_check"] = dependency_results
            
            # Step 3: Standards enforcement
            standards_results = {}
            
            if "architect_plan" in payload:
                plan_result = self.standards_enforcer.validate_architect_plan_standards(payload["architect_plan"])
                standards_results["architect_plan"] = plan_result
                if not plan_result.get("valid", True):
                    result["violations"].extend(plan_result.get("violations", []))
                    result["status"] = "blocked"
            
            if "system_design" in payload:
                design_result = self.standards_enforcer.validate_system_design_standards(payload["system_design"])
                standards_results["system_design"] = design_result
                if not design_result.get("valid", True):
                    result["violations"].extend(design_result.get("violations", []))
                    result["status"] = "blocked"
            
            if "builder_output" in payload:
                builder_result = self.standards_enforcer.validate_builder_output_standards(payload["builder_output"])
                standards_results["builder_output"] = builder_result
                if not builder_result.get("valid", True):
                    result["violations"].extend(builder_result.get("violations", []))
                    result["status"] = "blocked"
            
            result["validation_details"]["standards_enforcement"] = standards_results
            
            # Step 4: Cross-validation (check consistency between agents)
            cross_validation = self._cross_validate(payload)
            if cross_validation.get("inconsistencies"):
                result["warnings"].extend(cross_validation["inconsistencies"])
                if result["status"] == "approved":
                    result["status"] = "warnings"
            
            result["validation_details"]["cross_validation"] = cross_validation
            
            # Step 5: Generate actions required
            if result["violations"]:
                result["actions_required"].append("Fix all violations before integration")
            if result["warnings"]:
                result["actions_required"].append("Review warnings before proceeding")
            
            # Generate summary
            result["integration_summary"] = self._generate_integration_summary(result)
            
            # Store result
            integration_key = f"integration_{self.agent_id}_{self.context.get_context()['created_at']}"
            self.memory.write(integration_key, result)
            
            self.context.set_data('last_integration', result)
            self.context.add_history('integration_completed', {'status': result["status"]})
            self.context.set_state('idle')
            
            self.logger.info(f"Integration completed: {result['status']}")
            return result
            
        except Exception as e:
            error_msg = f"Error during integration: {str(e)}"
            self.logger.error(error_msg)
            result["violations"].append(error_msg)
            result["status"] = "blocked"
            result["integration_summary"] = f"Integration failed: {str(e)}"
            self.context.set_state('error')
            self.context.add_history('integration_failed', {'error': str(e)})
            return result
    
    def validate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a payload without full integration.
        
        Args:
            payload: Payload to validate
        
        Returns:
            Validation result dictionary
        """
        self.logger.info("Running validation")
        self.context.set_state('validating')
        
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            # Contract validation
            contract_valid, contract_errors, contract_details = self.contract_validator.validate_payload(payload)
            result["details"]["contract_validation"] = contract_details
            
            if not contract_valid:
                result["valid"] = False
                result["errors"].extend(contract_errors)
            
            # Standards validation
            if "architect_plan" in payload:
                plan_result = self.standards_enforcer.validate_architect_plan_standards(payload["architect_plan"])
                if not plan_result.get("valid", True):
                    result["valid"] = False
                    result["errors"].extend(plan_result.get("violations", []))
            
            self.context.set_state('idle')
            return result
            
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            self.logger.error(error_msg)
            result["valid"] = False
            result["errors"].append(error_msg)
            self.context.set_state('error')
            return result
    
    def block(self, reason: str) -> Dict[str, Any]:
        """
        Explicitly block an integration with a reason.
        
        Args:
            reason: Reason for blocking
        
        Returns:
            Blocked integration result dictionary
        """
        self.logger.warning(f"Integration blocked: {reason}")
        self.context.set_state('blocking')
        
        result = {
            "status": "blocked",
            "violations": [reason],
            "warnings": [],
            "actions_required": ["Resolve blocking issue: " + reason],
            "integration_summary": f"Integration blocked: {reason}",
            "validation_details": {}
        }
        
        self.context.add_history('integration_blocked', {'reason': reason})
        self.context.set_state('idle')
        
        return result
    
    def _cross_validate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cross-validate consistency between different agent outputs.
        
        Args:
            payload: Integration payload
        
        Returns:
            Cross-validation result dictionary
        """
        inconsistencies = []
        
        # Check if module names match between system design and builder output
        if "system_design" in payload and "builder_output" in payload:
            design = payload["system_design"]
            builder = payload["builder_output"]
            
            design_modules = {m.get("name") for m in design.get("modules", [])}
            builder_files = builder.get("files_changed", [])
            
            # Extract module names from file paths
            builder_modules = set()
            for file_path in builder_files:
                # Simple extraction (e.g., "core/memory.py" -> "memory")
                parts = file_path.replace("\\", "/").split("/")
                if parts:
                    module_name = parts[-1].replace(".py", "")
                    builder_modules.add(module_name)
            
            # Check for modules in builder that aren't in design
            unexpected = builder_modules - design_modules
            if unexpected:
                inconsistencies.append(f"Builder created files for modules not in design: {unexpected}")
        
        # Check if task IDs in architect plan match referenced tasks
        if "architect_plan" in payload:
            plan = payload["architect_plan"]
            tasks = {t.get("id") for t in plan.get("tasks", [])}
            milestones = plan.get("milestones", [])
            
            for milestone in milestones:
                milestone_id = milestone.get("id")
                # Check if tasks reference this milestone
                milestone_tasks = [t for t in plan.get("tasks", []) if t.get("milestone_id") == milestone_id]
                if not milestone_tasks:
                    inconsistencies.append(f"Milestone {milestone_id} has no associated tasks")
        
        return {
            "inconsistencies": inconsistencies,
            "valid": len(inconsistencies) == 0
        }
    
    def _generate_integration_summary(self, result: Dict[str, Any]) -> str:
        """
        Generate integration summary text.
        
        Args:
            result: Integration result dictionary
        
        Returns:
            Summary string
        """
        status = result.get("status", "unknown")
        violations_count = len(result.get("violations", []))
        warnings_count = len(result.get("warnings", []))
        
        if status == "approved":
            return f"Integration approved. No violations detected."
        elif status == "blocked":
            return f"Integration blocked. {violations_count} violation(s) prevent integration."
        else:
            return f"Integration has {warnings_count} warning(s). Review recommended before proceeding."
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status and context.
        
        Returns:
            Dictionary with agent status, state, and context information
        """
        return {
            "agent_id": self.agent_id,
            "state": self.context.get_state(),
            "context": self.context.get_context(),
            "has_last_integration": self.context.get_data('last_integration') is not None
        }

