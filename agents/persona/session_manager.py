"""
Session Manager module for Persona Agent.

Tracks session state and manages short-term conversational context.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque


class SessionManager:
    """
    Manages session state and conversation context.
    
    Responsibilities:
    - Track session state
    - Store recent commands
    - Manage short-term conversational context
    - Reset sessions safely
    
    This is not long-term memory.
    
    TODO: Add session persistence
    TODO: Implement context window management
    TODO: Add session statistics
    TODO: Support multiple concurrent sessions
    """
    
    def __init__(self, session_id: Optional[str] = None, max_history: int = 50):
        """
        Initialize the session manager.
        
        Args:
            session_id: Optional session identifier
            max_history: Maximum number of commands to remember
        """
        self.session_id = session_id or f"session_{datetime.now().isoformat()}"
        self.max_history = max_history
        self.command_history: deque = deque(maxlen=max_history)
        self.context: Dict[str, Any] = {
            "last_goal": None,
            "last_agent": None,
            "last_output": None,
            "last_intent": None
        }
        self.created_at = datetime.now().isoformat()
    
    def add_command(self, command: Dict[str, Any]) -> None:
        """
        Add a command to history.
        
        Args:
            command: Command dictionary with input, intent, output, etc.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "input": command.get("input", ""),
            "intent": command.get("intent", {}),
            "output": command.get("output", {}),
            "agent": command.get("agent"),
            "success": command.get("success", False)
        }
        
        self.command_history.append(entry)
        
        # Update context
        if "intent" in command:
            intent = command["intent"]
            if isinstance(intent, dict):
                self.context["last_intent"] = intent.get("intent")
                entities = intent.get("entities", {})
                if "goal" in entities:
                    self.context["last_goal"] = entities["goal"]
        
        if "agent" in command:
            self.context["last_agent"] = command["agent"]
        
        if "output" in command:
            self.context["last_output"] = command["output"]
    
    def get_recent_commands(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent commands from history.
        
        Args:
            count: Number of recent commands to return
        
        Returns:
            List of recent command dictionaries
        """
        return list(self.command_history)[-count:]
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get current session context.
        
        Returns:
            Context dictionary
        """
        return self.context.copy()
    
    def update_context(self, key: str, value: Any) -> None:
        """
        Update a context value.
        
        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value
    
    def reset(self) -> None:
        """Reset session (clear history and context)."""
        self.command_history.clear()
        self.context = {
            "last_goal": None,
            "last_agent": None,
            "last_output": None,
            "last_intent": None
        }
        self.created_at = datetime.now().isoformat()
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get session information.
        
        Returns:
            Session info dictionary
        """
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "command_count": len(self.command_history),
            "context": self.context.copy()
        }
    
    def has_recent_command(self, intent: str, lookback: int = 3) -> bool:
        """
        Check if a recent command had a specific intent.
        
        Args:
            intent: Intent to check for
            lookback: Number of recent commands to check
        
        Returns:
            True if intent found in recent commands
        """
        recent = self.get_recent_commands(lookback)
        for cmd in recent:
            cmd_intent = cmd.get("intent", {})
            if isinstance(cmd_intent, dict):
                if cmd_intent.get("intent") == intent:
                    return True
        return False

