"""
System Designer Agent (F-2) for Arcyn OS.

The System Designer Agent is responsible for architecture, standards, and structure —
not writing implementation code.

It defines how the system should be built, not how to build it line by line.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from .architecture_engine import ArchitectureEngine
from .schema_generator import SchemaGenerator
from .standards import Standards
from .dependency_mapper import DependencyMapper
from core.logger import Logger
from core.context_manager import ContextManager
from core.memory import Memory


class SystemDesignerAgent:
    """
    Main System Designer Agent class.
    
    The System Designer Agent does not write production code and does not modify files directly.
    It produces design artifacts, schemas, and standards.
    
    Example:
        >>> agent = SystemDesignerAgent(agent_id="designer_001")
        >>> result = agent.design("Design Arcyn OS memory system")
        >>> modules = agent.define_modules({"goal": "..."}, [{"name": "memory"}])
    """
    
    def __init__(self, agent_id: str = "system_designer_agent", log_level: int = 20):
        """
        Initialize the System Designer Agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            log_level: Logging level (default: 20 = INFO)
        """
        self.agent_id = agent_id
        self.logger = Logger(f"SystemDesignerAgent-{agent_id}", log_level=log_level)
        self.context = ContextManager(agent_id)
        self.memory = Memory()
        
        # Initialize sub-components
        self.architecture_engine = ArchitectureEngine()
        self.schema_generator = SchemaGenerator()
        self.standards = Standards()
        self.dependency_mapper = DependencyMapper()
        
        # Setup default layer dependencies
        self.dependency_mapper.set_allowed_direction("agents", "core")
        self.dependency_mapper.set_allowed_direction("interfaces", "core")
        self.dependency_mapper.set_allowed_direction("interfaces", "agents")
        
        self.logger.info(f"System Designer Agent {agent_id} initialized")
        self.context.set_state('idle')
    
    def design(self, goal: str, requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Design system architecture from a goal.
        
        Args:
            goal: High-level design goal (e.g., "Design Arcyn OS memory system")
            requirements: Optional requirements dictionary
        
        Returns:
            Dictionary containing:
            {
                "architecture": {},
                "modules": [],
                "schemas": [],
                "standards": {},
                "dependencies": {}
            }
        """
        self.logger.info(f"Designing: {goal}")
        self.context.set_state('designing')
        self.context.add_history('design_started', {'goal': goal})
        
        try:
            # Generate architecture
            architecture = self.architecture_engine.design_architecture(goal, requirements)
            
            # Generate schemas based on architecture
            schemas = self._generate_schemas_from_architecture(architecture)
            
            # Get standards
            standards = self.standards.get_standards()
            
            # Build dependency map
            dependencies = self._build_dependency_map(architecture)
            
            # Assemble result
            result = {
                "architecture": architecture,
                "modules": architecture.get("modules", []),
                "schemas": schemas,
                "standards": standards,
                "dependencies": dependencies,
                "metadata": {
                    "goal": goal,
                    "version": architecture.get("version", "1.0.0"),
                    "designer_id": self.agent_id
                }
            }
            
            # Store in memory
            design_key = f"design_{self.agent_id}_{self.context.get_context()['created_at']}"
            self.memory.write(design_key, result)
            
            self.context.set_data('current_design', result)
            self.context.add_history('design_completed', {'design_key': design_key})
            self.context.set_state('idle')
            
            self.logger.info(f"Design completed: {len(architecture.get('modules', []))} modules defined")
            return result
            
        except Exception as e:
            error_msg = f"Error during design: {str(e)}"
            self.logger.error(error_msg)
            self.context.set_state('error')
            self.context.add_history('design_failed', {'error': str(e)})
            raise
    
    def define_modules(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Define modules within an architecture context.
        
        Args:
            context: Context dictionary with:
                - architecture: Existing architecture (optional)
                - module_specs: List of module specifications
        
        Returns:
            Updated architecture with defined modules
        """
        self.logger.info("Defining modules")
        self.context.set_state('defining_modules')
        self.context.add_history('define_modules_started', {'context': context})
        
        try:
            architecture = context.get("architecture", {})
            module_specs = context.get("module_specs", [])
            
            if not architecture:
                # Create new architecture if none provided
                goal = context.get("goal", "Define modules")
                architecture = self.architecture_engine.design_architecture(goal)
            
            # Define modules
            updated_architecture = self.architecture_engine.define_modules(architecture, module_specs)
            
            # Update dependencies
            dependencies = self._build_dependency_map(updated_architecture)
            
            result = {
                "architecture": updated_architecture,
                "modules": updated_architecture.get("modules", []),
                "dependencies": dependencies
            }
            
            self.context.add_history('define_modules_completed', {'module_count': len(module_specs)})
            self.context.set_state('idle')
            
            self.logger.info(f"Modules defined: {len(module_specs)} modules")
            return result
            
        except Exception as e:
            error_msg = f"Error defining modules: {str(e)}"
            self.logger.error(error_msg)
            self.context.set_state('error')
            self.context.add_history('define_modules_failed', {'error': str(e)})
            raise
    
    def validate_architecture(self, artifacts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate architecture artifacts.
        
        Args:
            artifacts: Dictionary containing:
                - architecture: Architecture definition
                - dependencies: Dependency map (optional)
                - schemas: Schema definitions (optional)
        
        Returns:
            Validation result dictionary:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str],
                "recommendations": List[str]
            }
        """
        self.logger.info("Validating architecture")
        self.context.set_state('validating')
        self.context.add_history('validation_started', {})
        
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        try:
            architecture = artifacts.get("architecture", {})
            dependencies = artifacts.get("dependencies", {})
            
            # Validate architecture structure
            if not architecture:
                result["errors"].append("No architecture definition provided")
                result["valid"] = False
            
            # Validate layers
            layers = architecture.get("layers", {})
            if not layers:
                result["warnings"].append("No layers defined in architecture")
            
            # Validate modules
            modules = architecture.get("modules", [])
            for module in modules:
                if not module.get("name"):
                    result["errors"].append("Module missing name")
                    result["valid"] = False
                if not module.get("layer"):
                    result["warnings"].append(f"Module {module.get('name')} missing layer assignment")
            
            # Validate dependencies
            if dependencies:
                # Check for circular dependencies
                cycles = self.dependency_mapper.detect_circular_dependencies()
                if cycles:
                    result["errors"].append(f"Circular dependencies detected: {cycles}")
                    result["valid"] = False
                
                # Validate layer dependencies
                is_valid, violations = self.dependency_mapper.validate_layer_dependencies()
                if not is_valid:
                    result["warnings"].extend(violations)
            
            # Generate recommendations
            if not result["errors"]:
                result["recommendations"].append("Architecture structure is valid")
            
            if not modules:
                result["recommendations"].append("Consider defining modules for better organization")
            
            self.context.add_history('validation_completed', {'valid': result["valid"]})
            self.context.set_state('idle')
            
            self.logger.info(f"Validation completed: {'Valid' if result['valid'] else 'Invalid'}")
            return result
            
        except Exception as e:
            error_msg = f"Error during validation: {str(e)}"
            self.logger.error(error_msg)
            result["errors"].append(error_msg)
            result["valid"] = False
            self.context.set_state('error')
            self.context.add_history('validation_failed', {'error': str(e)})
            return result
    
    def _generate_schemas_from_architecture(self, architecture: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate schemas based on architecture definition.
        
        Args:
            architecture: Architecture definition
        
        Returns:
            List of schema dictionaries
        """
        schemas = []
        
        # Generate API schemas for modules
        for module in architecture.get("modules", []):
            if module.get("public_api"):
                api_schema = self.schema_generator.generate_api_schema(
                    module["name"],
                    module["public_api"]
                )
                schemas.append({
                    "type": "api",
                    "name": module["name"],
                    "schema": api_schema
                })
        
        return schemas
    
    def _build_dependency_map(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build dependency map from architecture.
        
        Args:
            architecture: Architecture definition
        
        Returns:
            Dependency map dictionary
        """
        # Clear existing dependencies
        self.dependency_mapper = DependencyMapper()
        self.dependency_mapper.set_allowed_direction("agents", "core")
        self.dependency_mapper.set_allowed_direction("interfaces", "core")
        self.dependency_mapper.set_allowed_direction("interfaces", "agents")
        
        # Add module dependencies
        for module in architecture.get("modules", []):
            module_name = module.get("name")
            deps = module.get("dependencies", [])
            
            for dep in deps:
                self.dependency_mapper.add_dependency(module_name, dep)
        
        return self.dependency_mapper.to_json()
    
    def export_artifacts(self, design_result: Dict[str, Any], output_dir: str = "design") -> Dict[str, Any]:
        """
        Export design artifacts to files.
        
        Args:
            design_result: Result from design() method
            output_dir: Output directory (default: "design")
        
        Returns:
            Dictionary with exported file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported = {
            "directory": str(output_path),
            "files": []
        }
        
        architecture = design_result.get("architecture", {})
        
        # Export architecture.json
        arch_json_path = output_path / "architecture.json"
        with open(arch_json_path, 'w') as f:
            json.dump(architecture, f, indent=2)
        exported["files"].append(str(arch_json_path))
        
        # Export architecture.md
        arch_md_path = output_path / "architecture.md"
        arch_md = self.architecture_engine.architecture_to_markdown(architecture)
        with open(arch_md_path, 'w') as f:
            f.write(arch_md)
        exported["files"].append(str(arch_md_path))
        
        # Export standards.json
        standards_json_path = output_path / "standards.json"
        with open(standards_json_path, 'w') as f:
            f.write(self.standards.to_json())
        exported["files"].append(str(standards_json_path))
        
        # Export standards.md
        standards_md_path = output_path / "standards.md"
        with open(standards_md_path, 'w') as f:
            f.write(self.standards.to_markdown())
        exported["files"].append(str(standards_md_path))
        
        # Export dependencies.json
        dependencies_json_path = output_path / "dependencies.json"
        with open(dependencies_json_path, 'w') as f:
            json.dump(design_result.get("dependencies", {}), f, indent=2)
        exported["files"].append(str(dependencies_json_path))
        
        # Export schemas
        schemas = design_result.get("schemas", [])
        if schemas:
            schemas_json_path = output_path / "schemas.json"
            with open(schemas_json_path, 'w') as f:
                json.dump(schemas, f, indent=2)
            exported["files"].append(str(schemas_json_path))
        
        return exported
    
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
            "has_current_design": self.context.get_data('current_design') is not None
        }

