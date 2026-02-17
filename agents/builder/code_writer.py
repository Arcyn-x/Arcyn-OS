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

    def add_class(self, file_path: str, class_code: str, position: Optional[int] = None) -> Dict[str, Any]:
        """
        Add a class to an existing file.

        Args:
            file_path: Path to the file
            class_code: Complete class code (including class statement)
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

        # Check for duplicate class name
        import re
        class_match = re.search(r'class\s+(\w+)', class_code)
        if class_match:
            class_name = class_match.group(1)
            if re.search(rf'class\s+{class_name}\b', content):
                result["errors"].append(f"Class '{class_name}' already exists in {file_path}")
                return result

        # Insert class
        lines = content.split('\n')

        if position is None:
            lines.append('')
            lines.append('')
            lines.append(class_code)
        else:
            lines.insert(position, class_code)

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

    def add_import(self, file_path: str, import_statement: str) -> Dict[str, Any]:
        """
        Add an import statement to a file (idempotent — skips duplicates).

        The import is inserted after existing imports or at the top of the file.

        Args:
            file_path: Path to the file
            import_statement: Complete import statement (e.g., "from typing import Dict")

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

        import_line = import_statement.strip()

        # Check for duplicate import
        existing_lines = content.split('\n')
        for line in existing_lines:
            if line.strip() == import_line:
                result["success"] = True
                result["warnings"].append(f"Import already exists: {import_line}")
                return result

        # Find the last import line to insert after it
        last_import_idx = -1
        for i, line in enumerate(existing_lines):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                last_import_idx = i

        if last_import_idx >= 0:
            existing_lines.insert(last_import_idx + 1, import_line)
        else:
            # No imports found — insert after docstring or at top
            insert_at = 0
            in_docstring = False
            for i, line in enumerate(existing_lines):
                stripped = line.strip()
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    if in_docstring:
                        insert_at = i + 1
                        break
                    else:
                        # Single-line docstring
                        count = stripped.count('"""') + stripped.count("'''")
                        if count >= 2:
                            insert_at = i + 1
                            break
                        in_docstring = True
                elif in_docstring:
                    continue
                else:
                    insert_at = i
                    break

            existing_lines.insert(insert_at, import_line)

        new_content = '\n'.join(existing_lines)

        # Write back
        write_success, backup_path, write_error = self.file_manager.write_file(
            file_path, new_content, create_backup=True
        )

        if not write_success:
            result["errors"].append(write_error or "Failed to write file")
            return result

        result["success"] = True
        result["backup_path"] = backup_path
        return result

    def generate_from_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a Python file from a structured specification.

        Args:
            spec: Dictionary with file specification:
                {
                    "file_path": str,
                    "module_docstring": str,
                    "imports": List[str],
                    "classes": List[{
                        "name": str,
                        "docstring": str,
                        "bases": List[str],
                        "methods": List[{
                            "name": str,
                            "args": str,
                            "docstring": str,
                            "body": str
                        }]
                    }],
                    "functions": List[{
                        "name": str,
                        "args": str,
                        "return_type": str,
                        "docstring": str,
                        "body": str
                    }],
                    "overwrite": bool
                }

        Returns:
            Dictionary with result (same format as create_file)
        """
        file_path = spec.get("file_path", "")
        if not file_path:
            return {"success": False, "errors": ["file_path is required in spec"]}

        lines: List[str] = []

        # Module docstring
        docstring = spec.get("module_docstring", "")
        if docstring:
            lines.append(f'"""\n{docstring}\n"""')
            lines.append("")

        # Imports
        imports = spec.get("imports", [])
        for imp in imports:
            lines.append(imp)
        if imports:
            lines.append("")
            lines.append("")

        # Functions
        for func in spec.get("functions", []):
            name = func.get("name", "untitled")
            args = func.get("args", "")
            return_type = func.get("return_type", "")
            func_docstring = func.get("docstring", "")
            body = func.get("body", "pass")

            ret = f" -> {return_type}" if return_type else ""
            lines.append(f"def {name}({args}){ret}:")
            if func_docstring:
                lines.append(f'    """{func_docstring}"""')
            for body_line in body.split('\n'):
                lines.append(f"    {body_line}")
            lines.append("")
            lines.append("")

        # Classes
        for cls in spec.get("classes", []):
            cls_name = cls.get("name", "Untitled")
            bases = cls.get("bases", [])
            cls_docstring = cls.get("docstring", "")
            methods = cls.get("methods", [])

            bases_str = f"({', '.join(bases)})" if bases else ""
            lines.append(f"class {cls_name}{bases_str}:")
            if cls_docstring:
                lines.append(f'    """{cls_docstring}"""')
            lines.append("")

            if not methods:
                lines.append("    pass")
            else:
                for method in methods:
                    m_name = method.get("name", "method")
                    m_args = method.get("args", "self")
                    m_docstring = method.get("docstring", "")
                    m_body = method.get("body", "pass")

                    lines.append(f"    def {m_name}({m_args}):")
                    if m_docstring:
                        lines.append(f'        """{m_docstring}"""')
                    for body_line in m_body.split('\n'):
                        lines.append(f"        {body_line}")
                    lines.append("")

            lines.append("")

        content = '\n'.join(lines)
        overwrite = spec.get("overwrite", False)

        return self.create_file(file_path, content, overwrite=overwrite)
