"""
Dependency Checker module for Integrator Agent.

Validates dependency graphs, detects circular dependencies, and enforces allowed
dependency directions.
"""

from typing import Dict, Any, List, Tuple, Set
from collections import defaultdict, deque


class DependencyChecker:
    """
    Validates dependencies and enforces system boundaries.
    
    Responsibilities:
    - Validate dependency graphs
    - Detect circular dependencies
    - Enforce allowed dependency directions
    - Ensure new modules do not violate system boundaries
    
    Output: Dependency DAG, violations list
    
    TODO: Add visualization export
    TODO: Implement dependency impact analysis
    TODO: Add version compatibility checking
    TODO: Integrate with package dependency tracking
    """
    
    def __init__(self):
        """Initialize the dependency checker."""
        self.allowed_directions = {
            "agents": ["core"],
            "interfaces": ["core", "agents"],
            "design": []
        }
    
    def detect_circular_dependencies(self, dependencies: Dict[str, List[str]]) -> List[List[str]]:
        """
        Detect circular dependencies in a dependency graph.
        
        Args:
            dependencies: Dictionary mapping modules to lists of dependencies
        
        Returns:
            List of cycles (each cycle is a list of module names)
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        # Build graph
        graph = defaultdict(set)
        for module, deps in dependencies.items():
            for dep in deps:
                graph[module].add(dep)
        
        def dfs(node: str) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, set()):
                dfs(neighbor)
            
            rec_stack.remove(node)
            path.pop()
        
        for module in dependencies:
            if module not in visited:
                dfs(module)
        
        return cycles
    
    def validate_layer_dependencies(self, module: str, dependencies: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate that a module's dependencies follow allowed layer directions.
        
        Args:
            module: Module name (e.g., "agents.builder")
            dependencies: List of dependency module names
        
        Returns:
            Tuple of (is_valid: bool, violations: List[str])
        """
        violations = []
        module_layer = self._extract_layer(module)
        
        for dep in dependencies:
            dep_layer = self._extract_layer(dep)
            
            # Check if this direction is allowed
            allowed_targets = self.allowed_directions.get(module_layer, [])
            
            if module_layer != dep_layer and dep_layer not in allowed_targets:
                violations.append(
                    f"Violation: {module} ({module_layer}) depends on {dep} ({dep_layer}). "
                    f"Allowed directions from {module_layer}: {allowed_targets}"
                )
        
        return len(violations) == 0, violations
    
    def validate_dependency_graph(self, dependencies: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Validate a complete dependency graph.
        
        Args:
            dependencies: Dictionary mapping modules to lists of dependencies
        
        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "circular_dependencies": [],
            "layer_violations": [],
            "missing_dependencies": [],
            "warnings": []
        }
        
        # Check for circular dependencies
        cycles = self.detect_circular_dependencies(dependencies)
        if cycles:
            result["valid"] = False
            result["circular_dependencies"] = cycles
        
        # Check layer violations
        all_violations = []
        for module, deps in dependencies.items():
            is_valid, violations = self.validate_layer_dependencies(module, deps)
            if not is_valid:
                result["valid"] = False
                all_violations.extend(violations)
        
        result["layer_violations"] = all_violations
        
        # Check for missing dependencies (dependencies that don't exist)
        all_modules = set(dependencies.keys())
        all_deps = set()
        for deps in dependencies.values():
            all_deps.update(deps)
        
        missing = all_deps - all_modules
        if missing:
            result["warnings"].append(f"Referenced dependencies that are not defined: {missing}")
            result["missing_dependencies"] = list(missing)
        
        return result
    
    def check_new_module_dependencies(self, new_module: str, new_dependencies: List[str], 
                                     existing_dependencies: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Check if adding a new module would violate dependency rules.
        
        Args:
            new_module: Name of the new module
            new_dependencies: Dependencies of the new module
            existing_dependencies: Existing dependency graph
        
        Returns:
            Validation result dictionary
        """
        # Create temporary graph with new module
        temp_dependencies = existing_dependencies.copy()
        temp_dependencies[new_module] = new_dependencies
        
        # Validate the temporary graph
        result = self.validate_dependency_graph(temp_dependencies)
        result["module"] = new_module
        result["new_dependencies"] = new_dependencies
        
        return result
    
    def get_topological_order(self, dependencies: Dict[str, List[str]]) -> List[List[str]]:
        """
        Get modules in topological order (dependency order).
        
        Args:
            dependencies: Dependency graph
        
        Returns:
            List of lists, where each inner list contains modules that can be processed in parallel
        """
        # Build reverse dependencies
        reverse_deps = defaultdict(set)
        all_modules = set(dependencies.keys())
        
        for module, deps in dependencies.items():
            all_modules.add(module)
            for dep in deps:
                all_modules.add(dep)
                reverse_deps[module].add(dep)
        
        # Calculate in-degrees
        in_degree = {module: 0 for module in all_modules}
        for module, deps in dependencies.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] = in_degree.get(dep, 0) + 1
        
        # Kahn's algorithm
        queue = deque([module for module, degree in in_degree.items() if degree == 0])
        result = []
        processed = set()
        
        while queue:
            current_level = []
            level_size = len(queue)
            
            for _ in range(level_size):
                module = queue.popleft()
                if module in processed:
                    continue
                
                current_level.append(module)
                processed.add(module)
                
                # Reduce in-degree for modules that depend on this one
                for dependent in dependencies.get(module, []):
                    if dependent in in_degree:
                        in_degree[dependent] -= 1
                        if in_degree[dependent] == 0 and dependent not in processed:
                            queue.append(dependent)
            
            if current_level:
                result.append(current_level)
        
        # Check for cycles
        if len(processed) < len(all_modules):
            unprocessed = all_modules - processed
            raise ValueError(f"Circular dependencies detected. Unprocessed modules: {unprocessed}")
        
        return result
    
    def _extract_layer(self, module_path: str) -> str:
        """
        Extract layer name from module path.
        
        Args:
            module_path: Module path (e.g., "core.memory", "agents.builder")
        
        Returns:
            Layer name (e.g., "core", "agents")
        """
        parts = module_path.split('.')
        if len(parts) > 0:
            return parts[0]
        return "unknown"
    
    def validate_architecture_dependencies(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate dependencies from an architecture definition.
        
        Args:
            architecture: Architecture dictionary from System Designer Agent
        
        Returns:
            Validation result dictionary
        """
        # Extract dependencies from modules
        dependencies = {}
        modules = architecture.get("modules", [])
        
        for module in modules:
            module_name = module.get("name")
            module_deps = module.get("dependencies", [])
            if module_name:
                dependencies[module_name] = module_deps
        
        # Validate
        return self.validate_dependency_graph(dependencies)

