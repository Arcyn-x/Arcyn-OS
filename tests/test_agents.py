"""
Tests for all agent modules.

Covers:
    - Agent initialization
    - Agent status reporting
    - Core methods for each agent
"""

import pytest


class TestArchitectAgent:
    """Tests for the Architect Agent."""

    def test_import(self):
        """ArchitectAgent should be importable."""
        from agents.architect import ArchitectAgent
        assert ArchitectAgent is not None

    def test_init(self):
        """ArchitectAgent should initialize without errors."""
        from agents.architect import ArchitectAgent
        agent = ArchitectAgent()
        assert agent is not None

    def test_plan(self):
        """plan() should return a dict with expected keys."""
        from agents.architect import ArchitectAgent
        agent = ArchitectAgent()
        result = agent.plan("Build a simple calculator")
        assert isinstance(result, dict)
        assert 'goal' in result

    def test_get_status(self):
        """get_status() should return agent status."""
        from agents.architect import ArchitectAgent
        agent = ArchitectAgent()
        status = agent.get_status()
        assert isinstance(status, dict)


class TestBuilderAgent:
    """Tests for the Builder Agent."""

    def test_import(self):
        """BuilderAgent should be importable."""
        from agents.builder import BuilderAgent
        assert BuilderAgent is not None

    def test_init(self):
        """BuilderAgent should initialize without errors."""
        from agents.builder import BuilderAgent
        agent = BuilderAgent()
        assert agent is not None

    def test_build(self):
        """build() should return a dict with expected keys."""
        from agents.builder import BuilderAgent
        agent = BuilderAgent()
        task = {
            "action": "build",
            "description": "Test module",
            "target_path": "core/test_output.py",
        }
        result = agent.build(task)
        assert isinstance(result, dict)

    def test_get_status(self):
        """get_status() should return agent status."""
        from agents.builder import BuilderAgent
        agent = BuilderAgent()
        status = agent.get_status()
        assert isinstance(status, dict)


class TestPersonaAgent:
    """Tests for the Persona Agent."""

    def test_import(self):
        """PersonaAgent should be importable."""
        from agents.persona import PersonaAgent
        assert PersonaAgent is not None

    def test_init(self):
        """PersonaAgent should initialize without errors."""
        from agents.persona import PersonaAgent
        agent = PersonaAgent()
        assert agent is not None

    def test_handle_input(self):
        """handle_input() should return a dict with response."""
        from agents.persona import PersonaAgent
        agent = PersonaAgent()
        result = agent.handle_input("help")
        assert isinstance(result, dict)

    def test_get_status(self):
        """get_status() should return agent status."""
        from agents.persona import PersonaAgent
        agent = PersonaAgent()
        status = agent.get_status()
        assert isinstance(status, dict)


class TestSystemDesignerAgent:
    """Tests for the System Designer Agent."""

    def test_import(self):
        """SystemDesignerAgent should be importable."""
        from agents.system_designer import SystemDesignerAgent
        assert SystemDesignerAgent is not None

    def test_init(self):
        """SystemDesignerAgent should initialize without errors."""
        from agents.system_designer import SystemDesignerAgent
        agent = SystemDesignerAgent()
        assert agent is not None

    def test_get_status(self):
        """get_status() should return agent status."""
        from agents.system_designer import SystemDesignerAgent
        agent = SystemDesignerAgent()
        status = agent.get_status()
        assert isinstance(status, dict)


class TestIntegratorAgent:
    """Tests for the Integrator Agent."""

    def test_import(self):
        """IntegratorAgent should be importable."""
        from agents.integrator import IntegratorAgent
        assert IntegratorAgent is not None

    def test_init(self):
        """IntegratorAgent should initialize without errors."""
        from agents.integrator import IntegratorAgent
        agent = IntegratorAgent()
        assert agent is not None

    def test_validate(self):
        """validate() should return a dict."""
        from agents.integrator import IntegratorAgent
        agent = IntegratorAgent()
        result = agent.validate({"test": True})
        assert isinstance(result, dict)

    def test_get_status(self):
        """get_status() should return agent status."""
        from agents.integrator import IntegratorAgent
        agent = IntegratorAgent()
        status = agent.get_status()
        assert isinstance(status, dict)


class TestKnowledgeEngine:
    """Tests for the Knowledge Engine."""

    def test_import(self):
        """KnowledgeEngine should be importable."""
        from agents.knowledge_engine import KnowledgeEngine
        assert KnowledgeEngine is not None

    def test_init(self):
        """KnowledgeEngine should initialize without errors."""
        from agents.knowledge_engine import KnowledgeEngine
        engine = KnowledgeEngine()
        assert engine is not None

    def test_get_status(self):
        """get_status() should return engine status."""
        from agents.knowledge_engine import KnowledgeEngine
        engine = KnowledgeEngine()
        status = engine.get_status()
        assert isinstance(status, dict)


class TestEvolutionAgent:
    """Tests for the Evolution Agent."""

    def test_import(self):
        """EvolutionAgent should be importable."""
        from agents.evolution import EvolutionAgent
        assert EvolutionAgent is not None

    def test_init(self):
        """EvolutionAgent should initialize without errors."""
        from agents.evolution import EvolutionAgent
        agent = EvolutionAgent()
        assert agent is not None

    def test_observe(self):
        """observe() should return observation data."""
        from agents.evolution import EvolutionAgent
        agent = EvolutionAgent()
        result = agent.observe()
        assert isinstance(result, dict)

    def test_full_cycle(self):
        """run_full_cycle() should complete without errors."""
        from agents.evolution import EvolutionAgent
        agent = EvolutionAgent()
        result = agent.run_full_cycle()
        assert isinstance(result, dict)

    def test_get_status(self):
        """get_status() should return agent status."""
        from agents.evolution import EvolutionAgent
        agent = EvolutionAgent()
        status = agent.get_status()
        assert isinstance(status, dict)

    def test_health_report(self):
        """get_health_report() should return health metrics."""
        from agents.evolution import EvolutionAgent
        agent = EvolutionAgent()
        report = agent.get_health_report()
        assert isinstance(report, dict)


class TestAgentsPackage:
    """Tests for the agents package __init__."""

    def test_all_agents_importable(self):
        """All agents should be importable from agents package."""
        from agents import (
            PersonaAgent,
            ArchitectAgent,
            BuilderAgent,
            SystemDesignerAgent,
            IntegratorAgent,
            KnowledgeEngine,
            EvolutionAgent,
        )
        assert PersonaAgent is not None
        assert ArchitectAgent is not None
        assert BuilderAgent is not None
        assert SystemDesignerAgent is not None
        assert IntegratorAgent is not None
        assert KnowledgeEngine is not None
        assert EvolutionAgent is not None
