"""
Planner module for Architect Agent.

Converts high-level goals into structured plans with milestones and tasks.
Supports both rule-based and LLM-powered planning.
"""

from typing import Dict, List, Any, Optional
import re


class Planner:
    """
    Plans development tasks from high-level goals.
    
    Supports two modes:
    1. Rule-based: Fast, deterministic planning (plan method)
    2. LLM-powered: Intelligent planning via gateway (plan_with_llm method)
    
    All LLM calls route through the central gateway.
    """
    
    def __init__(self, agent_name: str = "Architect"):
        """
        Initialize the planner.
        
        Args:
            agent_name: Agent identifier for gateway routing
        """
        self.agent_name = agent_name
        self.planning_rules = self._load_default_rules()
        self._use_llm = True  # Enable LLM by default

    
    def _load_default_rules(self) -> Dict[str, Any]:
        """
        Load default planning rules.
        
        Returns:
            Dictionary of planning rules
        """
        # TODO: Load from configuration file or database
        return {
            'min_tasks_per_milestone': 2,
            'max_tasks_per_milestone': 10,
            'default_milestones': ['planning', 'implementation', 'testing', 'deployment']
        }
    
    def plan(self, goal: str) -> Dict[str, Any]:
        """
        Create a structured plan from a high-level goal.
        
        Args:
            goal: High-level goal description
            
        Returns:
            Dictionary containing:
            {
                "goal": "...",
                "milestones": [...],
                "tasks": [...]
            }
            
        Example:
            >>> planner = Planner()
            >>> plan = planner.plan("Build a REST API")
            >>> plan['goal'] == "Build a REST API"
            True
        """
        # Extract key components from goal
        goal_components = self._analyze_goal(goal)
        
        # Generate milestones
        milestones = self._generate_milestones(goal, goal_components)
        
        # Generate tasks
        tasks = self._generate_tasks(goal, goal_components, milestones)
        
        return {
            "goal": goal,
            "milestones": milestones,
            "tasks": tasks,
            "metadata": {
                "total_milestones": len(milestones),
                "total_tasks": len(tasks),
                "estimated_complexity": self._estimate_complexity(goal_components)
            }
        }
    
    def _analyze_goal(self, goal: str) -> Dict[str, Any]:
        """
        Analyze goal to extract components and requirements.
        
        Args:
            goal: Goal description
            
        Returns:
            Dictionary with analyzed components
        """
        # TODO: Use NLP/LLM for intelligent analysis
        # For now, use simple keyword extraction
        
        components = {
            'keywords': [],
            'technologies': [],
            'complexity_indicators': [],
            'domain': 'general'
        }
        
        # Extract keywords (simple approach)
        keywords = re.findall(r'\b[A-Z][a-z]+\b|\b\w{4,}\b', goal)
        components['keywords'] = list(set(keywords))
        
        # Detect common technologies
        tech_keywords = {
            'api': 'REST API',
            'database': 'Database',
            'web': 'Web Application',
            'mobile': 'Mobile App',
            'ai': 'AI/ML',
            'blockchain': 'Blockchain'
        }
        
        goal_lower = goal.lower()
        for keyword, tech in tech_keywords.items():
            if keyword in goal_lower:
                components['technologies'].append(tech)
        
        # Detect complexity indicators
        complexity_words = ['complex', 'advanced', 'enterprise', 'scalable', 'distributed']
        for word in complexity_words:
            if word in goal_lower:
                components['complexity_indicators'].append(word)
        
        return components
    
    def _generate_milestones(self, goal: str, components: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate milestones for the plan.
        
        Args:
            goal: Goal description
            components: Analyzed goal components
            
        Returns:
            List of milestone dictionaries
        """
        # TODO: Use LLM or rule engine for intelligent milestone generation
        # Default milestone structure
        default_milestones = [
            {
                "id": "milestone_1",
                "name": "Planning & Design",
                "description": "Define architecture, requirements, and design specifications",
                "status": "pending",
                "order": 1
            },
            {
                "id": "milestone_2",
                "name": "Core Implementation",
                "description": "Implement core functionality and features",
                "status": "pending",
                "order": 2
            },
            {
                "id": "milestone_3",
                "name": "Integration & Testing",
                "description": "Integrate components and perform testing",
                "status": "pending",
                "order": 3
            },
            {
                "id": "milestone_4",
                "name": "Deployment & Documentation",
                "description": "Deploy solution and create documentation",
                "status": "pending",
                "order": 4
            }
        ]
        
        # Adjust milestones based on goal complexity
        if components['complexity_indicators']:
            # Add additional milestones for complex projects
            default_milestones.insert(2, {
                "id": "milestone_2.5",
                "name": "Advanced Features",
                "description": "Implement advanced and complex features",
                "status": "pending",
                "order": 2.5
            })
        
        return default_milestones
    
    def _generate_tasks(self, goal: str, components: Dict[str, Any], milestones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate tasks for each milestone.
        
        Args:
            goal: Goal description
            components: Analyzed goal components
            milestones: List of milestones
            
        Returns:
            List of task dictionaries
        """
        tasks = []
        task_id_counter = 1
        
        for milestone in milestones:
            milestone_id = milestone['id']
            milestone_name = milestone['name']
            
            # Generate tasks based on milestone type
            if 'Planning' in milestone_name:
                milestone_tasks = self._generate_planning_tasks(goal, components, milestone_id, task_id_counter)
            elif 'Implementation' in milestone_name or 'Core' in milestone_name:
                milestone_tasks = self._generate_implementation_tasks(goal, components, milestone_id, task_id_counter)
            elif 'Testing' in milestone_name or 'Integration' in milestone_name:
                milestone_tasks = self._generate_testing_tasks(goal, components, milestone_id, task_id_counter)
            elif 'Deployment' in milestone_name:
                milestone_tasks = self._generate_deployment_tasks(goal, components, milestone_id, task_id_counter)
            else:
                milestone_tasks = self._generate_generic_tasks(goal, components, milestone_id, task_id_counter)
            
            tasks.extend(milestone_tasks)
            task_id_counter += len(milestone_tasks)
        
        return tasks
    
    def _generate_planning_tasks(self, goal: str, components: Dict[str, Any], milestone_id: str, start_id: int) -> List[Dict[str, Any]]:
        """Generate planning phase tasks."""
        return [
            {
                "id": f"task_{start_id}",
                "name": "Requirements Analysis",
                "description": "Analyze and document requirements for the goal",
                "milestone_id": milestone_id,
                "status": "pending",
                "priority": "high",
                "estimated_effort": "medium"
            },
            {
                "id": f"task_{start_id + 1}",
                "name": "Architecture Design",
                "description": "Design system architecture and component structure",
                "milestone_id": milestone_id,
                "status": "pending",
                "priority": "high",
                "estimated_effort": "medium"
            },
            {
                "id": f"task_{start_id + 2}",
                "name": "Technology Stack Selection",
                "description": "Select appropriate technologies and tools",
                "milestone_id": milestone_id,
                "status": "pending",
                "priority": "medium",
                "estimated_effort": "low"
            }
        ]
    
    def _generate_implementation_tasks(self, goal: str, components: Dict[str, Any], milestone_id: str, start_id: int) -> List[Dict[str, Any]]:
        """Generate implementation phase tasks."""
        base_tasks = [
            {
                "id": f"task_{start_id}",
                "name": "Setup Development Environment",
                "description": "Configure development environment and tooling",
                "milestone_id": milestone_id,
                "status": "pending",
                "priority": "high",
                "estimated_effort": "low"
            },
            {
                "id": f"task_{start_id + 1}",
                "name": "Implement Core Components",
                "description": "Build core functionality and components",
                "milestone_id": milestone_id,
                "status": "pending",
                "priority": "high",
                "estimated_effort": "high"
            },
            {
                "id": f"task_{start_id + 2}",
                "name": "Implement Supporting Features",
                "description": "Add supporting features and utilities",
                "milestone_id": milestone_id,
                "status": "pending",
                "priority": "medium",
                "estimated_effort": "medium"
            }
        ]
        
        # Add technology-specific tasks
        if 'REST API' in components.get('technologies', []):
            base_tasks.append({
                "id": f"task_{start_id + 3}",
                "name": "Implement API Endpoints",
                "description": "Create REST API endpoints and handlers",
                "milestone_id": milestone_id,
                "status": "pending",
                "priority": "high",
                "estimated_effort": "medium"
            })
        
        return base_tasks
    
    def _generate_testing_tasks(self, goal: str, components: Dict[str, Any], milestone_id: str, start_id: int) -> List[Dict[str, Any]]:
        """Generate testing phase tasks."""
        return [
            {
                "id": f"task_{start_id}",
                "name": "Unit Testing",
                "description": "Write and execute unit tests",
                "milestone_id": milestone_id,
                "status": "pending",
                "priority": "high",
                "estimated_effort": "medium"
            },
            {
                "id": f"task_{start_id + 1}",
                "name": "Integration Testing",
                "description": "Perform integration testing between components",
                "milestone_id": milestone_id,
                "status": "pending",
                "priority": "high",
                "estimated_effort": "medium"
            },
            {
                "id": f"task_{start_id + 2}",
                "name": "System Testing",
                "description": "Perform end-to-end system testing",
                "milestone_id": milestone_id,
                "status": "pending",
                "priority": "medium",
                "estimated_effort": "low"
            }
        ]
    
    def _generate_deployment_tasks(self, goal: str, components: Dict[str, Any], milestone_id: str, start_id: int) -> List[Dict[str, Any]]:
        """Generate deployment phase tasks."""
        return [
            {
                "id": f"task_{start_id}",
                "name": "Deployment Configuration",
                "description": "Configure deployment environment and settings",
                "milestone_id": milestone_id,
                "status": "pending",
                "priority": "high",
                "estimated_effort": "medium"
            },
            {
                "id": f"task_{start_id + 1}",
                "name": "Deploy to Production",
                "description": "Deploy solution to production environment",
                "milestone_id": milestone_id,
                "status": "pending",
                "priority": "high",
                "estimated_effort": "low"
            },
            {
                "id": f"task_{start_id + 2}",
                "name": "Create Documentation",
                "description": "Write user and technical documentation",
                "milestone_id": milestone_id,
                "status": "pending",
                "priority": "medium",
                "estimated_effort": "medium"
            }
        ]
    
    def _generate_generic_tasks(self, goal: str, components: Dict[str, Any], milestone_id: str, start_id: int) -> List[Dict[str, Any]]:
        """Generate generic tasks for unknown milestone types."""
        return [
            {
                "id": f"task_{start_id}",
                "name": "Execute Milestone Tasks",
                "description": f"Complete tasks for {milestone_id}",
                "milestone_id": milestone_id,
                "status": "pending",
                "priority": "medium",
                "estimated_effort": "medium"
            }
        ]
    
    def _estimate_complexity(self, components: Dict[str, Any]) -> str:
        """
        Estimate overall plan complexity.
        
        Args:
            components: Analyzed goal components
            
        Returns:
            Complexity level: 'low', 'medium', or 'high'
        """
        complexity_score = 0
        
        # More technologies = higher complexity
        complexity_score += len(components.get('technologies', []))
        
        # Complexity indicators add to score
        complexity_score += len(components.get('complexity_indicators', [])) * 2
        
        if complexity_score <= 2:
            return 'low'
        elif complexity_score <= 5:
            return 'medium'
        else:
            return 'high'
    
    # =========================================================================
    # LLM-Powered Planning
    # =========================================================================
    
    def plan_with_llm(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        task_id: str = "plan"
    ) -> Dict[str, Any]:
        """
        Create a comprehensive plan using LLM.
        
        Uses the LLM Gateway for intelligent goal decomposition,
        technology decisions, and task generation.
        
        Args:
            goal: High-level goal description
            context: Optional context (existing code, constraints, etc.)
            task_id: Task identifier for tracking
        
        Returns:
            Dictionary containing:
            {
                "goal": str,
                "decisions": {...},
                "rejected_options": [...],
                "milestones": [...],
                "tasks": [...],
                "execution_order": [...],
                "architectural_constraints": [...],
                "open_questions": [...]
            }
        """
        if not self._use_llm:
            # Fall back to rule-based if LLM disabled
            return self.plan(goal)
        
        try:
            from core.llm_gateway import request_structured
            
            # Build the prompt
            context_str = ""
            if context:
                import json
                context_str = f"\nContext:\n{json.dumps(context, indent=2)}"
            
            prompt = f"""You are the Architect Agent (A-1) of Arcyn OS.

Create a comprehensive development plan for this goal:

Goal: {goal}
{context_str}

Requirements:
1. Technology decisions with clear reasoning
2. Rejected alternatives and why
3. 3-5 milestones with descriptions
4. Tasks for each milestone with dependencies
5. Execution order
6. Architectural constraints for Builders
7. Open questions needing clarification

Output JSON:
{{
  "goal": "...",
  "decisions": {{
    "framework": {{"choice": "...", "reasoning": "..."}},
    "database": {{"choice": "...", "reasoning": "..."}}
  }},
  "rejected_options": [
    {{"category": "...", "option": "...", "reason": "..."}}
  ],
  "milestones": [
    {{"id": "M1", "name": "...", "description": "...", "tasks": ["T1", "T2"]}}
  ],
  "tasks": [
    {{"id": "T1", "name": "...", "description": "...", "milestone_id": "M1", "dependencies": [], "effort": "low|medium|high"}}
  ],
  "execution_order": ["T1", "T2", "..."],
  "architectural_constraints": ["..."],
  "open_questions": ["..."]
}}"""
            
            response = request_structured(
                agent=self.agent_name,
                task_id=task_id,
                prompt=prompt,
                schema={
                    "goal": "",
                    "decisions": {},
                    "milestones": [],
                    "tasks": [],
                    "execution_order": []
                },
                config={"max_tokens": 4000, "temperature": 0.5}
            )
            
            if response.success and response.parsed_json:
                result = response.parsed_json
                result["source"] = "llm"
                result["metadata"] = {
                    "total_milestones": len(result.get("milestones", [])),
                    "total_tasks": len(result.get("tasks", [])),
                    "request_id": response.request_id,
                    "tokens_used": response.tokens_total
                }
                return result
            
            # Fall back to rule-based on failure
            return self.plan(goal)
            
        except Exception as e:
            # Fall back to rule-based on exception
            result = self.plan(goal)
            result["llm_error"] = str(e)
            return result
    
    def enable_llm(self) -> None:
        """Enable LLM-powered planning."""
        self._use_llm = True
    
    def disable_llm(self) -> None:
        """Disable LLM planning (rule-based only)."""
        self._use_llm = False
