"""
Validator module for Builder Agent.

Runs basic sanity checks: syntax validation, structural validation, and required files existence.
This is NOT a test runner — just safety checks.
"""

import ast
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional


class Validator:
    """
    Validates code and file structure for safety.
    
    TODO: Add type checking integration
    TODO: Implement AST-based complexity analysis
    TODO: Add dependency validation
    TODO: Integrate with linters (pylint, flake8, etc.)
    """
    
    def __init__(self):
        """Initialize the validator."""
        pass
    
    def validate_syntax(self, file_path: str, content: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Validate Python syntax.
        
        Args:
            file_path: Path to the Python file
            content: Optional file content (if None, reads from file)
            
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        
        try:
            if content is None:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            # Try to parse the AST
            ast.parse(content, filename=file_path)
            
            return True, []
            
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            if e.text:
                errors.append(f"  {e.text.strip()}")
            return False, errors
            
        except Exception as e:
            errors.append(f"Error validating syntax: {str(e)}")
            return False, errors
    
    def validate_structure(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Validate basic file structure (imports, basic structure).
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Tuple of (is_valid: bool, warnings: List[str])
        """
        warnings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content, filename=file_path)
            
            # Check for basic structure
            has_imports = any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(tree))
            has_functions = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
            has_classes = any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
            
            # Basic validation - file should have some structure
            if not (has_imports or has_functions or has_classes):
                warnings.append("File appears to be empty or has no structure")
            
            # Check for docstrings in classes and functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    if not ast.get_docstring(node):
                        warnings.append(f"Missing docstring in {node.name}")
            
            return True, warnings
            
        except SyntaxError:
            # Syntax errors are handled by validate_syntax
            return False, ["File has syntax errors - cannot validate structure"]
        except Exception as e:
            return False, [f"Error validating structure: {str(e)}"]
    
    def validate_required_files(self, base_path: str, required_files: List[str]) -> Tuple[bool, List[str]]:
        """
        Check if required files exist.
        
        Args:
            base_path: Base directory path
            required_files: List of required file paths (relative to base_path)
            
        Returns:
            Tuple of (all_exist: bool, missing_files: List[str])
        """
        base = Path(base_path)
        missing = []
        
        for file_path in required_files:
            full_path = base / file_path
            if not full_path.exists():
                missing.append(str(file_path))
        
        return len(missing) == 0, missing
    
    def validate_imports(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Validate that imports can be resolved (basic check).
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Tuple of (all_valid: bool, errors: List[str])
        """
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=file_path)
            
            # Extract import statements
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Basic check - just verify it's a valid module name
                        module_name = alias.name
                        if not module_name.replace('.', '').replace('_', '').isalnum():
                            errors.append(f"Invalid import name: {module_name}")
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module
                    if module and not module.replace('.', '').replace('_', '').isalnum():
                        errors.append(f"Invalid import from: {module}")
            
            # TODO: Actually try to resolve imports (requires proper Python environment)
            
            return len(errors) == 0, errors
            
        except SyntaxError:
            return False, ["File has syntax errors - cannot validate imports"]
        except Exception as e:
            return False, [f"Error validating imports: {str(e)}"]
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Run all validations on a file.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "file_path": file_path,
            "syntax_valid": False,
            "structure_valid": False,
            "syntax_errors": [],
            "structure_warnings": [],
            "import_errors": []
        }
        
        # Syntax validation
        syntax_valid, syntax_errors = self.validate_syntax(file_path)
        results["syntax_valid"] = syntax_valid
        results["syntax_errors"] = syntax_errors
        
        # Structure validation (only if syntax is valid)
        if syntax_valid:
            structure_valid, structure_warnings = self.validate_structure(file_path)
            results["structure_valid"] = structure_valid
            results["structure_warnings"] = structure_warnings
            
            # Import validation
            imports_valid, import_errors = self.validate_imports(file_path)
            results["import_errors"] = import_errors
        
        results["overall_valid"] = (
            results["syntax_valid"] and
            results["structure_valid"] and
            len(results["import_errors"]) == 0
        )
        
        return results

