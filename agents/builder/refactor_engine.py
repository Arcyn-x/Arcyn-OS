"""
Refactor Engine module for Builder Agent.

Handles function-level refactors, module reorganization, and cleanup operations.
"""

import ast
import re
from typing import Dict, Any, List, Optional, Tuple
from .file_manager import FileManager
from .validator import Validator


class RefactorEngine:
    """
    Performs code refactoring operations.
    
    Rules:
    - No logic changes without explicit instruction
    - Preserve public interfaces
    - Explain diffs in plain English
    
    TODO: Add AST-based refactoring capabilities
    TODO: Implement rename operations (functions, classes, variables)
    TODO: Add code formatting and style fixes
    TODO: Integrate with LLM for intelligent refactoring suggestions
    """
    
    def __init__(self, file_manager: Optional[FileManager] = None, validator: Optional[Validator] = None):
        """
        Initialize the refactor engine.
        
        Args:
            file_manager: FileManager instance (creates new if None)
            validator: Validator instance (creates new if None)
        """
        self.file_manager = file_manager or FileManager()
        self.validator = validator or Validator()
    
    def refactor_file(self, file_path: str, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply multiple refactoring operations to a file.
        
        Args:
            file_path: Path to the file to refactor
            operations: List of operation dictionaries, each with 'type' and 'params'
            
        Returns:
            Dictionary with result:
            {
                "success": bool,
                "file_path": str,
                "changes": List[str],  # Plain English descriptions
                "warnings": List[str],
                "errors": List[str],
                "backup_path": str or None
            }
        """
        result = {
            "success": False,
            "file_path": file_path,
            "changes": [],
            "warnings": [],
            "errors": [],
            "backup_path": None
        }
        
        # Read file
        read_success, content, read_error = self.file_manager.read_file(file_path)
        if not read_success:
            result["errors"].append(read_error or "Failed to read file")
            return result
        
        original_content = content
        
        # Apply operations
        for operation in operations:
            op_type = operation.get('type')
            op_params = operation.get('params', {})
            
            if op_type == 'rename_function':
                content, change_desc = self._rename_function(content, op_params)
                result["changes"].append(change_desc)
            elif op_type == 'rename_class':
                content, change_desc = self._rename_class(content, op_params)
                result["changes"].append(change_desc)
            elif op_type == 'add_docstring':
                content, change_desc = self._add_docstring(content, op_params)
                result["changes"].append(change_desc)
            elif op_type == 'format_code':
                content, change_desc = self._format_code(content)
                result["changes"].append(change_desc)
            else:
                result["warnings"].append(f"Unknown operation type: {op_type}")
        
        # Only write if content changed
        if content != original_content:
            write_success, backup_path, write_error = self.file_manager.write_file(
                file_path, content, create_backup=True
            )
            
            if not write_success:
                result["errors"].append(write_error or "Failed to write file")
                return result
            
            result["success"] = True
            result["backup_path"] = backup_path
            
            # Validate
            validation = self.validator.validate_file(file_path)
            if not validation["overall_valid"]:
                result["errors"].extend(validation.get("syntax_errors", []))
                result["warnings"].extend(validation.get("structure_warnings", []))
        else:
            result["warnings"].append("No changes made to file")
        
        return result
    
    def _rename_function(self, content: str, params: Dict[str, Any]) -> Tuple[str, str]:
        """
        Rename a function in the content.
        
        Args:
            content: File content
            params: Must contain 'old_name' and 'new_name'
            
        Returns:
            Tuple of (new_content, change_description)
        """
        old_name = params.get('old_name')
        new_name = params.get('new_name')
        
        if not old_name or not new_name:
            return content, "Skipped rename_function: missing old_name or new_name"
        
        # Simple regex-based replacement (def function_name)
        pattern = rf'\bdef\s+{re.escape(old_name)}\s*\('
        replacement = f'def {new_name}('
        
        new_content = re.sub(pattern, replacement, content)
        
        # Also replace function calls (simple approach)
        # TODO: Use AST for more accurate replacement
        new_content = re.sub(rf'\b{re.escape(old_name)}\s*\(', f'{new_name}(', new_content)
        
        change_desc = f"Renamed function '{old_name}' to '{new_name}'"
        return new_content, change_desc
    
    def _rename_class(self, content: str, params: Dict[str, Any]) -> Tuple[str, str]:
        """
        Rename a class in the content.
        
        Args:
            content: File content
            params: Must contain 'old_name' and 'new_name'
            
        Returns:
            Tuple of (new_content, change_description)
        """
        old_name = params.get('old_name')
        new_name = params.get('new_name')
        
        if not old_name or not new_name:
            return content, "Skipped rename_class: missing old_name or new_name"
        
        # Replace class definition
        pattern = rf'\bclass\s+{re.escape(old_name)}\s*[\(:]'
        replacement = f'class {new_name}('
        
        new_content = re.sub(pattern, replacement, content)
        
        # Also replace class instantiations
        # TODO: Use AST for more accurate replacement
        new_content = re.sub(rf'\b{re.escape(old_name)}\s*\(', f'{new_name}(', new_content)
        
        change_desc = f"Renamed class '{old_name}' to '{new_name}'"
        return new_content, change_desc
    
    def _add_docstring(self, content: str, params: Dict[str, Any]) -> Tuple[str, str]:
        """
        Add a docstring to a function or class.
        
        Args:
            content: File content
            params: Must contain 'target' (function/class name) and 'docstring'
            
        Returns:
            Tuple of (new_content, change_description)
        """
        target = params.get('target')
        docstring = params.get('docstring', '')
        target_type = params.get('target_type', 'function')  # 'function' or 'class'
        
        if not target:
            return content, "Skipped add_docstring: missing target"
        
        # Simple approach: find the definition and add docstring
        # TODO: Use AST for more accurate insertion
        if target_type == 'function':
            pattern = rf'(\s+def\s+{re.escape(target)}\s*\([^)]*\)\s*:)'
            replacement = rf'\1\n        """{docstring}"""'
        else:  # class
            pattern = rf'(\s+class\s+{re.escape(target)}\s*[\(:])'
            replacement = rf'\1\n    """{docstring}"""'
        
        new_content = re.sub(pattern, replacement, content)
        
        change_desc = f"Added docstring to {target_type} '{target}'"
        return new_content, change_desc
    
    def _format_code(self, content: str) -> Tuple[str, str]:
        """
        Basic code formatting (indentation, spacing).
        
        Args:
            content: File content
            
        Returns:
            Tuple of (new_content, change_description)
        """
        # TODO: Integrate with black, autopep8, or similar
        # For now, just normalize line endings
        new_content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        change_desc = "Normalized line endings"
        return new_content, change_desc
    
    def extract_public_interface(self, file_path: str) -> Dict[str, Any]:
        """
        Extract the public interface (classes, functions) from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with public interface information
        """
        result = {
            "file_path": file_path,
            "classes": [],
            "functions": [],
            "errors": []
        }
        
        read_success, content, read_error = self.file_manager.read_file(file_path)
        if not read_success:
            result["errors"].append(read_error or "Failed to read file")
            return result
        
        try:
            tree = ast.parse(content, filename=file_path)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's public (not starting with _)
                    if not node.name.startswith('_'):
                        result["classes"].append({
                            "name": node.name,
                            "line": node.lineno,
                            "docstring": ast.get_docstring(node)
                        })
                
                elif isinstance(node, ast.FunctionDef):
                    # Check if it's at module level and public
                    if not node.name.startswith('_'):
                        result["functions"].append({
                            "name": node.name,
                            "line": node.lineno,
                            "docstring": ast.get_docstring(node)
                        })
        
        except SyntaxError as e:
            result["errors"].append(f"Syntax error: {str(e)}")
        except Exception as e:
            result["errors"].append(f"Error parsing file: {str(e)}")
        
        return result

