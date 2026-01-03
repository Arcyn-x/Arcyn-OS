"""
Code Writer module for Builder Agent.

Handles file creation, module scaffolding, and boilerplate generation.
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from .file_manager import FileManager
from .validator import Validator


class CodeWriter:
    """
    Writes new code files with proper structure.
    
    Rules:
    - Never overwrite existing files
    - Must request confirmation through warnings if conflicts exist
    - Generates docstrings and type hints by default
    
    TODO: Add template system for common patterns
    TODO: Integrate with LLM for intelligent code generation
    TODO: Add code style configuration (PEP 8, black, etc.)
    TODO: Implement code generation from specifications
    """
    
    def __init__(self, file_manager: Optional[FileManager] = None, validator: Optional[Validator] = None):
        """
        Initialize the code writer.
        
        Args:
            file_manager: FileManager instance (creates new if None)
            validator: Validator instance (creates new if None)
        """
        self.file_manager = file_manager or FileManager()
        self.validator = validator or Validator()
    
    def create_file(self, file_path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        Create a new file with content.
        
        Args:
            file_path: Path where file should be created
            content: Content to write
            overwrite: Whether to overwrite if file exists
            
        Returns:
            Dictionary with result:
            {
                "success": bool,
                "file_path": str,
                "warnings": List[str],
                "errors": List[str],
                "backup_path": str or None
            }
        """
        result = {
            "success": False,
            "file_path": file_path,
            "warnings": [],
            "errors": [],
            "backup_path": None
        }
        
        # Check if file exists
        if self.file_manager.file_exists(file_path):
            if not overwrite:
                result["errors"].append(f"File already exists: {file_path}")
                result["warnings"].append("Use overwrite=True to replace existing file")
                return result
            else:
                result["warnings"].append(f"Overwriting existing file: {file_path}")
        
        # Validate path
        path_valid, path_error = self.file_manager.validate_path(file_path, must_exist=False)
        if not path_valid:
            result["errors"].append(path_error or "Invalid file path")
            return result
        
        # Write file
        write_success, backup_path, write_error = self.file_manager.write_file(
            file_path, content, create_backup=overwrite
        )
        
        if not write_success:
            result["errors"].append(write_error or "Failed to write file")
            return result
        
        result["success"] = True
        result["backup_path"] = backup_path
        
        # Validate the created file
        validation = self.validator.validate_file(file_path)
        if not validation["overall_valid"]:
            result["warnings"].extend(validation.get("syntax_errors", []))
            result["warnings"].extend(validation.get("structure_warnings", []))
            result["warnings"].extend(validation.get("import_errors", []))
        
        return result
    
    def scaffold_module(self, module_path: str, module_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a Python module with basic structure.
        
        Args:
            module_path: Path to the module file (e.g., "core/memory.py")
            module_name: Optional module name (extracted from path if not provided)
            
        Returns:
            Dictionary with result (same format as create_file)
        """
        if module_name is None:
            module_name = Path(module_path).stem
        
        # Generate module content
        content = self._generate_module_boilerplate(module_name)
        
        return self.create_file(module_path, content)
    
    def scaffold_package(self, package_path: str, package_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a Python package with __init__.py.
        
        Args:
            package_path: Path to the package directory (e.g., "agents/builder")
            package_name: Optional package name (extracted from path if not provided)
            
        Returns:
            Dictionary with results for all created files
        """
        if package_name is None:
            package_name = Path(package_path).name
        
        results = {
            "success": False,
            "package_path": package_path,
            "files_created": [],
            "warnings": [],
            "errors": []
        }
        
        # Create __init__.py
        init_path = str(Path(package_path) / "__init__.py")
        init_content = self._generate_package_init(package_name)
        
        init_result = self.create_file(init_path, init_content)
        results["files_created"].append(init_result)
        
        if init_result["success"]:
            results["success"] = True
        else:
            results["errors"].extend(init_result["errors"])
            results["warnings"].extend(init_result["warnings"])
        
        return results
    
    def _generate_module_boilerplate(self, module_name: str) -> str:
        """
        Generate boilerplate code for a Python module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Generated module content
        """
        # Convert module_name to class name (PascalCase)
        class_name = ''.join(word.capitalize() for word in module_name.split('_'))
        
        content = f'''"""
{module_name} module.

TODO: Add module description
"""

from typing import Any, Optional


class {class_name}:
    """
    {class_name} class.
    
    TODO: Add class description
    """
    
    def __init__(self):
        """
        Initialize {class_name}.
        """
        pass
    
    # TODO: Add methods
'''
        return content
    
    def _generate_package_init(self, package_name: str) -> str:
        """
        Generate __init__.py content for a package.
        
        Args:
            package_name: Name of the package
            
        Returns:
            Generated __init__.py content
        """
        content = f'''"""
{package_name} package.

TODO: Add package description
"""

# TODO: Add exports
__all__ = []
'''
        return content
    
    def add_function(self, file_path: str, function_code: str, position: Optional[int] = None) -> Dict[str, Any]:
        """
        Add a function to an existing file.
        
        Args:
            file_path: Path to the file
            function_code: Complete function code (including def statement)
            position: Optional line number to insert at (appends at end if None)
            
        Returns:
            Dictionary with result
        """
        result = {
            "success": False,
            "file_path": file_path,
            "warnings": [],
            "errors": []
        }
        
        # Read existing file
        read_success, content, read_error = self.file_manager.read_file(file_path)
        if not read_success:
            result["errors"].append(read_error or "Failed to read file")
            return result
        
        # Insert function
        lines = content.split('\n')
        
        if position is None:
            # Append at end
            lines.append('')
            lines.append(function_code)
        else:
            # Insert at specified position
            lines.insert(position, function_code)
        
        new_content = '\n'.join(lines)
        
        # Write back
        write_success, backup_path, write_error = self.file_manager.write_file(
            file_path, new_content, create_backup=True
        )
        
        if not write_success:
            result["errors"].append(write_error or "Failed to write file")
            return result
        
        result["success"] = True
        result["backup_path"] = backup_path
        
        # Validate
        validation = self.validator.validate_file(file_path)
        if not validation["overall_valid"]:
            result["warnings"].extend(validation.get("syntax_errors", []))
            result["warnings"].extend(validation.get("structure_warnings", []))
        
        return result

