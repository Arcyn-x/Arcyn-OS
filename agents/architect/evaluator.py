"""
Evaluator module for Architect Agent.

Evaluates progress, checks milestone completion, detects bottlenecks, and recommends next steps.
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime


class Evaluator:
    """
    Evaluates progress and provides recommendations.
    
    TODO: Add machine learning for bottleneck prediction
    TODO: Implement historical progress analysis
    TODO: Add risk assessment and mitigation recommendations
    TODO: Integrate with external metrics and monitoring
    """
    
    def __init__(self):
        """Initialize the evaluator."""
        self.evaluation_history: List[Dict[str, Any]] = []
    
    def evaluate(self, progress: Dict[str, Any], task_graph: Any) -> Dict[str, Any]:
        """
        Evaluate overall progress.
        
        Args:
            progress: Progress dictionary with task statuses
            task_graph: TaskGraph instance
            
        Returns:
            Dictionary containing:
            {
                "overall_score": float,
                "milestone_scores": {...},
                "bottlenecks": [...],
                "recommendations": [...]
            }
        """
        # Calculate overall progress score
        overall_score = self._calculate_overall_score(progress, task_graph)
        
        # Calculate milestone scores
        milestone_scores = self._calculate_milestone_scores(progress, task_graph)
        
        # Detect bottlenecks
        bottlenecks = self._detect_bottlenecks(progress, task_graph)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(progress, task_graph, bottlenecks)
        
        evaluation = {
            "overall_score": overall_score,
            "milestone_scores": milestone_scores,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
        
        self.evaluation_history.append(evaluation)
        return evaluation
    
    def _calculate_overall_score(self, progress: Dict[str, Any], task_graph: Any) -> float:
        """
        Calculate overall progress score (0.0 to 1.0).
        
        Args:
            progress: Progress dictionary
            task_graph: TaskGraph instance
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not task_graph.nodes:
            return 0.0
        
        total_tasks = len(task_graph.nodes)
        if total_tasks == 0:
            return 0.0
        
        completed_tasks = 0
        in_progress_tasks = 0
        
        task_statuses = progress.get('task_statuses', {})
        
        for task_id in task_graph.nodes:
            status = task_statuses.get(task_id, 'pending')
            if status == 'completed':
                completed_tasks += 1
            elif status == 'in_progress':
                in_progress_tasks += 0.5  # Count as half-complete
        
        # Score = (completed + 0.5 * in_progress) / total
        score = (completed_tasks + in_progress_tasks) / total_tasks
        return min(1.0, max(0.0, score))
    
    def _calculate_milestone_scores(self, progress: Dict[str, Any], task_graph: Any) -> Dict[str, float]:
        """
        Calculate progress score for each milestone.
        
        Args:
            progress: Progress dictionary
            task_graph: TaskGraph instance
            
        Returns:
            Dictionary mapping milestone_id to score (0.0 to 1.0)
        """
        milestone_scores: Dict[str, float] = {}
        task_statuses = progress.get('task_statuses', {})
        
        # Group tasks by milestone
        milestone_tasks: Dict[str, List[str]] = {}
        for task_id, task in task_graph.nodes.items():
            milestone_id = task.get('milestone_id')
            if milestone_id:
                if milestone_id not in milestone_tasks:
                    milestone_tasks[milestone_id] = []
                milestone_tasks[milestone_id].append(task_id)
        
        # Calculate score for each milestone
        for milestone_id, task_ids in milestone_tasks.items():
            if not task_ids:
                milestone_scores[milestone_id] = 0.0
                continue
            
            completed = sum(1 for tid in task_ids if task_statuses.get(tid) == 'completed')
            in_progress = sum(1 for tid in task_ids if task_statuses.get(tid) == 'in_progress')
            
            score = (completed + in_progress * 0.5) / len(task_ids)
            milestone_scores[milestone_id] = min(1.0, max(0.0, score))
        
        return milestone_scores
    
    def _detect_bottlenecks(self, progress: Dict[str, Any], task_graph: Any) -> List[Dict[str, Any]]:
        """
        Detect bottlenecks in the task graph.
        
        Args:
            progress: Progress dictionary
            task_graph: TaskGraph instance
            
        Returns:
            List of bottleneck dictionaries
        """
        bottlenecks = []
        task_statuses = progress.get('task_statuses', {})
        
        # Find tasks that are blocking many other tasks
        for task_id, task in task_graph.nodes.items():
            status = task_statuses.get(task_id, 'pending')
            
            # Check if task is blocking (not completed but has many dependents)
            dependents = task_graph.get_dependents(task_id)
            if status != 'completed' and len(dependents) > 2:
                bottlenecks.append({
                    "task_id": task_id,
                    "task_name": task.get('name', task_id),
                    "type": "blocking",
                    "severity": "high" if len(dependents) > 5 else "medium",
                    "blocked_tasks": list(dependents),
                    "description": f"Task '{task.get('name', task_id)}' is blocking {len(dependents)} other tasks"
                })
            
            # Check if task has been in progress for too long
            if status == 'in_progress':
                # TODO: Check actual time in progress from progress data
                bottlenecks.append({
                    "task_id": task_id,
                    "task_name": task.get('name', task_id),
                    "type": "stalled",
                    "severity": "medium",
                    "description": f"Task '{task.get('name', task_id)}' has been in progress for an extended period"
                })
        
        # Find critical path issues
        execution_order = task_graph.get_execution_order()
        for level_idx, level in enumerate(execution_order):
            # If a level has only one task and it's not completed, it's a bottleneck
            if len(level) == 1:
                task_id = level[0]
                status = task_statuses.get(task_id, 'pending')
                if status != 'completed':
                    bottlenecks.append({
                        "task_id": task_id,
                        "task_name": task_graph.nodes[task_id].get('name', task_id),
                        "type": "critical_path",
                        "severity": "high",
                        "description": f"Task '{task_graph.nodes[task_id].get('name', task_id)}' is on the critical path and blocking progress"
                    })
        
        return bottlenecks
    
    def _generate_recommendations(self, progress: Dict[str, Any], task_graph: Any, bottlenecks: List[Dict[str, Any]]) -> List[str]:
        """
        Generate recommendations based on progress and bottlenecks.
        
        Args:
            progress: Progress dictionary
            task_graph: TaskGraph instance
            bottlenecks: List of detected bottlenecks
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        task_statuses = progress.get('task_statuses', {})
        
        # Recommendations based on bottlenecks
        high_severity_bottlenecks = [b for b in bottlenecks if b.get('severity') == 'high']
        if high_severity_bottlenecks:
            for bottleneck in high_severity_bottlenecks[:3]:  # Top 3
                recommendations.append(
                    f"Priority: Complete '{bottleneck['task_name']}' to unblock {len(bottleneck.get('blocked_tasks', []))} dependent tasks"
                )
        
        # Find ready tasks that aren't started
        completed_tasks = {tid for tid, status in task_statuses.items() if status == 'completed'}
        ready_tasks = task_graph.get_ready_tasks(completed_tasks)
        unstarted_ready = [tid for tid in ready_tasks if task_statuses.get(tid) == 'pending']
        
        if unstarted_ready:
            task_names = [task_graph.nodes[tid].get('name', tid) for tid in unstarted_ready[:3]]
            recommendations.append(
                f"Next steps: Start these ready tasks: {', '.join(task_names)}"
            )
        
        # Check milestone progress
        milestone_scores = self._calculate_milestone_scores(progress, task_graph)
        stalled_milestones = [
            mid for mid, score in milestone_scores.items()
            if 0.0 < score < 1.0 and score < 0.3
        ]
        
        if stalled_milestones:
            recommendations.append(
                f"Attention: Milestones {', '.join(stalled_milestones)} are making slow progress"
            )
        
        # Overall progress recommendation
        overall_score = self._calculate_overall_score(progress, task_graph)
        if overall_score < 0.2:
            recommendations.append("Consider breaking down tasks into smaller, more manageable pieces")
        elif overall_score > 0.8:
            recommendations.append("Final stretch: Focus on completing remaining tasks and testing")
        
        if not recommendations:
            recommendations.append("Continue current progress. No immediate issues detected.")
        
        return recommendations
    
    def check_milestone_completion(self, milestone_id: str, progress: Dict[str, Any], task_graph: Any) -> Dict[str, Any]:
        """
        Check if a milestone is completed.
        
        Args:
            milestone_id: Milestone ID to check
            progress: Progress dictionary
            task_graph: TaskGraph instance
            
        Returns:
            Dictionary with completion status and details
        """
        task_statuses = progress.get('task_statuses', {})
        
        # Find all tasks for this milestone
        milestone_tasks = [
            tid for tid, task in task_graph.nodes.items()
            if task.get('milestone_id') == milestone_id
        ]
        
        if not milestone_tasks:
            return {
                "milestone_id": milestone_id,
                "completed": False,
                "reason": "No tasks found for this milestone"
            }
        
        completed_tasks = [
            tid for tid in milestone_tasks
            if task_statuses.get(tid) == 'completed'
        ]
        
        is_completed = len(completed_tasks) == len(milestone_tasks)
        
        return {
            "milestone_id": milestone_id,
            "completed": is_completed,
            "completed_tasks": len(completed_tasks),
            "total_tasks": len(milestone_tasks),
            "completion_percentage": (len(completed_tasks) / len(milestone_tasks)) * 100 if milestone_tasks else 0
        }
    
    def get_progress_summary(self, progress: Dict[str, Any], task_graph: Any) -> Dict[str, Any]:
        """
        Get a summary of current progress.
        
        Args:
            progress: Progress dictionary
            task_graph: TaskGraph instance
            
        Returns:
            Summary dictionary
        """
        task_statuses = progress.get('task_statuses', {})
        
        total = len(task_graph.nodes)
        completed = sum(1 for status in task_statuses.values() if status == 'completed')
        in_progress = sum(1 for status in task_statuses.values() if status == 'in_progress')
        pending = sum(1 for status in task_statuses.values() if status == 'pending')
        
        overall_score = self._calculate_overall_score(progress, task_graph)
        milestone_scores = self._calculate_milestone_scores(progress, task_graph)
        
        return {
            "overall_progress": overall_score,
            "task_counts": {
                "total": total,
                "completed": completed,
                "in_progress": in_progress,
                "pending": pending
            },
            "milestone_progress": milestone_scores,
            "timestamp": datetime.now().isoformat()
        }

