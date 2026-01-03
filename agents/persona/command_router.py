"""
Command Router module for Persona Agent.

Maps intents to internal agents and builds structured payloads.
"""

from typing import Dict, Any, Optional, List
import json
from pathlib import Path


class CommandRouter:
    """
    Routes commands to appropriate agents.
    
    Responsibilities:
    - Map intents to internal agents
    - Build structured payloads
    - Prevent unauthorized agent calls
    - Enforce command boundaries
    
    TODO: Add permission system
    TODO: Implement command validation
    TODO: Add rate limiting
    TODO: Support command chaining
    """
    
    def __init__(self):
        """Initialize the command router."""
        self.agent_map = self._build_agent_map()
        self.allowed_agents = ["architect", "system_designer", "builder", "integrator"]
    
    def _build_agent_map(self) -> Dict[str, Dict[str, Any]]:
        """
        Build mapping from intents to agents.
        
        Returns:
            Dictionary mapping intents to agent configurations
        """
        return {
            "build": {
                "agent": "builder",
                "method": "build",
                "requires": ["target_path", "description"]
            },
            "design": {
                "agent": "system_designer",
                "method": "design",
                "requires": ["goal"]
            },
            "integrate": {
                "agent": "integrator",
                "method": "integrate",
                "requires": ["payload"]
            },
            "status": {
                "agent": "architect",
                "method": "get_status",
                "requires": []
            },
            "explain": {
                "agent": None,  # Handled internally
                "method": None,
                "requires": []
            },
            "help": {
                "agent": None,  # Handled internally
                "method": None,
                "requires": []
            }
        }
    
    def route(self, intent: Dict[str, Any], session_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route an intent to the appropriate agent.
        
        Args:
            intent: Intent dictionary from classifier
            session_context: Optional session context
        
        Returns:
            Routing result dictionary:
            {
                "agent": str or None,
                "method": str or None,
                "payload": Dict,
                "requires_user_input": bool,
                "error": str or None
            }
        """
        intent_name = intent.get("intent")
        entities = intent.get("entities", {})
        
        if intent_name not in self.agent_map:
            return {
                "agent": None,
                "method": None,
                "payload": {},
                "requires_user_input": False,
                "error": f"Unknown intent: {intent_name}"
            }
        
        route_config = self.agent_map[intent_name]
        agent_name = route_config.get("agent")
        method = route_config.get("method")
        
        # Handle internal intents (help, explain)
        if agent_name is None:
            return {
                "agent": None,
                "method": None,
                "payload": {
                    "intent": intent_name,
                    "entities": entities
                },
                "requires_user_input": False,
                "error": None
            }
        
        # Build payload based on intent
        payload = self._build_payload(intent_name, entities, session_context)
        
        # Validate required fields
        required = route_config.get("requires", [])
        missing = [field for field in required if field not in payload or payload[field] is None]
        
        if missing:
            return {
                "agent": agent_name,
                "method": method,
                "payload": payload,
                "requires_user_input": True,
                "error": f"Missing required fields: {', '.join(missing)}"
            }
        
        return {
            "agent": agent_name,
            "method": method,
            "payload": payload,
            "requires_user_input": False,
            "error": None
        }
    
    def _build_payload(self, intent: str, entities: Dict[str, Any], 
                      session_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build payload for agent call.
        
        Args:
            intent: Intent name
            entities: Extracted entities
            session_context: Optional session context
        
        Returns:
            Payload dictionary
        """
        payload = {}
        
        if intent == "build":
            # Build task for Builder Agent
            goal = entities.get("goal") or session_context.get("last_goal")
            module = entities.get("module") or "module"
            
            payload = {
                "action": "build",
                "description": goal or f"Create {module} module",
                "target_path": entities.get("file") or f"core/{module}.py",
                "content": None  # Will be generated by Builder
            }
        
        elif intent == "design":
            # Design goal for System Designer Agent
            goal = entities.get("goal") or session_context.get("last_goal")
            if not goal:
                goal = "Design system architecture"
            
            payload = {
                "goal": goal,
                "requirements": {}
            }
        
        elif intent == "integrate":
            # Integration payload - may need to load from file or session
            payload_file = entities.get("file")
            if payload_file and Path(payload_file).exists():
                try:
                    with open(payload_file, 'r') as f:
                        payload = json.load(f)
                except Exception:
                    payload = {"error": "Failed to load payload file"}
            else:
                # Try to get from session context
                payload = session_context.get("last_integration_payload", {})
        
        elif intent == "status":
            # Status check - no payload needed
            payload = {}
        
        return payload
    
    def validate_agent_access(self, agent_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that an agent can be accessed.
        
        Args:
            agent_name: Name of the agent
        
        Returns:
            Tuple of (is_allowed: bool, error_message: Optional[str])
        """
        if agent_name not in self.allowed_agents:
            return False, f"Agent '{agent_name}' is not accessible"
        
        return True, None
    
    def get_available_commands(self) -> List[Dict[str, str]]:
        """
        Get list of available commands.
        
        Returns:
            List of command dictionaries
        """
        commands = []
        
        for intent, config in self.agent_map.items():
            if config["agent"]:
                commands.append({
                    "intent": intent,
                    "agent": config["agent"],
                    "description": self._get_intent_description(intent)
                })
        
        return commands
    
    def _get_intent_description(self, intent: str) -> str:
        """
        Get description for an intent.
        
        Args:
            intent: Intent name
        
        Returns:
            Description string
        """
        descriptions = {
            "build": "Create or scaffold code files",
            "design": "Design system architecture",
            "integrate": "Validate and integrate agent outputs",
            "status": "Check system or agent status"
        }
        return descriptions.get(intent, "")

