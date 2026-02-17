"""
Tests for core.orchestrator module.

Covers:
    - Orchestrator initialization
    - Agent lazy loading
    - Full pipeline execution
    - Individual stage execution
    - Error handling and pipeline failures
    - Status reporting
"""

import pytest
from unittest.mock import MagicMock, patch
from core.orchestrator import Orchestrator, PipelineError, PipelineStage, PipelineResult


class TestPipelineStage:
    """Tests for PipelineStage data class."""

    def test_creation(self):
        """PipelineStage should initialize with correct values."""
        stage = PipelineStage("classify", "S-1", "Intent classification")
        assert stage.name == "classify"
        assert stage.agent_id == "S-1"
        assert stage.status == "pending"

    def test_to_dict(self):
        """to_dict should return serializable dictionary."""
        stage = PipelineStage("plan", "A-1", "Planning")
        d = stage.to_dict()
        assert d['name'] == "plan"
        assert d['agent_id'] == "A-1"
        assert d['status'] == "pending"


class TestPipelineResult:
    """Tests for PipelineResult data class."""

    def test_creation(self):
        """PipelineResult should initialize with goal."""
        result = PipelineResult("Build API")
        assert result.goal == "Build API"
        assert result.status == "pending"
        assert result.stages == []

    def test_to_dict(self):
        """to_dict should return serializable dictionary."""
        result = PipelineResult("Test goal")
        d = result.to_dict()
        assert d['goal'] == "Test goal"
        assert 'stages' in d
        assert 'outputs' in d


class TestPipelineError:
    """Tests for PipelineError exception."""

    def test_properties(self):
        """PipelineError should preserve stage and message."""
        err = PipelineError("build", "No tasks to build")
        assert err.stage == "build"
        assert err.message == "No tasks to build"
        assert "build" in str(err)


class TestOrchestratorInit:
    """Tests for Orchestrator initialization."""

    def test_creation(self):
        """Orchestrator should create without agents loaded."""
        orch = Orchestrator()
        assert orch._initialized is False
        assert len(orch._agents) == 0

    def test_lazy_init(self):
        """Agents should be loaded on first use."""
        orch = Orchestrator()
        orch._ensure_agents()
        assert orch._initialized is True


class TestOrchestratorStages:
    """Tests for individual pipeline stages."""

    @pytest.fixture
    def orch(self):
        """Create orchestrator with agents partially loaded."""
        o = Orchestrator()
        o._initialized = True  # Skip lazy init
        return o

    def test_classify_fallback(self, orch):
        """Classify should work without Persona agent."""
        result = orch.classify("Build a REST API")
        assert result['goal'] == "Build a REST API"
        assert result['intent'] == "BUILD_REQUEST"
        assert '_stage' in result

    def test_plan_fallback(self, orch):
        """Plan should work without Architect agent."""
        classification = {"goal": "Build API", "intent": "BUILD_REQUEST"}
        result = orch.plan(classification)
        assert 'tasks' in result
        assert len(result['tasks']) > 0
        assert '_stage' in result

    def test_build_fallback(self, orch):
        """Build should work without Builder agent."""
        plan = {"tasks": [{"id": "T1", "name": "Create module"}]}
        result = orch.build(plan)
        assert 'warnings' in result
        assert '_stage' in result

    def test_validate_fallback(self, orch):
        """Validate should pass without System Designer."""
        result = orch.validate({}, {})
        assert result['valid'] is True
        assert '_stage' in result

    def test_integrate_fallback(self, orch):
        """Integrate should approve without Integrator."""
        result = orch.integrate({})
        assert result['status'] == "APPROVED"
        assert '_stage' in result

    def test_store_fallback(self, orch):
        """Store should use basic memory without Knowledge Engine."""
        result = orch.store("Test goal", {})
        assert result['success'] is True
        assert '_stage' in result

    def test_review_fallback(self, orch):
        """Review should return empty without Evolution Agent."""
        result = orch.review({})
        assert 'risks' in result
        assert '_stage' in result


class TestOrchestratorPipeline:
    """Tests for full pipeline execution."""

    def test_execute_returns_result(self):
        """Execute should return a complete result dictionary."""
        orch = Orchestrator()
        orch._initialized = True  # Skip agent loading
        result = orch.execute("Test goal")
        assert 'goal' in result
        assert 'status' in result
        assert 'stages' in result
        assert 'total_duration_ms' in result

    def test_execute_completes(self):
        """Execute should complete all stages with fallbacks."""
        orch = Orchestrator()
        orch._initialized = True
        result = orch.execute("Simple test")
        assert result['status'] == "completed"
        assert len(result['stages']) == 7


class TestOrchestratorStatus:
    """Tests for status reporting."""

    def test_get_status(self):
        """get_status should return valid status dict."""
        orch = Orchestrator()
        status = orch.get_status()
        assert 'orchestrator' in status
        assert 'agents' in status
        assert 'agents_loaded' in status
        assert 'agents_total' in status
        assert status['agents_total'] == 7
