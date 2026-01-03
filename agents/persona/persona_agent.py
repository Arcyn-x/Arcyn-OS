"""
Persona Agent (S-1) for Arcyn OS.

The Persona Agent is the primary human interface to Arcyn OS.

It translates human intent → structured system commands
and system outputs → human-readable responses.
"""

from typing import Dict, Any, Optional
from .intent_classifier import IntentClassifier
from .command_router import CommandRouter
from .response_formatter import ResponseFormatter
from .session_manager import SessionManager
from core.logger import Logger
from core.context_manager import ContextManager
from core.memory import Memory


class PersonaAgent:
    """
    Main Persona Agent class.
    
    The Persona Agent does NOT plan architecture, write code, or design systems.
    It is an interface, not a decision-maker.
    
    Example:
        >>> agent = PersonaAgent()
        >>> response = agent.handle_input("build a memory module")
        >>> print(response)
    """
    
    def __init__(self, agent_id: str = "persona_agent", log_level: int = 20, verbose: bool = False):
        """
        Initialize the Persona Agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            log_level: Logging level (default: 20 = INFO)
            verbose: Whether to use verbose output mode
        """
        self.agent_id = agent_id
        self.logger = Logger(f"PersonaAgent-{agent_id}", log_level=log_level)
        self.context = ContextManager(agent_id)
        self.memory = Memory()
        
        # Initialize sub-components
        self.intent_classifier = IntentClassifier()
        self.command_router = CommandRouter()
        self.response_formatter = ResponseFormatter(verbose=verbose)
        self.session_manager = SessionManager(session_id=agent_id)
        
        # Lazy import agents (only when needed)
        self._architect_agent = None
        self._system_designer_agent = None
        self._builder_agent = None
        self._integrator_agent = None
        
        self.logger.info(f"Persona Agent {agent_id} initialized")
        self.context.set_state('idle')
    
    def handle_input(self, user_input: str) -> Dict[str, Any]:
        """
        Handle user input and return response.
        
        Args:
            user_input: User's natural language input
        
        Returns:
            Dictionary containing:
            {
                "response": str,
                "intent": Dict,
                "routing": Dict,
                "success": bool,
                "error": str or None
            }
        """
        self.logger.info(f"Handling input: {user_input[:50]}...")
        self.context.set_state('processing')
        self.context.add_history('input_received', {'input': user_input})
        
        result = {
            "response": "",
            "intent": {},
            "routing": {},
            "success": False,
            "error": None
        }
        
        try:
            # Step 1: Classify intent
            intent = self.intent_classifier.classify(user_input)
            result["intent"] = intent
            
            # Step 2: Route command
            session_context = self.session_manager.get_context()
            routing = self.command_router.route(intent, session_context)
            result["routing"] = routing
            
            # Step 3: Execute or handle internally
            if routing.get("error"):
                result["error"] = routing["error"]
                result["response"] = f"Error: {routing['error']}"
                result["success"] = False
            elif routing.get("requires_user_input"):
                result["error"] = routing.get("error", "Missing required information")
                result["response"] = f"Please provide: {routing.get('error', 'more information')}"
                result["success"] = False
            elif routing.get("agent") is None:
                # Handle internally (help, explain)
                result["response"] = self._handle_internal_intent(intent, routing.get("payload", {}))
                result["success"] = True
            else:
                # Execute agent call
                agent_output = self._execute_agent_call(routing)
                result["response"] = self.response_formatter.format(agent_output, intent.get("intent"))
                result["success"] = agent_output is not None
                
                # Store in session
                self.session_manager.add_command({
                    "input": user_input,
                    "intent": intent,
                    "output": agent_output,
                    "agent": routing.get("agent"),
                    "success": result["success"]
                })
            
            self.context.add_history('input_processed', {'intent': intent.get("intent"), 'success': result["success"]})
            self.context.set_state('idle')
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing input: {str(e)}"
            self.logger.error(error_msg)
            result["error"] = error_msg
            result["response"] = f"Error: {str(e)}"
            result["success"] = False
            self.context.set_state('error')
            self.context.add_history('input_failed', {'error': str(e)})
            return result
    
    def route(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route an intent to the appropriate agent (without execution).
        
        Args:
            intent: Intent dictionary
        
        Returns:
            Routing result dictionary
        """
        session_context = self.session_manager.get_context()
        return self.command_router.route(intent, session_context)
    
    def respond(self, system_output: Dict[str, Any], intent: Optional[str] = None) -> str:
        """
        Format system output into human-readable response.
        
        Args:
            system_output: System output dictionary
            intent: Optional intent that generated this output
        
        Returns:
            Formatted response string
        """
        return self.response_formatter.format(system_output, intent)
    
    def _handle_internal_intent(self, intent: Dict[str, Any], payload: Dict[str, Any]) -> str:
        """
        Handle internal intents (help, explain).
        
        Args:
            intent: Intent dictionary
            payload: Payload dictionary
        
        Returns:
            Response string
        """
        intent_name = intent.get("intent", "")
        
        if intent_name == "help":
            commands = self.command_router.get_available_commands()
            return self.response_formatter.format_help(commands)
        
        elif intent_name == "explain":
            entities = intent.get("entities", {})
            topic = entities.get("agent") or entities.get("module") or "system"
            return self.response_formatter.format_explain(topic)
        
        return "I didn't understand that. Type 'help' for available commands."
    
    def _execute_agent_call(self, routing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute an agent call based on routing.
        
        Args:
            routing: Routing result dictionary
        
        Returns:
            Agent output dictionary or None if error
        """
        agent_name = routing.get("agent")
        method = routing.get("method")
        payload = routing.get("payload", {})
        
        try:
            # Lazy load and call agent
            if agent_name == "architect":
                if self._architect_agent is None:
                    from agents.architect import ArchitectAgent
                    self._architect_agent = ArchitectAgent(agent_id="persona_architect", log_level=30)
                
                if method == "plan":
                    return self._architect_agent.plan(payload.get("goal", ""))
                elif method == "get_status":
                    return self._architect_agent.get_status()
            
            elif agent_name == "system_designer":
                if self._system_designer_agent is None:
                    from agents.system_designer import SystemDesignerAgent
                    self._system_designer_agent = SystemDesignerAgent(agent_id="persona_system_designer", log_level=30)
                
                if method == "design":
                    return self._system_designer_agent.design(payload.get("goal", ""))
            
            elif agent_name == "builder":
                if self._builder_agent is None:
                    from agents.builder import BuilderAgent
                    self._builder_agent = BuilderAgent(agent_id="persona_builder", log_level=30)
                
                if method == "build":
                    return self._builder_agent.build(payload)
            
            elif agent_name == "integrator":
                if self._integrator_agent is None:
                    from agents.integrator import IntegratorAgent
                    self._integrator_agent = IntegratorAgent(agent_id="persona_integrator", log_level=30)
                
                if method == "integrate":
                    return self._integrator_agent.integrate(payload)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error executing agent call: {str(e)}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status and session info.
        
        Returns:
            Dictionary with agent status and session information
        """
        return {
            "agent_id": self.agent_id,
            "state": self.context.get_state(),
            "session": self.session_manager.get_session_info()
        }
    
    def set_verbose(self, verbose: bool) -> None:
        """
        Set verbose output mode.
        
        Args:
            verbose: Whether to use verbose output
        """
        self.response_formatter.set_verbose(verbose)

