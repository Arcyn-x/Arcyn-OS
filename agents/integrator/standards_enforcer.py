"""
Standards Enforcer module for Integrator Agent.

Enforces naming conventions, folder structure rules, module interface contracts,
and versioning policies.
"""

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import json


class StandardsEnforcer:
    """
    Enforces system-wide standards.
    
    Responsibilities:
    - Enforce naming conventions
    - Enforce folder structure rules
    - Enforce module interface contracts
    - Enforce versioning policies
    
    This module must reference standards defined by the System Designer Agent.
    
    TODO: Load standards from System Designer Agent output
    TODO: Add file system validation
    TODO: Implement code style checking
    TODO: Add version compatibility enforcement
    """
    
    def __init__(self, standards: Optional[Dict[str, Any]] = None):
        """
        Initialize the standards enforcer.
        
        Args:
            standards: Optional standards dictionary (loads defaults if None)
        """
        if standards:
            self.standards = standards
        else:
            self.standards = self._load_default_standards()
    
    def _load_default_standards(self) -> Dict[str, Any]:
        """
        Load default standards (matches System Designer Agent standards).
        
        Returns:
            Standards dictionary
        """
        return {
            "naming_conventions": {
                "modules": {"pattern": "snake_case"},
                "classes": {"pattern": "PascalCase"},
                "functions": {"pattern": "snake_case"},
                "constants": {"pattern": "UPPER_SNAKE_CASE"},
                "agents": {"pattern": "PascalCase with Agent suffix"}
            },
            "folder_structure": {
                "core": {"path": "core/"},
                "agents": {"path": "agents/{agent_name}/"},
                "design": {"path": "design/"},
                "backups": {"path": "backups/"}
            },
            "module_interfaces": {
                "required_exports": True,
                "docstrings": {"required": True},
                "type_hints": {"required": True}
            },
            "versioning": {
                "semantic_versioning": {"pattern": "MAJOR.MINOR.PATCH"}
            }
        }
    
    def enforce_naming(self, name: str, category: str) -> Tuple[bool, Optional[str]]:
        """
        Enforce naming convention for a name.
        
        Args:
            name: Name to validate
            category: Category (modules, classes, functions, constants, agents)
        
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        conventions = self.standards.get("naming_conventions", {})
        
        if category not in conventions:
            return False, f"Unknown naming category: {category}"
        
        pattern = conventions[category].get("pattern", "")
        
        # Basic validation
        if category == "modules" and not name.replace("_", "").islower():
            return False, f"Module name '{name}' violates snake_case convention"
        elif category == "classes" and not name[0].isupper():
            return False, f"Class name '{name}' violates PascalCase convention"
        elif category == "functions" and not name.replace("_", "").islower():
            return False, f"Function name '{name}' violates snake_case convention"
        elif category == "constants" and not name.isupper():
            return False, f"Constant name '{name}' violates UPPER_SNAKE_CASE convention"
        elif category == "agents" and not name.endswith("Agent"):
            return False, f"Agent name '{name}' must end with 'Agent'"
        
        return True, None
    
    def enforce_folder_structure(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Enforce folder structure rules for a file path.
        
        Args:
            file_path: File path to validate
        
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        path = Path(file_path)
        folder_structure = self.standards.get("folder_structure", {})
        
        # Check if path matches any allowed folder structure
        path_str = str(path.parent)
        
        # Check core folder
        if path_str.startswith("core"):
            return True, None
        
        # Check agents folder
        if path_str.startswith("agents"):
            return True, None
        
        # Check design folder
        if path_str.startswith("design"):
            return True, None
        
        # Check backups folder
        if path_str.startswith("backups"):
            return True, None
        
        # Root level files (like run.py) are allowed
        if path.parent == Path("."):
            return True, None
        
        return False, f"File path '{file_path}' violates folder structure rules"
    
    def enforce_module_interface(self, module_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Enforce module interface contract.
        
        Args:
            module_info: Module information dictionary with:
                - has_exports: Whether module has __all__ defined
                - has_docstrings: Whether module has docstrings
                - has_type_hints: Whether module has type hints
        
        Returns:
            Tuple of (is_valid: bool, violations: List[str])
        """
        violations = []
        interfaces = self.standards.get("module_interfaces", {})
        
        # Check required exports
        if interfaces.get("required_exports") and not module_info.get("has_exports", False):
            violations.append("Module missing required __all__ exports")
        
        # Check docstrings
        if interfaces.get("docstrings", {}).get("required") and not module_info.get("has_docstrings", False):
            violations.append("Module missing required docstrings")
        
        # Check type hints
        if interfaces.get("type_hints", {}).get("required") and not module_info.get("has_type_hints", False):
            violations.append("Module missing required type hints")
        
        return len(violations) == 0, violations
    
    def enforce_versioning(self, version: str) -> Tuple[bool, Optional[str]]:
        """
        Enforce versioning policy.
        
        Args:
            version: Version string to validate
        
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        versioning = self.standards.get("versioning", {})
        semantic = versioning.get("semantic_versioning", {})
        pattern = semantic.get("pattern", "MAJOR.MINOR.PATCH")
        
        # Basic semantic versioning check
        parts = version.split(".")
        if len(parts) != 3:
            return False, f"Version '{version}' does not match semantic versioning pattern (MAJOR.MINOR.PATCH)"
        
        try:
            major, minor, patch = map(int, parts)
            if major < 0 or minor < 0 or patch < 0:
                return False, "Version numbers must be non-negative"
        except ValueError:
            return False, f"Version '{version}' contains non-numeric parts"
        
        return True, None
    
    def validate_architect_plan_standards(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate Architect Agent plan against standards.
        
        Args:
            plan: Plan dictionary from Architect Agent
        
        Returns:
            Validation result dictionary
        """
        violations = []
        warnings = []
        
        # Validate task names
        tasks = plan.get("tasks", [])
        for task in tasks:
            task_name = task.get("name", "")
            if task_name:
                is_valid, error = self.enforce_naming(task_name, "functions")
                if not is_valid:
                    violations.append(f"Task name violation: {error}")
        
        # Validate milestone names
        milestones = plan.get("milestones", [])
        for milestone in milestones:
            milestone_name = milestone.get("name", "")
            if milestone_name:
                # Milestones can have spaces, so we'll just check they're not empty
                if not milestone_name:
                    violations.append("Milestone name cannot be empty")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings
        }
    
    def validate_builder_output_standards(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate Builder Agent output against standards.
        
        Args:
            output: Output dictionary from Builder Agent
        
        Returns:
            Validation result dictionary
        """
        violations = []
        warnings = []
        
        # Validate file paths
        files_changed = output.get("files_changed", [])
        for file_path in files_changed:
            is_valid, error = self.enforce_folder_structure(file_path)
            if not is_valid:
                violations.append(f"File path violation: {error}")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings
        }
    
    def validate_system_design_standards(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate System Designer Agent output against standards.
        
        Args:
            design: Design dictionary from System Designer Agent
        
        Returns:
            Validation result dictionary
        """
        violations = []
        warnings = []
        
        # Validate module names
        modules = design.get("modules", [])
        for module in modules:
            module_name = module.get("name", "")
            if module_name:
                is_valid, error = self.enforce_naming(module_name, "modules")
                if not is_valid:
                    violations.append(f"Module name violation: {error}")
        
        # Validate version
        architecture = design.get("architecture", {})
        version = architecture.get("version", "")
        if version:
            is_valid, error = self.enforce_versioning(version)
            if not is_valid:
                violations.append(f"Version violation: {error}")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings
        }
    
    def load_standards_from_design(self, design: Dict[str, Any]) -> None:
        """
        Load standards from System Designer Agent output.
        
        Args:
            design: Design dictionary from System Designer Agent
        """
        standards = design.get("standards", {})
        if standards:
            self.standards = standards

