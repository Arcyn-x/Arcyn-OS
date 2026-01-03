"""
Architect Agent (A-1) for Arcyn OS.

The Architect Agent is the "brain" of Arcyn OS. It takes high-level goals and
turns them into structured development plans with tasks, dependencies, and milestones.
"""

from typing import Dict, Any, Optional
from .planner import Planner
from .task_graph import TaskGraph
from .evaluator import Evaluator
from core.logger import Logger
from core.context_manager import ContextManager
from core.memory import Memory


class ArchitectAgent:
    """
    Main Architect Agent class.
    
    The Architect Agent does not write code — it plans the code, organizes modules,
    and defines build sequences. It outputs clear JSON that other agents can consume.
    
    Example:
        >>> agent = ArchitectAgent(agent_id="architect_001")
        >>> plan = agent.plan("Build a REST API for user management")
        >>> breakdown = agent.breakdown("Implement authentication")
        >>> progress = {"task_statuses": {"task_1": "completed"}}
        >>> evaluation = agent.evaluate(progress)
    """
    
    def __init__(self, agent_id: str = "architect_agent", log_level: int = 20):
        """
        Initialize the Architect Agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            log_level: Logging level (default: 20 = INFO)
        """
        self.agent_id = agent_id
        self.logger = Logger(f"ArchitectAgent-{agent_id}", log_level=log_level)
        self.context = ContextManager(agent_id)
        self.memory = Memory()
        
        # Initialize sub-components
        self.planner = Planner()
        self.task_graph = TaskGraph()
        self.evaluator = Evaluator()
        
        self.logger.info(f"Architect Agent {agent_id} initialized")
        self.context.set_state('idle')
    
    def plan(self, goal: str) -> Dict[str, Any]:
        """
        Take a high-level goal and turn it into a structured development plan.
        
        Args:
            goal: High-level goal description (e.g., "Build a REST API")
            
        Returns:
            Dictionary containing:
            {
                "goal": "...",
                "milestones": [...],
                "tasks": [...],
                "task_graph": {...},
                "metadata": {...}
            }
            
        Example:
            >>> agent = ArchitectAgent()
            >>> result = agent.plan("Create a web application")
            >>> "goal" in result
            True
            >>> "milestones" in result
            True
            >>> "tasks" in result
            True
        """
        self.logger.info(f"Planning for goal: {goal}")
        self.context.set_state('planning')
        self.context.add_history('plan_started', {'goal': goal})
        
        try:
            # Generate plan using planner
            plan = self.planner.plan(goal)
            
            # Build task graph from plan
            self.task_graph.from_plan(plan)
            task_graph_json = self.task_graph.to_json()
            
            # Store plan in memory
            plan_key = f"plan_{self.agent_id}_{self.context.get_context()['created_at']}"
            self.memory.write(plan_key, plan)
            
            # Assemble final response
            result = {
                "goal": plan["goal"],
                "milestones": plan["milestones"],
                "tasks": plan["tasks"],
                "task_graph": task_graph_json,
                "metadata": {
                    **plan.get("metadata", {}),
                    "plan_id": plan_key,
                    "execution_order": task_graph_json["execution_order"]
                }
            }
            
            self.context.set_data('current_plan', result)
            self.context.add_history('plan_completed', {'plan_id': plan_key})
            self.context.set_state('idle')
            
            self.logger.info(f"Plan generated successfully: {len(plan['tasks'])} tasks, {len(plan['milestones'])} milestones")
            return result
            
        except Exception as e:
            self.logger.error(f"Error during planning: {str(e)}")
            self.context.set_state('error')
            self.context.add_history('plan_failed', {'error': str(e)})
            raise
    
    def breakdown(self, task: str) -> Dict[str, Any]:
        """
        Break down a task into subtasks with dependencies.
        
        Args:
            task: Task description to break down
            
        Returns:
            Dictionary containing:
            {
                "task": "...",
                "subtasks": [...],
                "dependencies": [...],
                "estimated_effort": "..."
            }
            
        Example:
            >>> agent = ArchitectAgent()
            >>> breakdown = agent.breakdown("Implement user authentication")
            >>> "subtasks" in breakdown
            True
        """
        self.logger.info(f"Breaking down task: {task}")
        self.context.set_state('planning')
        self.context.add_history('breakdown_started', {'task': task})
        
        try:
            # Use planner to create a mini-plan for this task
            mini_plan = self.planner.plan(task)
            
            # Extract subtasks
            subtasks = mini_plan.get('tasks', [])
            
            # Create a temporary task graph for this breakdown
            temp_graph = TaskGraph()
            for subtask in subtasks:
                temp_graph.add_task(subtask)
            
            # Build dependencies (simplified - tasks in order depend on previous)
            for i in range(1, len(subtasks)):
                temp_graph.add_dependency(subtasks[i]['id'], subtasks[i-1]['id'])
            
            # Get dependencies structure
            dependencies = []
            for subtask in subtasks:
                deps = temp_graph.get_dependencies(subtask['id'])
                if deps:
                    dependencies.append({
                        "task_id": subtask['id'],
                        "depends_on": list(deps)
                    })
            
            result = {
                "task": task,
                "subtasks": subtasks,
                "dependencies": dependencies,
                "estimated_effort": mini_plan.get('metadata', {}).get('estimated_complexity', 'medium'),
                "execution_order": temp_graph.get_execution_order()
            }
            
            self.context.add_history('breakdown_completed', {'task': task, 'subtask_count': len(subtasks)})
            self.context.set_state('idle')
            
            self.logger.info(f"Task broken down into {len(subtasks)} subtasks")
            return result
            
        except Exception as e:
            self.logger.error(f"Error during task breakdown: {str(e)}")
            self.context.set_state('error')
            self.context.add_history('breakdown_failed', {'error': str(e)})
            raise
    
    def evaluate(self, progress: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate progress based on the task graph.
        
        Args:
            progress: Progress dictionary with task statuses.
                      Expected format:
                      {
                          "task_statuses": {
                              "task_1": "completed",
                              "task_2": "in_progress",
                              "task_3": "pending"
                          }
                      }
            
        Returns:
            Dictionary containing:
            {
                "overall_score": float,
                "milestone_scores": {...},
                "bottlenecks": [...],
                "recommendations": [...],
                "summary": {...}
            }
            
        Example:
            >>> agent = ArchitectAgent()
            >>> # First create a plan
            >>> plan = agent.plan("Build an API")
            >>> # Then evaluate progress
            >>> progress = {"task_statuses": {"task_1": "completed"}}
            >>> evaluation = agent.evaluate(progress)
            >>> "overall_score" in evaluation
            True
        """
        self.logger.info("Evaluating progress")
        self.context.set_state('evaluating')
        self.context.add_history('evaluation_started', {'progress': progress})
        
        try:
            # Ensure we have a task graph (from previous plan)
            if not self.task_graph.nodes:
                raise ValueError("No task graph available. Call plan() first.")
            
            # Perform evaluation
            evaluation = self.evaluator.evaluate(progress, self.task_graph)
            
            # Get progress summary
            summary = self.evaluator.get_progress_summary(progress, self.task_graph)
            
            # Check milestone completions
            milestone_completions = {}
            current_plan = self.context.get_data('current_plan')
            if current_plan:
                for milestone in current_plan.get('milestones', []):
                    milestone_id = milestone.get('id')
                    if milestone_id:
                        completion = self.evaluator.check_milestone_completion(
                            milestone_id, progress, self.task_graph
                        )
                        milestone_completions[milestone_id] = completion
            
            result = {
                **evaluation,
                "summary": summary,
                "milestone_completions": milestone_completions
            }
            
            # Store evaluation in memory
            eval_key = f"evaluation_{self.agent_id}_{evaluation['timestamp']}"
            self.memory.write(eval_key, result)
            
            self.context.set_data('last_evaluation', result)
            self.context.add_history('evaluation_completed', {'overall_score': evaluation['overall_score']})
            self.context.set_state('idle')
            
            self.logger.info(f"Evaluation completed. Overall score: {evaluation['overall_score']:.2%}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error during evaluation: {str(e)}")
            self.context.set_state('error')
            self.context.add_history('evaluation_failed', {'error': str(e)})
            raise
    
    def get_current_plan(self) -> Optional[Dict[str, Any]]:
        """
        Get the current plan from context.
        
        Returns:
            Current plan dictionary or None if no plan exists
        """
        return self.context.get_data('current_plan')
    
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
            "has_plan": self.context.get_data('current_plan') is not None,
            "has_evaluation": self.context.get_data('last_evaluation') is not None
        }

