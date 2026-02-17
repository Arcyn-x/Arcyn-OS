"""
Pipeline Orchestrator for Arcyn OS.

Wires all agents together into a coherent execution pipeline:
    Persona → Architect → Builder → SystemDesigner → Integrator → KnowledgeEngine → Evolution

This is the BRAIN of Arcyn OS — it takes a user goal and runs it through
the full multi-agent pipeline, collecting results at each stage.

Usage:
    from core.orchestrator import Orchestrator

    orch = Orchestrator()
    result = orch.execute("Build a REST API for task management")

Design Constraints:
    - Each stage is isolated and produces a structured output
    - Failures at any stage halt the pipeline with a clear error
    - All activity is logged and tracked by the Evolution Agent
    - The KnowledgeEngine stores results for cross-project learning
"""

import sys
import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Ensure project root is on path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import Logger
from core.memory import Memory
from core.context_manager import ContextManager


# =============================================================================
# Pipeline Stage Definitions
# =============================================================================

class PipelineStage:
    """Represents a single stage in the agent pipeline."""

    def __init__(self, name: str, agent_id: str, description: str):
        self.name = name
        self.agent_id = agent_id
        self.description = description
        self.status: str = "pending"
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.duration_ms: float = 0
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "agent_id": self.agent_id,
            "description": self.description,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }


class PipelineResult:
    """Complete result of a pipeline execution."""

    def __init__(self, goal: str):
        self.goal = goal
        self.status: str = "pending"
        self.stages: List[PipelineStage] = []
        self.started_at: str = datetime.now().isoformat()
        self.completed_at: Optional[str] = None
        self.total_duration_ms: float = 0
        self.error: Optional[str] = None
        self.outputs: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_ms": self.total_duration_ms,
            "error": self.error,
            "stages": [s.to_dict() for s in self.stages],
            "outputs": {
                k: (v if isinstance(v, (str, int, float, bool, list)) else str(v)[:500])
                for k, v in self.outputs.items()
            },
        }


# =============================================================================
# Orchestrator
# =============================================================================

class Orchestrator:
    """
    Pipeline Orchestrator for Arcyn OS.

    Coordinates the full agent pipeline from user input to final output.
    Each stage is executed in sequence, with failures halting the pipeline.

    Pipeline:
        1. classify  — Persona Agent classifies user intent
        2. plan      — Architect Agent creates structured plan
        3. build     — Builder Agent generates code
        4. validate  — System Designer validates architecture
        5. integrate — Integrator Agent checks compatibility
        6. store     — Knowledge Engine stores results
        7. review    — Evolution Agent provides strategic analysis

    Example:
        >>> orch = Orchestrator()
        >>> result = orch.execute("Build a REST API for task management")
        >>> print(result['status'])
        'completed'
    """

    def __init__(self, log_level: int = logging.INFO):
        """
        Initialize the Orchestrator with all agents.

        Args:
            log_level: Logging level (default: INFO)
        """
        self.logger = Logger("orchestrator", log_level=log_level)
        self.memory = Memory()
        self.context = ContextManager("orchestrator")
        self._agents: Dict[str, Any] = {}
        self._initialized = False

        self.logger.info("Orchestrator created")

    def _ensure_agents(self) -> None:
        """Lazy-initialize agents on first use to avoid import overhead."""
        if self._initialized:
            return

        self.logger.info("Initializing agent pipeline...")

        try:
            from agents.persona import PersonaAgent
            self._agents['persona'] = PersonaAgent()
            self.logger.info("  ✓ Persona Agent (S-1)")
        except Exception as e:
            self.logger.warning(f"  ✗ Persona Agent: {e}")

        try:
            from agents.architect import ArchitectAgent
            self._agents['architect'] = ArchitectAgent()
            self.logger.info("  ✓ Architect Agent (A-1)")
        except Exception as e:
            self.logger.warning(f"  ✗ Architect Agent: {e}")

        try:
            from agents.builder import BuilderAgent
            self._agents['builder'] = BuilderAgent()
            self.logger.info("  ✓ Builder Agent (F-1)")
        except Exception as e:
            self.logger.warning(f"  ✗ Builder Agent: {e}")

        try:
            from agents.system_designer import SystemDesignerAgent
            self._agents['system_designer'] = SystemDesignerAgent()
            self.logger.info("  ✓ System Designer Agent (F-2)")
        except Exception as e:
            self.logger.warning(f"  ✗ System Designer Agent: {e}")

        try:
            from agents.integrator import IntegratorAgent
            self._agents['integrator'] = IntegratorAgent()
            self.logger.info("  ✓ Integrator Agent (F-3)")
        except Exception as e:
            self.logger.warning(f"  ✗ Integrator Agent: {e}")

        try:
            from agents.knowledge_engine import KnowledgeEngine
            self._agents['knowledge'] = KnowledgeEngine()
            self.logger.info("  ✓ Knowledge Engine (S-2)")
        except Exception as e:
            self.logger.warning(f"  ✗ Knowledge Engine: {e}")

        try:
            from agents.evolution import EvolutionAgent
            self._agents['evolution'] = EvolutionAgent()
            self.logger.info("  ✓ Evolution Agent (S-3)")
        except Exception as e:
            self.logger.warning(f"  ✗ Evolution Agent: {e}")

        self._initialized = True
        agent_count = len(self._agents)
        self.logger.info(f"Pipeline ready: {agent_count}/7 agents loaded")

    # =========================================================================
    # Full Pipeline Execution
    # =========================================================================

    def execute(self, goal: str) -> Dict[str, Any]:
        """
        Execute a goal through the full agent pipeline.

        Runs all 7 stages in sequence. If any stage fails, the pipeline
        halts and returns a partial result with the error.

        Args:
            goal: Natural language goal (e.g., "Build a REST API")

        Returns:
            Pipeline result dictionary with status, stages, and outputs
        """
        self._ensure_agents()
        pipeline = PipelineResult(goal=goal)
        self.context.set_state("executing")
        self.context.add_history("pipeline_started", {"goal": goal})
        self.logger.info(f"Pipeline started: {goal}")

        start_time = time.time()

        try:
            # Stage 1: Classify
            stage_result = self.classify(goal)
            pipeline.stages.append(stage_result['_stage'])
            pipeline.outputs['classification'] = stage_result
            if stage_result.get('error'):
                raise PipelineError("classify", stage_result['error'])

            # Stage 2: Plan
            stage_result = self.plan(stage_result)
            pipeline.stages.append(stage_result['_stage'])
            pipeline.outputs['plan'] = stage_result
            if stage_result.get('error'):
                raise PipelineError("plan", stage_result['error'])

            # Stage 3: Build
            stage_result = self.build(stage_result)
            pipeline.stages.append(stage_result['_stage'])
            pipeline.outputs['build'] = stage_result
            if stage_result.get('error'):
                raise PipelineError("build", stage_result['error'])

            # Stage 4: Validate
            plan_output = pipeline.outputs.get('plan', {})
            stage_result = self.validate(stage_result, plan_output)
            pipeline.stages.append(stage_result['_stage'])
            pipeline.outputs['validation'] = stage_result
            # Validation warnings don't halt the pipeline

            # Stage 5: Integrate
            stage_result = self.integrate(pipeline.outputs)
            pipeline.stages.append(stage_result['_stage'])
            pipeline.outputs['integration'] = stage_result
            # Integration warnings don't halt unless BLOCKED

            if stage_result.get('status') == 'BLOCKED':
                raise PipelineError("integrate", "Integration blocked: " +
                                    str(stage_result.get('blocking_issues', [])))

            # Stage 6: Store
            stage_result = self.store(goal, pipeline.outputs)
            pipeline.stages.append(stage_result['_stage'])
            pipeline.outputs['knowledge'] = stage_result

            # Stage 7: Review
            stage_result = self.review(pipeline.outputs)
            pipeline.stages.append(stage_result['_stage'])
            pipeline.outputs['review'] = stage_result

            pipeline.status = "completed"
            self.logger.info("Pipeline completed successfully")

        except PipelineError as e:
            pipeline.status = "failed"
            pipeline.error = f"Pipeline failed at stage '{e.stage}': {e.message}"
            self.logger.error(pipeline.error)

        except Exception as e:
            pipeline.status = "error"
            pipeline.error = f"Unexpected error: {str(e)}"
            self.logger.error(pipeline.error)

        finally:
            elapsed = (time.time() - start_time) * 1000
            pipeline.total_duration_ms = elapsed
            pipeline.completed_at = datetime.now().isoformat()
            self.context.set_state("idle")
            self.context.add_history("pipeline_completed", {
                "status": pipeline.status,
                "duration_ms": elapsed,
            })

            # Clean stage metadata from outputs
            for key in pipeline.outputs:
                if isinstance(pipeline.outputs[key], dict):
                    pipeline.outputs[key].pop('_stage', None)

            # Persist pipeline result
            self.memory.write(
                f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                pipeline.to_dict()
            )

        return pipeline.to_dict()

    # =========================================================================
    # Individual Pipeline Stages
    # =========================================================================

    def classify(self, user_input: str) -> Dict[str, Any]:
        """
        Stage 1: Classify user intent via Persona Agent.

        Args:
            user_input: Raw user input string

        Returns:
            Classification result with intent, entities, routing
        """
        stage = PipelineStage("classify", "S-1", "Intent classification & routing")
        stage.started_at = datetime.now().isoformat()
        start = time.time()

        try:
            persona = self._agents.get('persona')
            if not persona:
                # Fallback: basic classification without agent
                result = {
                    "intent": "BUILD_REQUEST",
                    "goal": user_input,
                    "confidence": 0.7,
                    "routing": {"target_agent": "architect"},
                    "assumptions": ["Treating as a build request"],
                    "missing_info": [],
                }
            else:
                result = persona.handle_input(user_input)
                # Ensure we have the goal field
                if 'goal' not in result:
                    result['goal'] = user_input

            stage.status = "completed"
            self._record_activity("persona", "classify", "success", time.time() - start)

        except Exception as e:
            result = {"error": str(e), "goal": user_input}
            stage.status = "failed"
            stage.error = str(e)
            self._record_activity("persona", "classify", "failed", time.time() - start, str(e))

        stage.duration_ms = (time.time() - start) * 1000
        stage.completed_at = datetime.now().isoformat()
        result['_stage'] = stage
        return result

    def plan(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 2: Create structured plan via Architect Agent.

        Args:
            classification: Output from classify() stage

        Returns:
            Structured plan with tasks, milestones, dependencies
        """
        stage = PipelineStage("plan", "A-1", "Goal → structured plan")
        stage.started_at = datetime.now().isoformat()
        start = time.time()

        goal = classification.get('goal', '')

        try:
            architect = self._agents.get('architect')
            if not architect:
                result = {
                    "goal": goal,
                    "tasks": [{"id": "T1", "name": goal, "type": "feature", "effort": "medium"}],
                    "milestones": [{"id": "M1", "name": "MVP", "tasks": ["T1"]}],
                    "execution_order": ["T1"],
                    "warnings": ["Architect agent not available — minimal plan generated"],
                }
            else:
                result = architect.plan(goal)
                if not result:
                    result = {"goal": goal, "tasks": [], "milestones": []}

            stage.status = "completed"
            self._record_activity("architect", "plan", "success", time.time() - start)

        except Exception as e:
            result = {"error": str(e), "goal": goal}
            stage.status = "failed"
            stage.error = str(e)
            self._record_activity("architect", "plan", "failed", time.time() - start, str(e))

        stage.duration_ms = (time.time() - start) * 1000
        stage.completed_at = datetime.now().isoformat()
        result['_stage'] = stage
        return result

    def build(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 3: Generate code via Builder Agent.

        Args:
            plan: Output from plan() stage

        Returns:
            Build result with generated files, warnings, next steps
        """
        stage = PipelineStage("build", "F-1", "Plan → code generation")
        stage.started_at = datetime.now().isoformat()
        start = time.time()

        try:
            builder = self._agents.get('builder')
            tasks = plan.get('tasks', [])

            if not builder:
                result = {
                    "action": "build",
                    "files_changed": [],
                    "summary": "Builder agent not available",
                    "warnings": ["Builder agent not loaded"],
                    "task_results": [],
                }
            else:
                # Execute each task through the builder
                task_results = []
                files_changed = []
                warnings = []

                for task in tasks:
                    task_input = {
                        "action": "build",
                        "description": task.get("name", task.get("description", "")),
                        "target_path": task.get("target_path", ""),
                    }
                    try:
                        task_result = builder.build(task_input)
                        task_results.append({
                            "task_id": task.get("id", "unknown"),
                            "status": "completed",
                            "result": task_result,
                        })
                        files_changed.extend(task_result.get("files_changed", []))
                        warnings.extend(task_result.get("warnings", []))
                    except Exception as te:
                        task_results.append({
                            "task_id": task.get("id", "unknown"),
                            "status": "failed",
                            "error": str(te),
                        })
                        warnings.append(f"Task {task.get('id', '?')} failed: {te}")

                result = {
                    "action": "build",
                    "files_changed": files_changed,
                    "summary": f"Built {len(files_changed)} file(s) from {len(tasks)} task(s)",
                    "warnings": warnings,
                    "task_results": task_results,
                }

            stage.status = "completed"
            self._record_activity("builder", "build", "success", time.time() - start)

        except Exception as e:
            result = {"error": str(e)}
            stage.status = "failed"
            stage.error = str(e)
            self._record_activity("builder", "build", "failed", time.time() - start, str(e))

        stage.duration_ms = (time.time() - start) * 1000
        stage.completed_at = datetime.now().isoformat()
        result['_stage'] = stage
        return result

    def validate(self, build_result: Dict[str, Any],
                 plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 4: Validate architecture via System Designer Agent.

        Args:
            build_result: Output from build() stage
            plan: Output from plan() stage

        Returns:
            Validation result with compliance checks
        """
        stage = PipelineStage("validate", "F-2", "Architectural validation")
        stage.started_at = datetime.now().isoformat()
        start = time.time()

        try:
            designer = self._agents.get('system_designer')
            if not designer:
                result = {
                    "valid": True,
                    "errors": [],
                    "warnings": ["System Designer not available — validation skipped"],
                    "recommendations": [],
                }
            else:
                artifacts = {
                    "architecture": plan,
                    "build_output": build_result,
                }
                result = designer.validate_architecture(artifacts)

            stage.status = "completed"
            self._record_activity("system_designer", "validate", "success", time.time() - start)

        except Exception as e:
            result = {"valid": False, "error": str(e), "errors": [str(e)], "warnings": []}
            stage.status = "failed"
            stage.error = str(e)
            self._record_activity("system_designer", "validate", "failed",
                                  time.time() - start, str(e))

        stage.duration_ms = (time.time() - start) * 1000
        stage.completed_at = datetime.now().isoformat()
        result['_stage'] = stage
        return result

    def integrate(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 5: Check compatibility via Integrator Agent.

        Args:
            outputs: All pipeline outputs so far

        Returns:
            Integration result with compatibility checks
        """
        stage = PipelineStage("integrate", "F-3", "Compatibility & standards check")
        stage.started_at = datetime.now().isoformat()
        start = time.time()

        try:
            integrator = self._agents.get('integrator')
            if not integrator:
                result = {
                    "status": "APPROVED",
                    "warnings": ["Integrator not available — auto-approved"],
                    "actions_required": [],
                    "validation_details": {},
                }
            else:
                payload = {
                    "architect_plan": outputs.get('plan', {}),
                    "builder_output": outputs.get('build', {}),
                    "system_design": outputs.get('validation', {}),
                }
                result = integrator.integrate(payload)

            stage.status = "completed"
            self._record_activity("integrator", "integrate", "success", time.time() - start)

        except Exception as e:
            result = {"status": "ERROR", "error": str(e)}
            stage.status = "failed"
            stage.error = str(e)
            self._record_activity("integrator", "integrate", "failed",
                                  time.time() - start, str(e))

        stage.duration_ms = (time.time() - start) * 1000
        stage.completed_at = datetime.now().isoformat()
        result['_stage'] = stage
        return result

    def store(self, goal: str, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 6: Store results via Knowledge Engine.

        Args:
            goal: Original user goal
            outputs: All pipeline outputs

        Returns:
            Storage result with record IDs
        """
        stage = PipelineStage("store", "S-2", "Knowledge storage & indexing")
        stage.started_at = datetime.now().isoformat()
        start = time.time()

        try:
            knowledge = self._agents.get('knowledge')
            if not knowledge:
                result = {
                    "success": True,
                    "record_id": None,
                    "warnings": ["Knowledge Engine not available — stored to memory only"],
                }
                # Fallback: store to basic memory
                self.memory.write(f"goal_{datetime.now().strftime('%Y%m%d_%H%M%S')}", {
                    "goal": goal,
                    "plan": str(outputs.get('plan', {}))[:1000],
                    "status": outputs.get('integration', {}).get('status', 'unknown'),
                })
            else:
                source = {
                    "namespace": "pipeline",
                    "key": f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "content": {
                        "goal": goal,
                        "plan_summary": str(outputs.get('plan', {}))[:2000],
                        "build_summary": str(outputs.get('build', {}))[:2000],
                        "integration_status": outputs.get('integration', {}).get('status'),
                    },
                    "metadata": {
                        "source_agent": "orchestrator",
                        "pipeline_status": "completed",
                        "timestamp": datetime.now().isoformat(),
                    },
                }
                result = knowledge.ingest(source)

            stage.status = "completed"
            self._record_activity("knowledge", "store", "success", time.time() - start)

        except Exception as e:
            result = {"success": False, "error": str(e)}
            stage.status = "failed"
            stage.error = str(e)
            self._record_activity("knowledge", "store", "failed",
                                  time.time() - start, str(e))

        stage.duration_ms = (time.time() - start) * 1000
        stage.completed_at = datetime.now().isoformat()
        result['_stage'] = stage
        return result

    def review(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 7: Strategic review via Evolution Agent.

        Args:
            outputs: All pipeline outputs

        Returns:
            Review with risks, recommendations, priority
        """
        stage = PipelineStage("review", "S-3", "Strategic analysis & recommendations")
        stage.started_at = datetime.now().isoformat()
        start = time.time()

        try:
            evolution = self._agents.get('evolution')
            if not evolution:
                result = {
                    "risks": [],
                    "inefficiencies": [],
                    "suggested_changes": [],
                    "priority": "low",
                    "confidence": 0.0,
                    "warnings": ["Evolution Agent not available — review skipped"],
                }
            else:
                # Run a full observation cycle with pipeline context
                observation = evolution.observe()
                analysis = evolution.analyze(observation)
                result = evolution.recommend(analysis)

            stage.status = "completed"
            self._record_activity("evolution", "review", "success", time.time() - start)

        except Exception as e:
            result = {
                "risks": [],
                "inefficiencies": [],
                "suggested_changes": [],
                "priority": "unknown",
                "confidence": 0.0,
                "error": str(e),
            }
            stage.status = "failed"
            stage.error = str(e)
            self._record_activity("evolution", "review", "failed",
                                  time.time() - start, str(e))

        stage.duration_ms = (time.time() - start) * 1000
        stage.completed_at = datetime.now().isoformat()
        result['_stage'] = stage
        return result

    # =========================================================================
    # Status & Utilities
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status and agent health."""
        self._ensure_agents()
        agent_statuses = {}
        for name, agent in self._agents.items():
            try:
                status = agent.get_status()
                agent_statuses[name] = {
                    "loaded": True,
                    "state": status.get('state', 'unknown'),
                }
            except Exception as e:
                agent_statuses[name] = {
                    "loaded": True,
                    "state": "error",
                    "error": str(e),
                }

        # Mark missing agents
        for name in ['persona', 'architect', 'builder', 'system_designer',
                      'integrator', 'knowledge', 'evolution']:
            if name not in agent_statuses:
                agent_statuses[name] = {"loaded": False}

        return {
            "orchestrator": "ready" if self._initialized else "not_initialized",
            "agents": agent_statuses,
            "agents_loaded": len(self._agents),
            "agents_total": 7,
            "context": self.context.get_state(),
        }

    def _record_activity(self, agent_id: str, action: str, status: str,
                         duration: float, error: Optional[str] = None) -> None:
        """Record agent activity for monitoring."""
        evolution = self._agents.get('evolution')
        if evolution:
            try:
                evolution.record_agent_activity(
                    agent_id=agent_id,
                    agent_type="pipeline",
                    action=action,
                    status=status,
                    duration_ms=duration * 1000,
                    error_message=error,
                )
            except Exception:
                pass  # Don't let monitoring failures affect pipeline


class PipelineError(Exception):
    """Exception raised when a pipeline stage fails."""

    def __init__(self, stage: str, message: str):
        self.stage = stage
        self.message = message
        super().__init__(f"Pipeline failed at '{stage}': {message}")


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI entry point for the orchestrator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Arcyn OS Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m core.orchestrator "Build a REST API"
  python -m core.orchestrator --status
  python -m core.orchestrator --interactive
        """
    )

    parser.add_argument('goal', type=str, nargs='?', help='Goal to execute')
    parser.add_argument('--status', action='store_true', help='Show agent status')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    orch = Orchestrator(log_level=log_level)

    if args.status:
        import json
        status = orch.get_status()
        print(json.dumps(status, indent=2))

    elif args.interactive:
        print("\n" + "=" * 60)
        print("  Arcyn OS Pipeline Orchestrator")
        print("  Execute goals through the full agent pipeline")
        print("=" * 60)
        print("  Type a goal or 'exit' to quit")
        print("  Type 'status' to see agent health")
        print("=" * 60 + "\n")

        while True:
            try:
                goal = input("Goal > ").strip()
                if not goal:
                    continue
                if goal.lower() in ("exit", "quit"):
                    print("\nShutting down.\n")
                    break
                if goal.lower() == "status":
                    import json
                    print(json.dumps(orch.get_status(), indent=2))
                    continue

                print(f"\nExecuting: {goal}\n")
                result = orch.execute(goal)

                print(f"\nStatus: {result['status']}")
                print(f"Duration: {result['total_duration_ms']:.0f}ms")
                if result.get('error'):
                    print(f"Error: {result['error']}")

                for stage_info in result.get('stages', []):
                    status_icon = "✓" if stage_info['status'] == 'completed' else "✗"
                    print(f"  {status_icon} {stage_info['name']} "
                          f"({stage_info['duration_ms']:.0f}ms) - {stage_info['status']}")

                print()

            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.\n")
            except EOFError:
                break

    elif args.goal:
        import json
        result = orch.execute(args.goal)
        print(json.dumps(result, indent=2, default=str))

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
