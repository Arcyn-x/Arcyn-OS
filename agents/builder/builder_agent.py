"""
Builder Agent (F-1) for Arcyn OS.

The Builder Agent is responsible for writing, modifying, and refactoring code,
but ONLY when instructed by the Architect Agent.

It must be safe, auditable, modular, and fully controlled.
"""

from typing import Dict, Any, List, Optional
from .code_writer import CodeWriter
from .refactor_engine import RefactorEngine
from .file_manager import FileManager
from .validator import Validator
from core.logger import Logger
from core.context_manager import ContextManager
from core.memory import Memory


class BuilderAgent:
    """
    Main Builder Agent class.
    
    The Builder Agent does not plan and does not decide priorities.
    It only executes tasks provided by the Architect Agent.
    
    Example:
        >>> agent = BuilderAgent(agent_id="builder_001")
        >>> task = {
        ...     "action": "build",
        ...     "description": "Create a new module",
        ...     "target_path": "core/test_module.py",
        ...     "content": "# Test module"
        ... }
        >>> result = agent.build(task)
    """
    
    def __init__(self, agent_id: str = "builder_agent", log_level: int = 20):
        """
        Initialize the Builder Agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            log_level: Logging level (default: 20 = INFO)
        """
        self.agent_id = agent_id
        self.logger = Logger(f"BuilderAgent-{agent_id}", log_level=log_level)
        self.context = ContextManager(agent_id)
        self.memory = Memory()
        
        # Initialize sub-components
        self.file_manager = FileManager()
        self.validator = Validator()
        self.code_writer = CodeWriter(self.file_manager, self.validator)
        self.refactor_engine = RefactorEngine(self.file_manager, self.validator)
        
        self.logger.info(f"Builder Agent {agent_id} initialized")
        self.context.set_state('idle')
    
    def build(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build new code files and modules.
        
        Args:
            task: Task dictionary with:
                - action: "build"
                - description: Task description
                - target_path: Path where file should be created
                - content: File content (optional, will generate if missing)
                - constraints: List of constraints (optional)
                - overwrite: Whether to overwrite existing files (default: False)
        
        Returns:
            Dictionary with result:
            {
                "action": "build",
                "files_changed": List[str],
                "summary": str,
                "warnings": List[str],
                "next_steps": List[str]
            }
        """
        self.logger.info(f"Building: {task.get('description', 'Unknown task')}")
        self.context.set_state('building')
        self.context.add_history('build_started', {'task': task})
        
        result = {
            "action": "build",
            "files_changed": [],
            "summary": "",
            "warnings": [],
            "next_steps": []
        }
        
        try:
            target_path = task.get('target_path')
            if not target_path:
                result["warnings"].append("No target_path specified")
                result["summary"] = "Build task failed: missing target_path"
                self.context.set_state('error')
                return result
            
            content = task.get('content')
            overwrite = task.get('overwrite', False)
            
            # Generate content if not provided
            if not content:
                # Determine if it's a module or package
                if target_path.endswith('__init__.py') or target_path.endswith('/__init__.py'):
                    # It's a package
                    package_path = str(target_path).replace('__init__.py', '').rstrip('/')
                    package_result = self.code_writer.scaffold_package(package_path)
                    if package_result["success"]:
                        result["files_changed"].extend([f["file_path"] for f in package_result["files_created"] if f.get("success")])
                    result["warnings"].extend(package_result.get("warnings", []))
                else:
                    # It's a module
                    module_result = self.code_writer.scaffold_module(target_path)
                    if module_result["success"]:
                        result["files_changed"].append(target_path)
                    result["warnings"].extend(module_result.get("warnings", []))
            else:
                # Use provided content
                write_result = self.code_writer.create_file(target_path, content, overwrite=overwrite)
                if write_result["success"]:
                    result["files_changed"].append(target_path)
                else:
                    result["warnings"].extend(write_result.get("errors", []))
                result["warnings"].extend(write_result.get("warnings", []))
            
            # Generate summary
            if result["files_changed"]:
                result["summary"] = f"Successfully created {len(result['files_changed'])} file(s)"
                result["next_steps"].append("Validate created files")
                result["next_steps"].append("Review generated code")
            else:
                result["summary"] = "No files were created"
            
            self.context.add_history('build_completed', {'files_changed': result["files_changed"]})
            self.context.set_state('idle')
            
            self.logger.info(f"Build completed: {result['summary']}")
            return result
            
        except Exception as e:
            error_msg = f"Error during build: {str(e)}"
            self.logger.error(error_msg)
            result["warnings"].append(error_msg)
            result["summary"] = f"Build task failed: {str(e)}"
            self.context.set_state('error')
            self.context.add_history('build_failed', {'error': str(e)})
            return result
    
    def modify(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Modify existing files.
        
        Args:
            task: Task dictionary with:
                - action: "modify"
                - description: Task description
                - target_path: Path to file to modify
                - modifications: List of modification operations
                    Each operation can be:
                    - type: "replace", "insert", "append"
                    - params: Operation-specific parameters
        
        Returns:
            Dictionary with result (same format as build)
        """
        self.logger.info(f"Modifying: {task.get('description', 'Unknown task')}")
        self.context.set_state('modifying')
        self.context.add_history('modify_started', {'task': task})
        
        result = {
            "action": "modify",
            "files_changed": [],
            "summary": "",
            "warnings": [],
            "next_steps": []
        }
        
        try:
            target_path = task.get('target_path')
            if not target_path:
                result["warnings"].append("No target_path specified")
                result["summary"] = "Modify task failed: missing target_path"
                self.context.set_state('error')
                return result
            
            # Check if file exists
            if not self.file_manager.file_exists(target_path):
                result["warnings"].append(f"File does not exist: {target_path}")
                result["summary"] = f"Modify task failed: file not found"
                self.context.set_state('error')
                return result
            
            # Read file
            read_success, content, read_error = self.file_manager.read_file(target_path)
            if not read_success:
                result["warnings"].append(read_error or "Failed to read file")
                result["summary"] = "Modify task failed: could not read file"
                self.context.set_state('error')
                return result
            
            # Apply modifications
            modifications = task.get('modifications', [])
            changes_made = []
            
            for mod in modifications:
                mod_type = mod.get('type')
                mod_params = mod.get('params', {})
                
                if mod_type == 'replace':
                    # Replace text
                    old_text = mod_params.get('old_text')
                    new_text = mod_params.get('new_text')
                    if old_text in content:
                        content = content.replace(old_text, new_text)
                        changes_made.append(f"Replaced text in {target_path}")
                
                elif mod_type == 'insert':
                    # Insert at line
                    line_num = mod_params.get('line', 0)
                    insert_text = mod_params.get('text', '')
                    lines = content.split('\n')
                    lines.insert(line_num, insert_text)
                    content = '\n'.join(lines)
                    changes_made.append(f"Inserted text at line {line_num} in {target_path}")
                
                elif mod_type == 'append':
                    # Append to end
                    append_text = mod_params.get('text', '')
                    content += '\n' + append_text
                    changes_made.append(f"Appended text to {target_path}")
            
            # Write modified content
            if changes_made:
                write_success, backup_path, write_error = self.file_manager.write_file(
                    target_path, content, create_backup=True
                )
                
                if write_success:
                    result["files_changed"].append(target_path)
                    result["summary"] = f"Successfully modified {target_path} ({len(changes_made)} changes)"
                    result["next_steps"].append("Review changes")
                    result["next_steps"].append("Validate modified file")
                else:
                    result["warnings"].append(write_error or "Failed to write file")
                    result["summary"] = "Modify task failed: could not write file"
            else:
                result["warnings"].append("No modifications were applied")
                result["summary"] = "No changes made to file"
            
            # Validate
            validation = self.validator.validate_file(target_path)
            if not validation["overall_valid"]:
                result["warnings"].extend(validation.get("syntax_errors", []))
                result["warnings"].extend(validation.get("structure_warnings", []))
            
            self.context.add_history('modify_completed', {'files_changed': result["files_changed"]})
            self.context.set_state('idle')
            
            self.logger.info(f"Modify completed: {result['summary']}")
            return result
            
        except Exception as e:
            error_msg = f"Error during modify: {str(e)}"
            self.logger.error(error_msg)
            result["warnings"].append(error_msg)
            result["summary"] = f"Modify task failed: {str(e)}"
            self.context.set_state('error')
            self.context.add_history('modify_failed', {'error': str(e)})
            return result
    
    def refactor(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refactor existing code.
        
        Args:
            task: Task dictionary with:
                - action: "refactor"
                - description: Task description
                - target_path: Path to file to refactor
                - operations: List of refactoring operations
                    Each operation has 'type' and 'params'
        
        Returns:
            Dictionary with result (same format as build)
        """
        self.logger.info(f"Refactoring: {task.get('description', 'Unknown task')}")
        self.context.set_state('refactoring')
        self.context.add_history('refactor_started', {'task': task})
        
        result = {
            "action": "refactor",
            "files_changed": [],
            "summary": "",
            "warnings": [],
            "next_steps": []
        }
        
        try:
            target_path = task.get('target_path')
            if not target_path:
                result["warnings"].append("No target_path specified")
                result["summary"] = "Refactor task failed: missing target_path"
                self.context.set_state('error')
                return result
            
            # Check if file exists
            if not self.file_manager.file_exists(target_path):
                result["warnings"].append(f"File does not exist: {target_path}")
                result["summary"] = f"Refactor task failed: file not found"
                self.context.set_state('error')
                return result
            
            # Perform refactoring
            operations = task.get('operations', [])
            refactor_result = self.refactor_engine.refactor_file(target_path, operations)
            
            if refactor_result["success"]:
                result["files_changed"].append(target_path)
                result["summary"] = f"Successfully refactored {target_path}"
                result["warnings"].extend(refactor_result.get("warnings", []))
                result["next_steps"].append("Review refactored code")
                result["next_steps"].append("Run tests to verify functionality")
            else:
                result["warnings"].extend(refactor_result.get("errors", []))
                result["summary"] = "Refactor task failed"
            
            # Add change descriptions
            if refactor_result.get("changes"):
                result["summary"] += f" ({len(refactor_result['changes'])} changes)"
            
            self.context.add_history('refactor_completed', {'files_changed': result["files_changed"]})
            self.context.set_state('idle')
            
            self.logger.info(f"Refactor completed: {result['summary']}")
            return result
            
        except Exception as e:
            error_msg = f"Error during refactor: {str(e)}"
            self.logger.error(error_msg)
            result["warnings"].append(error_msg)
            result["summary"] = f"Refactor task failed: {str(e)}"
            self.context.set_state('error')
            self.context.add_history('refactor_failed', {'error': str(e)})
            return result
    
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
            "has_recent_activity": len(self.context.get_history(limit=1)) > 0
        }

