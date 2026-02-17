"""
Context manager for Arcyn OS.

Manages agent state, context switching, session management, and inter-agent
context sharing.

Features:
    - Agent state tracking (idle, planning, executing, evaluating, etc.)
    - Session data persistence via Memory module
    - Context sharing between agents via shared context bus
    - Context versioning with history
    - Serializable context snapshots
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .memory import Memory


# Global shared context bus for inter-agent communication
_shared_contexts: Dict[str, Dict[str, Any]] = {}


class ContextManager:
    """
    Manages context and state for agents.

    Each agent gets its own ContextManager instance with isolated state.
    Agents can publish context to the shared bus and subscribe to other
    agents' context for coordination.

    Example:
        >>> ctx = ContextManager("architect")
        >>> ctx.set_state("planning")
        >>> ctx.set_data("current_goal", "Build API")
        >>> ctx.publish("current_plan", {"tasks": [...]})
        >>>
        >>> # From another agent:
        >>> plan = ContextManager.get_shared("architect", "current_plan")
    """

    def __init__(self, agent_id: str, memory: Optional[Memory] = None,
                 persist: bool = False):
        """
        Initialize the context manager.

        Args:
            agent_id: Unique identifier for the agent
            memory: Optional Memory instance for persistence
            persist: Whether to auto-persist context changes
        """
        self.agent_id = agent_id
        self._memory = memory
        self._persist = persist
        self._version = 0
        self._context: Dict[str, Any] = {
            'agent_id': agent_id,
            'created_at': datetime.now().isoformat(),
            'state': 'idle',
            'session_data': {},
            'history': [],
            'version': 0,
        }

        # Try to restore persisted context
        if self._persist and self._memory:
            self._restore()

    def set_state(self, state: str) -> None:
        """
        Set the current agent state.

        Args:
            state: New state (e.g., 'planning', 'executing', 'evaluating', 'idle')
        """
        old_state = self._context['state']
        self._context['state'] = state
        self._context['last_updated'] = datetime.now().isoformat()
        self._bump_version()

        if old_state != state:
            self.add_history("state_changed", {
                "from": old_state,
                "to": state,
            })

    def get_state(self) -> str:
        """
        Get the current agent state.

        Returns:
            Current state string
        """
        return self._context.get('state', 'idle')

    def set_data(self, key: str, value: Any) -> None:
        """
        Store data in context.

        Args:
            key: Data key
            value: Data value
        """
        self._context['session_data'][key] = value
        self._context['last_updated'] = datetime.now().isoformat()
        self._bump_version()

    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Retrieve data from context.

        Args:
            key: Data key
            default: Default value if key not found

        Returns:
            Stored value or default
        """
        return self._context['session_data'].get(key, default)

    def remove_data(self, key: str) -> bool:
        """
        Remove data from context.

        Args:
            key: Data key to remove

        Returns:
            True if key was found and removed
        """
        if key in self._context['session_data']:
            del self._context['session_data'][key]
            self._bump_version()
            return True
        return False

    def add_history(self, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an event to history.

        Args:
            event: Event description
            data: Optional event data
        """
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'data': data or {},
            'version': self._version,
        }
        self._context['history'].append(history_entry)
        # Keep only last 1000 entries
        if len(self._context['history']) > 1000:
            self._context['history'] = self._context['history'][-1000:]

    def get_history(self, limit: Optional[int] = None,
                    event_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get context history.

        Args:
            limit: Optional limit on number of entries to return
            event_filter: Optional filter by event name

        Returns:
            List of history entries
        """
        history = self._context['history']

        if event_filter:
            history = [h for h in history if h.get('event') == event_filter]

        if limit:
            return history[-limit:]
        return history

    def get_context(self) -> Dict[str, Any]:
        """
        Get full context dictionary.

        Returns:
            Complete context dictionary (copy)
        """
        return self._context.copy()

    def get_snapshot(self) -> Dict[str, Any]:
        """
        Get a lightweight snapshot without history.

        Returns:
            Context snapshot with state, data, and version
        """
        return {
            'agent_id': self.agent_id,
            'state': self._context['state'],
            'session_data': self._context['session_data'].copy(),
            'version': self._version,
            'last_updated': self._context.get('last_updated'),
        }

    def clear_context(self) -> None:
        """Clear all context data (except agent_id and created_at)."""
        self._context = {
            'agent_id': self.agent_id,
            'created_at': self._context.get('created_at', datetime.now().isoformat()),
            'state': 'idle',
            'session_data': {},
            'history': [],
            'version': self._version + 1,
        }
        self._version += 1
        self._auto_persist()

    # =========================================================================
    # Context Sharing (Inter-Agent Communication)
    # =========================================================================

    def publish(self, key: str, value: Any) -> None:
        """
        Publish data to the shared context bus.

        Other agents can read this via ContextManager.get_shared().

        Args:
            key: Data key
            value: Data value
        """
        if self.agent_id not in _shared_contexts:
            _shared_contexts[self.agent_id] = {}

        _shared_contexts[self.agent_id][key] = {
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'version': self._version,
        }

    @staticmethod
    def get_shared(agent_id: str, key: str, default: Any = None) -> Any:
        """
        Read data from another agent's shared context.

        Args:
            agent_id: ID of the agent that published the data
            key: Data key
            default: Default value if not found

        Returns:
            Published value or default
        """
        agent_ctx = _shared_contexts.get(agent_id, {})
        entry = agent_ctx.get(key)
        if entry is not None:
            return entry.get('value', default)
        return default

    @staticmethod
    def list_shared(agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        List all shared context entries.

        Args:
            agent_id: Optional filter by agent

        Returns:
            Dictionary of shared context entries
        """
        if agent_id:
            return {
                k: v.get('value')
                for k, v in _shared_contexts.get(agent_id, {}).items()
            }
        return {
            aid: {k: v.get('value') for k, v in entries.items()}
            for aid, entries in _shared_contexts.items()
        }

    # =========================================================================
    # Persistence
    # =========================================================================

    def save(self) -> bool:
        """
        Explicitly save context to persistent memory.

        Returns:
            True if saved successfully
        """
        if not self._memory:
            self._memory = Memory()

        return self._memory.write(
            f"context_{self.agent_id}",
            self._context,
            namespace="context",
            source_agent=self.agent_id,
            tags=["context", self.agent_id],
        )

    def _restore(self) -> None:
        """Restore context from persistent memory."""
        if not self._memory:
            return

        saved = self._memory.read(f"context_{self.agent_id}")
        if saved and isinstance(saved, dict):
            self._context = saved
            self._version = saved.get('version', 0)

    def _bump_version(self) -> None:
        """Increment version counter and auto-persist if enabled."""
        self._version += 1
        self._context['version'] = self._version
        self._auto_persist()

    def _auto_persist(self) -> None:
        """Auto-save if persistence is enabled."""
        if self._persist and self._memory:
            self.save()
