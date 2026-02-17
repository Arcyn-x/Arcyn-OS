"""
Tests for core.context_manager module.

Covers:
    - State management (set, get)
    - Data storage (set, get, remove)
    - History tracking
    - Context snapshots
    - Inter-agent context sharing
    - Persistence
    - Versioning
"""

import pytest
from core.context_manager import ContextManager, _shared_contexts


@pytest.fixture(autouse=True)
def clear_shared_contexts():
    """Clear shared context bus between tests."""
    _shared_contexts.clear()
    yield
    _shared_contexts.clear()


class TestContextState:
    """Tests for state management."""

    def test_initial_state(self):
        """Context should start in 'idle' state."""
        ctx = ContextManager("test_agent")
        assert ctx.get_state() == "idle"

    def test_set_state(self):
        """Setting state should update it."""
        ctx = ContextManager("test_agent")
        ctx.set_state("planning")
        assert ctx.get_state() == "planning"

    def test_state_change_logs_history(self):
        """State changes should be logged in history."""
        ctx = ContextManager("test_agent")
        ctx.set_state("executing")
        history = ctx.get_history(event_filter="state_changed")
        assert len(history) == 1
        assert history[0]['data']['from'] == 'idle'
        assert history[0]['data']['to'] == 'executing'


class TestContextData:
    """Tests for data storage."""

    def test_set_and_get(self):
        """Set data should be retrievable."""
        ctx = ContextManager("test_agent")
        ctx.set_data("goal", "Build API")
        assert ctx.get_data("goal") == "Build API"

    def test_get_default(self):
        """Missing key should return default."""
        ctx = ContextManager("test_agent")
        assert ctx.get_data("missing", "fallback") == "fallback"

    def test_get_default_none(self):
        """Missing key with no default should return None."""
        ctx = ContextManager("test_agent")
        assert ctx.get_data("missing") is None

    def test_remove_data(self):
        """Remove should delete key and return True."""
        ctx = ContextManager("test_agent")
        ctx.set_data("temp", 123)
        assert ctx.remove_data("temp") is True
        assert ctx.get_data("temp") is None

    def test_remove_missing(self):
        """Removing missing key should return False."""
        ctx = ContextManager("test_agent")
        assert ctx.remove_data("ghost") is False


class TestContextHistory:
    """Tests for history tracking."""

    def test_add_history(self):
        """Adding history should be retrievable."""
        ctx = ContextManager("test_agent")
        ctx.add_history("task_completed", {"task_id": "T1"})
        history = ctx.get_history()
        assert len(history) >= 1
        assert history[-1]['event'] == "task_completed"

    def test_history_limit(self):
        """History should respect limit parameter."""
        ctx = ContextManager("test_agent")
        for i in range(10):
            ctx.add_history(f"event_{i}")
        history = ctx.get_history(limit=3)
        assert len(history) == 3

    def test_history_filter(self):
        """History should filter by event name."""
        ctx = ContextManager("test_agent")
        ctx.add_history("type_a", {"v": 1})
        ctx.add_history("type_b", {"v": 2})
        ctx.add_history("type_a", {"v": 3})
        filtered = ctx.get_history(event_filter="type_a")
        assert len(filtered) == 2
        assert all(h['event'] == 'type_a' for h in filtered)


class TestContextSnapshot:
    """Tests for context snapshots."""

    def test_snapshot_excludes_history(self):
        """Snapshot should not include history."""
        ctx = ContextManager("test_agent")
        ctx.add_history("event1")
        snap = ctx.get_snapshot()
        assert 'history' not in snap

    def test_snapshot_includes_state(self):
        """Snapshot should include current state."""
        ctx = ContextManager("test_agent")
        ctx.set_state("building")
        snap = ctx.get_snapshot()
        assert snap['state'] == "building"

    def test_snapshot_includes_data(self):
        """Snapshot should include session data."""
        ctx = ContextManager("test_agent")
        ctx.set_data("key", "value")
        snap = ctx.get_snapshot()
        assert snap['session_data']['key'] == "value"


class TestContextSharing:
    """Tests for inter-agent context sharing."""

    def test_publish_and_read(self):
        """Published data should be readable by other agents."""
        ctx_a = ContextManager("agent_a")
        ctx_a.publish("plan", {"tasks": ["T1", "T2"]})

        # Another agent reads it
        plan = ContextManager.get_shared("agent_a", "plan")
        assert plan == {"tasks": ["T1", "T2"]}

    def test_read_missing_agent(self):
        """Reading from non-existent agent should return default."""
        result = ContextManager.get_shared("ghost_agent", "key", "default_val")
        assert result == "default_val"

    def test_read_missing_key(self):
        """Reading missing key from existing agent should return default."""
        ctx = ContextManager("agent_x")
        ctx.publish("exists", True)

        result = ContextManager.get_shared("agent_x", "missing_key", None)
        assert result is None

    def test_list_shared(self):
        """List shared should show all published entries."""
        ctx_a = ContextManager("agent_a")
        ctx_b = ContextManager("agent_b")
        ctx_a.publish("plan", "plan_data")
        ctx_b.publish("code", "code_data")

        all_shared = ContextManager.list_shared()
        assert "agent_a" in all_shared
        assert "agent_b" in all_shared
        assert all_shared["agent_a"]["plan"] == "plan_data"

    def test_list_shared_filtered(self):
        """List shared with agent filter should return only that agent."""
        ctx = ContextManager("filtered_agent")
        ctx.publish("item", 42)

        result = ContextManager.list_shared("filtered_agent")
        assert result == {"item": 42}


class TestContextVersioning:
    """Tests for version tracking."""

    def test_version_increments(self):
        """Version should increment on state and data changes."""
        ctx = ContextManager("test_agent")
        initial = ctx._version
        ctx.set_state("planning")
        assert ctx._version > initial

    def test_version_in_snapshot(self):
        """Version should be present in snapshot."""
        ctx = ContextManager("test_agent")
        ctx.set_data("x", 1)
        snap = ctx.get_snapshot()
        assert 'version' in snap
        assert snap['version'] > 0


class TestContextClear:
    """Tests for context clearing."""

    def test_clear_resets_state(self):
        """Clear should reset state to idle."""
        ctx = ContextManager("test_agent")
        ctx.set_state("executing")
        ctx.set_data("key", "value")
        ctx.clear_context()
        assert ctx.get_state() == "idle"
        assert ctx.get_data("key") is None
