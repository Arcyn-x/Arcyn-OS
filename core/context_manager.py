"""
Context manager for Arcyn OS.

Manages agent state, context switching, and session management.
"""

from typing import Any, Dict, Optional
from datetime import datetime


class ContextManager:
    """
    Manages context and state for agents.
    
    TODO: Implement context persistence
    TODO: Add context versioning
    TODO: Implement context sharing between agents
    TODO: Add context compression for large states
    """
    
    def __init__(self, agent_id: str):
        """
        Initialize the context manager.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        self.agent_id = agent_id
        self._context: Dict[str, Any] = {
            'agent_id': agent_id,
            'created_at': datetime.now().isoformat(),
            'state': 'idle',
            'session_data': {},
            'history': []
        }
    
    def set_state(self, state: str) -> None:
        """
        Set the current agent state.
        
        Args:
            state: New state (e.g., 'planning', 'executing', 'evaluating', 'idle')
        """
        self._context['state'] = state
        self._context['last_updated'] = datetime.now().isoformat()
    
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
            'data': data or {}
        }
        self._context['history'].append(history_entry)
        # Keep only last 1000 entries
        if len(self._context['history']) > 1000:
            self._context['history'] = self._context['history'][-1000:]
    
    def get_history(self, limit: Optional[int] = None) -> list:
        """
        Get context history.
        
        Args:
            limit: Optional limit on number of entries to return
            
        Returns:
            List of history entries
        """
        history = self._context['history']
        if limit:
            return history[-limit:]
        return history
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get full context dictionary.
        
        Returns:
            Complete context dictionary
        """
        return self._context.copy()
    
    def clear_context(self) -> None:
        """Clear all context data (except agent_id and created_at)."""
        self._context = {
            'agent_id': self.agent_id,
            'created_at': self._context.get('created_at', datetime.now().isoformat()),
            'state': 'idle',
            'session_data': {},
            'history': []
        }

