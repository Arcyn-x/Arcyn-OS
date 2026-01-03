"""
Standards module for System Designer Agent.

Defines system-wide rules: naming conventions, folder structure, module interfaces,
versioning rules, and deprecation policy.
"""

from typing import Dict, Any, List
from pathlib import Path
import json


class Standards:
    """
    Defines and enforces system-wide standards.
    
    These standards must be machine-readable (JSON) and human-readable (MD).
    
    TODO: Add validation against standards
    TODO: Implement standards versioning
    TODO: Add standards compliance checker
    TODO: Integrate with CI/CD for standards enforcement
    """
    
    def __init__(self):
        """Initialize the standards manager."""
        self.standards = self._load_default_standards()
    
    def _load_default_standards(self) -> Dict[str, Any]:
        """
        Load default Arcyn OS standards.
        
        Returns:
            Dictionary containing all standards
        """
        return {
            "naming_conventions": {
                "modules": {
                    "pattern": "snake_case",
                    "description": "Module files use snake_case (e.g., memory_manager.py)",
                    "examples": ["memory_manager.py", "context_manager.py", "task_graph.py"]
                },
                "classes": {
                    "pattern": "PascalCase",
                    "description": "Classes use PascalCase (e.g., MemoryManager)",
                    "examples": ["MemoryManager", "ContextManager", "TaskGraph"]
                },
                "functions": {
                    "pattern": "snake_case",
                    "description": "Functions use snake_case (e.g., read_memory)",
                    "examples": ["read_memory", "write_context", "validate_task"]
                },
                "constants": {
                    "pattern": "UPPER_SNAKE_CASE",
                    "description": "Constants use UPPER_SNAKE_CASE (e.g., MAX_SIZE)",
                    "examples": ["MAX_SIZE", "DEFAULT_TIMEOUT", "API_VERSION"]
                },
                "agents": {
                    "pattern": "PascalCase with Agent suffix",
                    "description": "Agent classes end with 'Agent' (e.g., ArchitectAgent)",
                    "examples": ["ArchitectAgent", "BuilderAgent", "SystemDesignerAgent"]
                }
            },
            "folder_structure": {
                "core": {
                    "path": "core/",
                    "description": "Core system modules",
                    "allowed_files": ["*.py"],
                    "required_files": ["__init__.py"]
                },
                "agents": {
                    "path": "agents/{agent_name}/",
                    "description": "Agent implementations",
                    "allowed_files": ["*.py"],
                    "required_files": ["__init__.py", "{agent_name}_agent.py"]
                },
                "design": {
                    "path": "design/",
                    "description": "Design artifacts and documentation",
                    "allowed_files": ["*.json", "*.md", "*.yaml", "*.yml"]
                },
                "backups": {
                    "path": "backups/",
                    "description": "File backups",
                    "allowed_files": ["*.py", "*.json"]
                }
            },
            "module_interfaces": {
                "required_exports": {
                    "description": "All modules must export public API via __all__",
                    "pattern": "__all__ = ['Class1', 'Class2', 'function1']"
                },
                "docstrings": {
                    "required": True,
                    "format": "Google style",
                    "description": "All public classes and functions must have docstrings"
                },
                "type_hints": {
                    "required": True,
                    "description": "All function signatures must include type hints"
                }
            },
            "versioning": {
                "semantic_versioning": {
                    "pattern": "MAJOR.MINOR.PATCH",
                    "description": "Use semantic versioning (e.g., 1.2.3)",
                    "breaking_changes": "Increment MAJOR",
                    "new_features": "Increment MINOR",
                    "bug_fixes": "Increment PATCH"
                },
                "agent_versioning": {
                    "format": "{agent_id}_v{version}",
                    "example": "architect_agent_v1.0.0"
                }
            },
            "deprecation_policy": {
                "notice_period": "2 minor versions",
                "description": "Deprecated features must be announced 2 minor versions before removal",
                "warnings": {
                    "required": True,
                    "format": "DeprecationWarning in code and documentation"
                },
                "migration_guide": {
                    "required": True,
                    "description": "Must provide migration guide for deprecated features"
                }
            },
            "code_quality": {
                "linter": {
                    "required": True,
                    "tools": ["pylint", "flake8", "mypy"],
                    "max_complexity": 10
                },
                "test_coverage": {
                    "minimum": 0.8,
                    "description": "Minimum 80% test coverage required"
                },
                "documentation": {
                    "required": True,
                    "format": "Docstrings + README.md per module"
                }
            },
            "agent_interaction": {
                "message_format": {
                    "type": "JSON",
                    "required_fields": ["action", "agent_id", "timestamp", "data"],
                    "description": "All agent-to-agent communication uses JSON"
                },
                "error_handling": {
                    "required": True,
                    "format": "Structured error responses with error codes"
                },
                "async_support": {
                    "current": False,
                    "future": True,
                    "description": "Future versions will support async operations"
                }
            }
        }
    
    def get_standards(self) -> Dict[str, Any]:
        """
        Get all standards.
        
        Returns:
            Complete standards dictionary
        """
        return self.standards.copy()
    
    def get_naming_conventions(self) -> Dict[str, Any]:
        """
        Get naming convention standards.
        
        Returns:
            Naming conventions dictionary
        """
        return self.standards.get("naming_conventions", {})
    
    def get_folder_structure(self) -> Dict[str, Any]:
        """
        Get folder structure standards.
        
        Returns:
            Folder structure rules dictionary
        """
        return self.standards.get("folder_structure", {})
    
    def get_module_interfaces(self) -> Dict[str, Any]:
        """
        Get module interface standards.
        
        Returns:
            Module interface rules dictionary
        """
        return self.standards.get("module_interfaces", {})
    
    def to_json(self) -> str:
        """
        Export standards as JSON.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.standards, indent=2)
    
    def to_markdown(self) -> str:
        """
        Export standards as Markdown documentation.
        
        Returns:
            Markdown string representation
        """
        md = ["# Arcyn OS Standards", "", "This document defines system-wide standards for Arcyn OS.", ""]
        
        # Naming Conventions
        md.append("## Naming Conventions\n")
        naming = self.standards.get("naming_conventions", {})
        for category, rules in naming.items():
            md.append(f"### {category.replace('_', ' ').title()}\n")
            md.append(f"- **Pattern**: {rules.get('pattern', 'N/A')}")
            md.append(f"- **Description**: {rules.get('description', 'N/A')}")
            if 'examples' in rules:
                md.append(f"- **Examples**: {', '.join(rules['examples'])}")
            md.append("")
        
        # Folder Structure
        md.append("## Folder Structure\n")
        folders = self.standards.get("folder_structure", {})
        for folder_name, rules in folders.items():
            md.append(f"### {folder_name}\n")
            md.append(f"- **Path**: `{rules.get('path', 'N/A')}`")
            md.append(f"- **Description**: {rules.get('description', 'N/A')}")
            md.append("")
        
        # Module Interfaces
        md.append("## Module Interfaces\n")
        interfaces = self.standards.get("module_interfaces", {})
        for rule_name, rule_value in interfaces.items():
            md.append(f"### {rule_name.replace('_', ' ').title()}\n")
            if isinstance(rule_value, dict):
                for key, value in rule_value.items():
                    md.append(f"- **{key}**: {value}")
            else:
                md.append(f"- {rule_value}")
            md.append("")
        
        # Versioning
        md.append("## Versioning\n")
        versioning = self.standards.get("versioning", {})
        for version_type, rules in versioning.items():
            md.append(f"### {version_type.replace('_', ' ').title()}\n")
            if isinstance(rules, dict):
                for key, value in rules.items():
                    md.append(f"- **{key}**: {value}")
            md.append("")
        
        # Deprecation Policy
        md.append("## Deprecation Policy\n")
        deprecation = self.standards.get("deprecation_policy", {})
        for key, value in deprecation.items():
            if isinstance(value, dict):
                md.append(f"### {key.replace('_', ' ').title()}\n")
                for sub_key, sub_value in value.items():
                    md.append(f"- **{sub_key}**: {sub_value}")
            else:
                md.append(f"- **{key}**: {value}")
            md.append("")
        
        return "\n".join(md)
    
    def validate_naming(self, name: str, category: str) -> tuple[bool, str]:
        """
        Validate a name against naming conventions.
        
        Args:
            name: Name to validate
            category: Category (modules, classes, functions, constants, agents)
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        conventions = self.get_naming_conventions()
        
        if category not in conventions:
            return False, f"Unknown category: {category}"
        
        pattern = conventions[category].get("pattern", "")
        
        # Basic validation (simplified)
        if category == "modules" and not name.replace("_", "").islower():
            return False, f"Module name '{name}' should be snake_case"
        elif category == "classes" and not name[0].isupper():
            return False, f"Class name '{name}' should be PascalCase"
        elif category == "functions" and not name.replace("_", "").islower():
            return False, f"Function name '{name}' should be snake_case"
        elif category == "constants" and not name.isupper():
            return False, f"Constant name '{name}' should be UPPER_SNAKE_CASE"
        elif category == "agents" and not name.endswith("Agent"):
            return False, f"Agent name '{name}' should end with 'Agent'"
        
        return True, ""

