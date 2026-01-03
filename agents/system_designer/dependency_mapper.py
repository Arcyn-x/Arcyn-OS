"""
Dependency Mapper module for System Designer Agent.

Builds dependency graphs, detects circular dependencies, and defines allowed dependency directions.
"""

from typing import Dict, List, Set, Any, Tuple
from collections import defaultdict, deque


class DependencyMapper:
    """
    Maps and validates system dependencies.
    
    Responsibilities:
    - Build dependency graphs
    - Detect circular dependencies
    - Define allowed dependency directions
    - Output DAG representation
    
    TODO: Add visualization export (Graphviz, Mermaid)
    TODO: Implement dependency impact analysis
    TODO: Add dependency version tracking
    TODO: Integrate with package managers
    """
    
    def __init__(self):
        """Initialize the dependency mapper."""
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.allowed_directions: Dict[str, List[str]] = {}
    
    def add_dependency(self, module: str, depends_on: str) -> None:
        """
        Add a dependency relationship.
        
        Args:
            module: Module that depends on another
            depends_on: Module that is depended upon
            
        Example:
            >>> mapper = DependencyMapper()
            >>> mapper.add_dependency("agents.builder", "core.memory")
        """
        self.dependencies[module].add(depends_on)
        self.reverse_dependencies[depends_on].add(module)
    
    def add_dependencies(self, dependencies: Dict[str, List[str]]) -> None:
        """
        Add multiple dependencies at once.
        
        Args:
            dependencies: Dictionary mapping modules to lists of dependencies
        """
        for module, deps in dependencies.items():
            for dep in deps:
                self.add_dependency(module, dep)
    
    def set_allowed_direction(self, from_layer: str, to_layer: str) -> None:
        """
        Define allowed dependency direction between layers.
        
        Args:
            from_layer: Source layer (e.g., "agents")
            to_layer: Target layer (e.g., "core")
            
        Example:
            >>> mapper.set_allowed_direction("agents", "core")
            >>> # Agents can depend on core, but not vice versa
        """
        if from_layer not in self.allowed_directions:
            self.allowed_directions[from_layer] = []
        self.allowed_directions[from_layer].append(to_layer)
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Detect circular dependencies in the graph.
        
        Returns:
            List of cycles (each cycle is a list of module names)
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
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
            
            for neighbor in self.dependencies.get(node, set()):
                dfs(neighbor)
            
            rec_stack.remove(node)
            path.pop()
        
        for module in self.dependencies:
            if module not in visited:
                dfs(module)
        
        return cycles
    
    def get_dependency_graph(self) -> Dict[str, Any]:
        """
        Get the complete dependency graph as a dictionary.
        
        Returns:
            Dictionary with nodes, edges, and metadata
        """
        nodes = set(self.dependencies.keys()) | set(self.reverse_dependencies.keys())
        
        edges = []
        for module, deps in self.dependencies.items():
            for dep in deps:
                edges.append({
                    "from": module,
                    "to": dep,
                    "type": "depends_on"
                })
        
        return {
            "nodes": list(nodes),
            "edges": edges,
            "metadata": {
                "total_modules": len(nodes),
                "total_dependencies": len(edges),
                "has_circular_dependencies": len(self.detect_circular_dependencies()) > 0
            }
        }
    
    def get_topological_order(self) -> List[List[str]]:
        """
        Get modules in topological order (dependency order).
        
        Returns:
            List of lists, where each inner list contains modules that can be processed in parallel
        """
        # Calculate in-degrees
        in_degree: Dict[str, int] = defaultdict(int)
        all_modules = set(self.dependencies.keys()) | set(self.reverse_dependencies.keys())
        
        for module in all_modules:
            in_degree[module] = len(self.reverse_dependencies.get(module, set()))
        
        # Kahn's algorithm
        queue = deque([module for module in all_modules if in_degree[module] == 0])
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
                
                # Reduce in-degree for dependents
                for dependent in self.dependencies.get(module, set()):
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
    
    def validate_layer_dependencies(self) -> Tuple[bool, List[str]]:
        """
        Validate that dependencies follow allowed layer directions.
        
        Returns:
            Tuple of (is_valid: bool, violations: List[str])
        """
        violations = []
        
        for module, deps in self.dependencies.items():
            module_layer = self._extract_layer(module)
            
            for dep in deps:
                dep_layer = self._extract_layer(dep)
                
                # Check if this direction is allowed
                allowed_targets = self.allowed_directions.get(module_layer, [])
                
                if module_layer != dep_layer and dep_layer not in allowed_targets:
                    violations.append(
                        f"Violation: {module} ({module_layer}) depends on {dep} ({dep_layer})"
                    )
        
        return len(violations) == 0, violations
    
    def _extract_layer(self, module_path: str) -> str:
        """
        Extract layer name from module path.
        
        Args:
            module_path: Module path (e.g., "core.memory", "agents.builder")
            
        Returns:
            Layer name (e.g., "core", "agents")
        """
        parts = module_path.split('.')
        return parts[0] if parts else "unknown"
    
    def to_json(self) -> Dict[str, Any]:
        """
        Export dependency graph as JSON.
        
        Returns:
            JSON-serializable dictionary
        """
        graph = self.get_dependency_graph()
        cycles = self.detect_circular_dependencies()
        is_valid, violations = self.validate_layer_dependencies()
        
        return {
            **graph,
            "circular_dependencies": cycles,
            "layer_validation": {
                "valid": is_valid,
                "violations": violations
            },
            "topological_order": self.get_topological_order()
        }
    
    def get_dependents(self, module: str) -> Set[str]:
        """
        Get all modules that depend on the given module.
        
        Args:
            module: Module name
            
        Returns:
            Set of dependent module names
        """
        return self.reverse_dependencies.get(module, set()).copy()
    
    def get_dependencies(self, module: str) -> Set[str]:
        """
        Get all modules that the given module depends on.
        
        Args:
            module: Module name
            
        Returns:
            Set of dependency module names
        """
        return self.dependencies.get(module, set()).copy()

