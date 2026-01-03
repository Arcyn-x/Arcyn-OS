"""
Task Graph module for Architect Agent.

Manages task dependencies and creates execution order (DAG).
"""

from typing import Dict, List, Set, Any, Optional
from collections import deque, defaultdict


class TaskGraph:
    """
    Manages task dependencies as a Directed Acyclic Graph (DAG).
    
    TODO: Add cycle detection and prevention
    TODO: Implement parallel execution optimization
    TODO: Add task prioritization algorithms
    TODO: Implement dynamic dependency resolution
    """
    
    def __init__(self):
        """Initialize the task graph."""
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: Dict[str, Set[str]] = defaultdict(set)  # task_id -> set of dependent task_ids
        self.reverse_edges: Dict[str, Set[str]] = defaultdict(set)  # task_id -> set of prerequisite task_ids
    
    def add_task(self, task: Dict[str, Any]) -> None:
        """
        Add a task node to the graph.
        
        Args:
            task: Task dictionary with at least 'id' field
            
        Example:
            >>> graph = TaskGraph()
            >>> graph.add_task({"id": "task_1", "name": "Setup"})
        """
        task_id = task.get('id')
        if not task_id:
            raise ValueError("Task must have an 'id' field")
        
        self.nodes[task_id] = task.copy()
        
        # Initialize empty dependency sets if not present
        if task_id not in self.edges:
            self.edges[task_id] = set()
        if task_id not in self.reverse_edges:
            self.reverse_edges[task_id] = set()
    
    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """
        Add a dependency: task_id depends on depends_on.
        
        Args:
            task_id: Task that depends on another task
            depends_on: Task that must be completed first
            
        Example:
            >>> graph = TaskGraph()
            >>> graph.add_task({"id": "task_1"})
            >>> graph.add_task({"id": "task_2"})
            >>> graph.add_dependency("task_2", "task_1")  # task_2 depends on task_1
        """
        if task_id not in self.nodes:
            raise ValueError(f"Task {task_id} not found in graph")
        if depends_on not in self.nodes:
            raise ValueError(f"Dependency {depends_on} not found in graph")
        
        # Add edge: depends_on -> task_id (depends_on must complete before task_id)
        self.edges[depends_on].add(task_id)
        self.reverse_edges[task_id].add(depends_on)
    
    def add_dependencies(self, task_id: str, dependencies: List[str]) -> None:
        """
        Add multiple dependencies for a task.
        
        Args:
            task_id: Task that depends on others
            dependencies: List of task IDs that must be completed first
        """
        for dep in dependencies:
            self.add_dependency(task_id, dep)
    
    def get_dependencies(self, task_id: str) -> Set[str]:
        """
        Get all tasks that a task depends on.
        
        Args:
            task_id: Task ID
            
        Returns:
            Set of task IDs that must be completed before this task
        """
        return self.reverse_edges.get(task_id, set()).copy()
    
    def get_dependents(self, task_id: str) -> Set[str]:
        """
        Get all tasks that depend on this task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Set of task IDs that depend on this task
        """
        return self.edges.get(task_id, set()).copy()
    
    def get_execution_order(self) -> List[List[str]]:
        """
        Get tasks in execution order using topological sort.
        Returns list of task ID lists, where each inner list can be executed in parallel.
        
        Returns:
            List of lists, where each inner list contains task IDs that can run in parallel
            
        Example:
            >>> graph = TaskGraph()
            >>> graph.add_task({"id": "task_1"})
            >>> graph.add_task({"id": "task_2"})
            >>> graph.add_task({"id": "task_3"})
            >>> graph.add_dependency("task_2", "task_1")
            >>> graph.add_dependency("task_3", "task_1")
            >>> order = graph.get_execution_order()
            >>> order[0] == ["task_1"]
            True
            >>> set(order[1]) == {"task_2", "task_3"}
            True
        """
        # Calculate in-degrees
        in_degree: Dict[str, int] = {task_id: 0 for task_id in self.nodes}
        for task_id in self.nodes:
            in_degree[task_id] = len(self.reverse_edges[task_id])
        
        # Find all tasks with no dependencies (in-degree = 0)
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
        execution_order: List[List[str]] = []
        processed = set()
        
        while queue:
            # Current level: all tasks that can be executed in parallel
            current_level = []
            level_size = len(queue)
            
            for _ in range(level_size):
                task_id = queue.popleft()
                if task_id in processed:
                    continue
                
                current_level.append(task_id)
                processed.add(task_id)
                
                # Reduce in-degree for dependent tasks
                for dependent in self.edges[task_id]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0 and dependent not in processed:
                        queue.append(dependent)
            
            if current_level:
                execution_order.append(current_level)
        
        # Check for cycles (if there are unprocessed nodes)
        if len(processed) < len(self.nodes):
            unprocessed = set(self.nodes.keys()) - processed
            raise ValueError(f"Cycle detected in task graph. Unprocessed tasks: {unprocessed}")
        
        return execution_order
    
    def get_ready_tasks(self, completed_tasks: Set[str]) -> List[str]:
        """
        Get tasks that are ready to execute (all dependencies completed).
        
        Args:
            completed_tasks: Set of completed task IDs
            
        Returns:
            List of task IDs ready to execute
        """
        ready = []
        for task_id in self.nodes:
            if task_id in completed_tasks:
                continue
            
            dependencies = self.get_dependencies(task_id)
            if dependencies.issubset(completed_tasks):
                ready.append(task_id)
        
        return ready
    
    def to_json(self) -> Dict[str, Any]:
        """
        Convert task graph to JSON representation.
        
        Returns:
            Dictionary containing nodes, edges, and metadata
        """
        return {
            "nodes": list(self.nodes.values()),
            "edges": [
                {"from": source, "to": target}
                for source, targets in self.edges.items()
                for target in targets
            ],
            "execution_order": self.get_execution_order(),
            "metadata": {
                "total_tasks": len(self.nodes),
                "total_dependencies": sum(len(deps) for deps in self.reverse_edges.values()),
                "max_parallel_levels": len(self.get_execution_order())
            }
        }
    
    def from_plan(self, plan: Dict[str, Any]) -> None:
        """
        Build task graph from a plan structure.
        
        Args:
            plan: Plan dictionary with 'tasks' and 'milestones' keys
            
        Example:
            >>> graph = TaskGraph()
            >>> plan = {
            ...     "tasks": [
            ...         {"id": "task_1", "milestone_id": "milestone_1"},
            ...         {"id": "task_2", "milestone_id": "milestone_2"}
            ...     ],
            ...     "milestones": [
            ...         {"id": "milestone_1", "order": 1},
            ...         {"id": "milestone_2", "order": 2}
            ...     ]
            ... }
            >>> graph.from_plan(plan)
        """
        # Add all tasks
        for task in plan.get('tasks', []):
            self.add_task(task)
        
        # Create dependencies based on milestone order
        milestones = sorted(plan.get('milestones', []), key=lambda m: m.get('order', 0))
        milestone_to_tasks: Dict[str, List[str]] = defaultdict(list)
        
        for task in plan.get('tasks', []):
            milestone_id = task.get('milestone_id')
            if milestone_id:
                milestone_to_tasks[milestone_id].append(task['id'])
        
        # Tasks in earlier milestones depend on tasks in later milestones
        # (Actually, tasks in later milestones depend on earlier ones)
        for i in range(len(milestones) - 1):
            current_milestone = milestones[i]
            next_milestone = milestones[i + 1]
            
            current_tasks = milestone_to_tasks.get(current_milestone['id'], [])
            next_tasks = milestone_to_tasks.get(next_milestone['id'], [])
            
            # All tasks in next milestone depend on all tasks in current milestone
            for next_task in next_tasks:
                for current_task in current_tasks:
                    self.add_dependency(next_task, current_task)
        
        # TODO: Add intelligent dependency detection based on task names/descriptions
        # TODO: Use LLM to detect implicit dependencies

