"""
Refactor Engine module for Builder Agent.

Handles function-level refactors, module reorganization, and cleanup operations.
Uses Python AST for safe, accurate code transformations.
"""

import ast
import re
import textwrap
from typing import Dict, Any, List, Optional, Tuple
from .file_manager import FileManager
from .validator import Validator


class RefactorEngine:
    """
    Performs code refactoring operations using AST analysis.

    Rules:
    - No logic changes without explicit instruction
    - Preserve public interfaces
    - Explain diffs in plain English

    Capabilities:
    - rename_function / rename_class (regex-based, call-site aware)
    - add_docstring (AST-aware insertion)
    - format_code (line ending normalization)
    - extract_function (move code block into new function)
    - move_function (relocate function definition)
    - extract_public_interface (AST analysis)
    - extract_functions (full function metadata)
    - extract_imports (import analysis)
    - analyze_complexity (cyclomatic complexity scoring)
    - remove_unused_imports (dead import detection)
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
            elif op_type == 'extract_function':
                content, change_desc = self._extract_function(content, op_params)
                result["changes"].append(change_desc)
            elif op_type == 'move_function':
                content, change_desc = self._move_function(content, op_params)
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

    # ─── Refactor Operations ────────────────────────────────────

    def _rename_function(self, content: str, params: Dict[str, Any]) -> Tuple[str, str]:
        """Rename a function in the content (definition + call sites)."""
        old_name = params.get('old_name')
        new_name = params.get('new_name')

        if not old_name or not new_name:
            return content, "Skipped rename_function: missing old_name or new_name"

        pattern = rf'\bdef\s+{re.escape(old_name)}\s*\('
        replacement = f'def {new_name}('
        new_content = re.sub(pattern, replacement, content)

        # Also replace call sites
        new_content = re.sub(rf'\b{re.escape(old_name)}\s*\(', f'{new_name}(', new_content)

        return new_content, f"Renamed function '{old_name}' to '{new_name}'"

    def _rename_class(self, content: str, params: Dict[str, Any]) -> Tuple[str, str]:
        """Rename a class in the content (definition + instantiations)."""
        old_name = params.get('old_name')
        new_name = params.get('new_name')

        if not old_name or not new_name:
            return content, "Skipped rename_class: missing old_name or new_name"

        pattern = rf'\bclass\s+{re.escape(old_name)}\s*[\(:]'
        replacement = f'class {new_name}('
        new_content = re.sub(pattern, replacement, content)

        new_content = re.sub(rf'\b{re.escape(old_name)}\s*\(', f'{new_name}(', new_content)

        return new_content, f"Renamed class '{old_name}' to '{new_name}'"

    def _add_docstring(self, content: str, params: Dict[str, Any]) -> Tuple[str, str]:
        """Add a docstring to a function or class."""
        target = params.get('target')
        docstring = params.get('docstring', '')
        target_type = params.get('target_type', 'function')

        if not target:
            return content, "Skipped add_docstring: missing target"

        if target_type == 'function':
            pattern = rf'(\s+def\s+{re.escape(target)}\s*\([^)]*\)\s*:)'
            replacement = rf'\1\n        """{docstring}"""'
        else:
            pattern = rf'(\s+class\s+{re.escape(target)}\s*[\(:])'
            replacement = rf'\1\n    """{docstring}"""'

        new_content = re.sub(pattern, replacement, content)
        return new_content, f"Added docstring to {target_type} '{target}'"

    def _format_code(self, content: str) -> Tuple[str, str]:
        """Basic code formatting (normalize line endings, trailing whitespace)."""
        new_content = content.replace('\r\n', '\n').replace('\r', '\n')
        # Strip trailing whitespace per line
        lines = new_content.split('\n')
        new_content = '\n'.join(line.rstrip() for line in lines)
        return new_content, "Normalized line endings and stripped trailing whitespace"

    def _extract_function(self, content: str, params: Dict[str, Any]) -> Tuple[str, str]:
        """
        Extract a code block into a new function.

        params:
            start_line: First line of code to extract (1-indexed)
            end_line: Last line of code to extract (1-indexed)
            function_name: Name for the new function
        """
        start_line = params.get('start_line')
        end_line = params.get('end_line')
        function_name = params.get('function_name')

        if not all([start_line, end_line, function_name]):
            return content, "Skipped extract_function: need start_line, end_line, function_name"

        lines = content.split('\n')
        if start_line < 1 or end_line > len(lines):
            return content, f"Skipped extract_function: line range out of bounds"

        # Extract the block
        extracted = lines[start_line - 1:end_line]
        if not extracted:
            return content, "Skipped extract_function: empty block"

        # Determine indentation of extracted code
        min_indent = float('inf')
        for line in extracted:
            if line.strip():
                min_indent = min(min_indent, len(line) - len(line.lstrip()))
        if min_indent == float('inf'):
            min_indent = 0

        # Build new function
        body_lines = []
        for line in extracted:
            if line.strip():
                body_lines.append('    ' + line[min_indent:])
            else:
                body_lines.append('')

        new_func = f"def {function_name}():\n" + '\n'.join(body_lines)

        # Replace extracted block with function call
        indent = ' ' * min_indent
        new_lines = (
            lines[:start_line - 1]
            + [f"{indent}{function_name}()"]
            + lines[end_line:]
        )

        # Append new function at end
        new_lines.append('')
        new_lines.append('')
        new_lines.append(new_func)

        return '\n'.join(new_lines), f"Extracted lines {start_line}-{end_line} into function '{function_name}'"

    def _move_function(self, content: str, params: Dict[str, Any]) -> Tuple[str, str]:
        """
        Move a function to a different position in the file.

        params:
            function_name: Name of the function to move
            position: 'top' (after imports) or 'bottom' (end of file)
        """
        function_name = params.get('function_name')
        position = params.get('position', 'bottom')

        if not function_name:
            return content, "Skipped move_function: missing function_name"

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return content, "Skipped move_function: syntax error in file"

        # Find the function
        func_node = None
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                func_node = node
                break

        if not func_node:
            return content, f"Skipped move_function: function '{function_name}' not found"

        lines = content.split('\n')
        start = func_node.lineno - 1
        end = func_node.end_lineno if hasattr(func_node, 'end_lineno') and func_node.end_lineno else start + 1

        # Extract the function code
        func_lines = lines[start:end]
        remaining = lines[:start] + lines[end:]

        if position == 'top':
            # Insert after imports
            insert_at = 0
            for i, line in enumerate(remaining):
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    insert_at = i + 1
            remaining.insert(insert_at, '')
            for j, fl in enumerate(func_lines):
                remaining.insert(insert_at + 1 + j, fl)
            remaining.insert(insert_at + 1 + len(func_lines), '')
        else:
            remaining.append('')
            remaining.append('')
            remaining.extend(func_lines)

        return '\n'.join(remaining), f"Moved function '{function_name}' to {position}"

    # ─── AST Analysis ───────────────────────────────────────────

    def extract_public_interface(self, file_path: str) -> Dict[str, Any]:
        """Extract the public interface (classes, functions) from a file using AST."""
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

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    if not node.name.startswith('_'):
                        methods = []
                        for item in node.body:
                            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                if not item.name.startswith('_') or item.name in ('__init__', '__str__', '__repr__'):
                                    methods.append(item.name)
                        result["classes"].append({
                            "name": node.name,
                            "line": node.lineno,
                            "docstring": ast.get_docstring(node),
                            "methods": methods,
                            "bases": [self._get_name(b) for b in node.bases]
                        })

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith('_'):
                        result["functions"].append({
                            "name": node.name,
                            "line": node.lineno,
                            "docstring": ast.get_docstring(node),
                            "args": [a.arg for a in node.args.args],
                            "is_async": isinstance(node, ast.AsyncFunctionDef)
                        })

        except SyntaxError as e:
            result["errors"].append(f"Syntax error: {str(e)}")
        except Exception as e:
            result["errors"].append(f"Error parsing file: {str(e)}")

        return result

    def extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract all function definitions with full metadata from source code.

        Args:
            content: Python source code

        Returns:
            List of function metadata dictionaries
        """
        functions = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return functions

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Extract argument info
                args = []
                defaults_offset = len(node.args.args) - len(node.args.defaults)
                for i, arg in enumerate(node.args.args):
                    arg_info: Dict[str, Any] = {"name": arg.arg}
                    if arg.annotation:
                        arg_info["type"] = self._get_annotation(arg.annotation)
                    default_idx = i - defaults_offset
                    if default_idx >= 0:
                        arg_info["has_default"] = True
                    args.append(arg_info)

                # Return type
                return_type = None
                if node.returns:
                    return_type = self._get_annotation(node.returns)

                # Decorators
                decorators = []
                for dec in node.decorator_list:
                    decorators.append(self._get_name(dec))

                end_line = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno

                functions.append({
                    "name": node.name,
                    "start_line": node.lineno,
                    "end_line": end_line,
                    "args": args,
                    "return_type": return_type,
                    "decorators": decorators,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "docstring": ast.get_docstring(node),
                    "line_count": end_line - node.lineno + 1
                })

        return functions

    def extract_imports(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract all import statements with metadata.

        Args:
            content: Python source code

        Returns:
            List of import metadata dictionaries
        """
        imports = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return imports

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "type": "import",
                        "module": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno,
                        "names": [alias.asname or alias.name]
                    })
            elif isinstance(node, ast.ImportFrom):
                names = [alias.asname or alias.name for alias in node.names]
                imports.append({
                    "type": "from",
                    "module": node.module or "",
                    "names": names,
                    "line": node.lineno,
                    "level": node.level  # relative import depth
                })

        return imports

    def analyze_complexity(self, content: str) -> Dict[str, Any]:
        """
        Analyze cyclomatic complexity of functions.

        Counts branches (if, elif, for, while, except, with, and, or, assert)
        to compute per-function complexity scores.

        Args:
            content: Python source code

        Returns:
            Dictionary with complexity scores and overall metrics
        """
        result: Dict[str, Any] = {
            "functions": [],
            "overall_complexity": 0,
            "max_complexity": 0,
            "hotspots": []  # functions with complexity > 10
        }

        try:
            tree = ast.parse(content)
        except SyntaxError:
            result["error"] = "Syntax error in source"
            return result

        # Walk only top-level and class-level functions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = 1  # base complexity

                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.IfExp)):
                        complexity += 1
                    elif isinstance(child, ast.For):
                        complexity += 1
                    elif isinstance(child, ast.While):
                        complexity += 1
                    elif isinstance(child, ast.ExceptHandler):
                        complexity += 1
                    elif isinstance(child, ast.With):
                        complexity += 1
                    elif isinstance(child, ast.Assert):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        # Each 'and'/'or' adds a branch
                        complexity += len(child.values) - 1

                end_line = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
                func_data = {
                    "name": node.name,
                    "complexity": complexity,
                    "line": node.lineno,
                    "line_count": end_line - node.lineno + 1,
                    "rating": "low" if complexity <= 5 else ("medium" if complexity <= 10 else "high")
                }
                result["functions"].append(func_data)

                if complexity > 10:
                    result["hotspots"].append(func_data)

        total = sum(f["complexity"] for f in result["functions"])
        result["overall_complexity"] = total
        result["max_complexity"] = max(
            (f["complexity"] for f in result["functions"]), default=0
        )
        result["function_count"] = len(result["functions"])

        return result

    def remove_unused_imports(self, content: str) -> Tuple[str, List[str]]:
        """
        Detect and remove unused imports from Python source code.

        Args:
            content: Python source code

        Returns:
            Tuple of (cleaned_content, list_of_removed_imports)
        """
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return content, []

        # Collect all imported names
        imported_names: Dict[str, int] = {}  # name -> line number
        import_lines: Dict[int, ast.stmt] = {}  # line -> import node

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    imported_names[name] = node.lineno
                    import_lines[node.lineno] = node
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    if name == '*':
                        continue  # don't touch star imports
                    imported_names[name] = node.lineno
                    import_lines[node.lineno] = node

        if not imported_names:
            return content, []

        # Collect all names used in the code (excluding import nodes)
        used_names: set = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Get the root of attribute access chains
                cur = node
                while isinstance(cur, ast.Attribute):
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    used_names.add(cur.id)

        # Find unused imports
        unused = {}
        for name, line in imported_names.items():
            if name not in used_names:
                unused[name] = line

        if not unused:
            return content, []

        # Build lines to remove
        lines_to_remove: set = set()
        removed_descriptions: List[str] = []

        for name, line in unused.items():
            node = import_lines.get(line)
            if node is None:
                continue

            if isinstance(node, ast.Import):
                if len(node.names) == 1:
                    lines_to_remove.add(line)
                    removed_descriptions.append(f"import {node.names[0].name}")
            elif isinstance(node, ast.ImportFrom):
                if len(node.names) == 1:
                    lines_to_remove.add(line)
                    removed_descriptions.append(f"from {node.module} import {name}")
                # For multi-name imports, we'd need more complex editing
                # (skip for safety — only remove single-name import lines)

        if not lines_to_remove:
            return content, []

        # Remove identified lines
        source_lines = content.split('\n')
        new_lines = []
        for i, line in enumerate(source_lines, 1):
            if i not in lines_to_remove:
                new_lines.append(line)

        return '\n'.join(new_lines), removed_descriptions

    # ─── Helpers ────────────────────────────────────────────────

    def _get_name(self, node: ast.expr) -> str:
        """Extract a human-readable name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return "<unknown>"

    def _get_annotation(self, node: ast.expr) -> str:
        """Extract annotation string from an AST annotation node."""
        if isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_annotation(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            base = self._get_annotation(node.value)
            if isinstance(node.slice, ast.Tuple):
                args = ", ".join(self._get_annotation(elt) for elt in node.slice.elts)
            else:
                args = self._get_annotation(node.slice)
            return f"{base}[{args}]"
        return "Any"
