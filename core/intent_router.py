"""
Intent Router for Arcyn OS Command Trigger.

Maps string commands to predefined intents using RULE-BASED matching.
No ML guessing, no fuzzy matching — explicit phrase detection only.

This router does not think — it classifies.

Supported Intents:
    - LOOP_TEST_REQUEST: Full system loop test prompt
    - AGENT_PROMPT_REQUEST: Specific agent prompt
    - SYSTEM_STATUS: System health/status check
    - ARCHITECTURE_EXPLANATION: Explain system architecture
    - EVOLUTION_CYCLE: Run evolution agent cycle
    - UNKNOWN_COMMAND: Fallback for unrecognized commands
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


class Intent(Enum):
    """Supported command intents."""
    LOOP_TEST_REQUEST = "loop_test_request"
    AGENT_PROMPT_REQUEST = "agent_prompt_request"
    SYSTEM_STATUS = "system_status"
    ARCHITECTURE_EXPLANATION = "architecture_explanation"
    EVOLUTION_CYCLE = "evolution_cycle"
    HELP_REQUEST = "help_request"
    UNKNOWN_COMMAND = "unknown_command"


@dataclass
class IntentMatch:
    """Result of intent classification."""
    intent: Intent
    confidence: str  # "exact", "partial", "fallback"
    matched_phrase: Optional[str]
    extracted_params: Dict[str, str]


class IntentRouter:
    """
    Rule-based intent router.
    
    Maps string commands to intents using explicit phrase matching.
    Deterministic behavior — same input always produces same output.
    
    Example:
        >>> router = IntentRouter()
        >>> result = router.classify("Give me the full Arcyn OS loop test prompt.")
        >>> result.intent
        Intent.LOOP_TEST_REQUEST
    
    Future Integration Points:
        # TODO: Voice trigger hook - classify(transcribed_text)
        # TODO: UI button hook - classify_from_action(button_id)
        # TODO: API endpoint hook - POST /api/command {text: "..."}
    """
    
    # Phrase patterns for each intent (priority order)
    INTENT_PATTERNS: Dict[Intent, List[str]] = {
        Intent.LOOP_TEST_REQUEST: [
            "full arcyn os loop test",
            "loop test prompt",
            "full loop test",
            "system loop test",
            "complete loop test",
            "arcyn loop test",
            "full system test prompt",
            "give me the loop test",
        ],
        Intent.AGENT_PROMPT_REQUEST: [
            "agent prompt",
            "build agent",
            "create agent",
            "agent template",
            "agent scaffold",
            "generate agent",
            "new agent prompt",
            "prompt for agent",
        ],
        Intent.SYSTEM_STATUS: [
            "system status",
            "health check",
            "system health",
            "status report",
            "how is the system",
            "check status",
            "arcyn status",
        ],
        Intent.ARCHITECTURE_EXPLANATION: [
            "explain architecture",
            "architecture explanation",
            "how does arcyn work",
            "system architecture",
            "explain the system",
            "how arcyn works",
            "describe architecture",
        ],
        Intent.EVOLUTION_CYCLE: [
            "run evolution",
            "evolution cycle",
            "analyze system",
            "system analysis",
            "run analysis",
            "evolution agent",
            "monitor system",
        ],
        Intent.HELP_REQUEST: [
            "help",
            "what can you do",
            "available commands",
            "list commands",
            "show commands",
            "command list",
        ],
    }
    
    # Agent name extraction patterns
    AGENT_NAMES = {
        "persona": ["persona", "s-1", "s1"],
        "architect": ["architect", "a-1", "a1"],
        "builder": ["builder", "b-1", "b1", "forge", "f-1", "f1"],
        "integrator": ["integrator", "i-1", "i1"],
        "knowledge": ["knowledge", "knowledge engine", "s-2", "s2"],
        "evolution": ["evolution", "s-3", "s3"],
        "system_designer": ["system designer", "designer", "d-1", "d1"],
    }
    
    def __init__(self):
        """Initialize the intent router."""
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Pre-compile patterns for faster matching."""
        # Lowercase all patterns for case-insensitive matching
        self._patterns = {
            intent: [p.lower() for p in phrases]
            for intent, phrases in self.INTENT_PATTERNS.items()
        }
    
    def classify(self, command: str) -> IntentMatch:
        """
        Classify a command string into an intent.
        
        Args:
            command: Natural language command string
            
        Returns:
            IntentMatch with intent, confidence, and extracted params
        """
        if not command or not command.strip():
            return IntentMatch(
                intent=Intent.UNKNOWN_COMMAND,
                confidence="fallback",
                matched_phrase=None,
                extracted_params={}
            )
        
        # Normalize input
        normalized = command.lower().strip()
        
        # Check each intent's patterns (priority order)
        for intent, phrases in self._patterns.items():
            for phrase in phrases:
                if phrase in normalized:
                    # Extract additional parameters
                    params = self._extract_params(normalized, intent)
                    
                    return IntentMatch(
                        intent=intent,
                        confidence="exact",
                        matched_phrase=phrase,
                        extracted_params=params
                    )
        
        # Fallback to unknown
        return IntentMatch(
            intent=Intent.UNKNOWN_COMMAND,
            confidence="fallback",
            matched_phrase=None,
            extracted_params={}
        )
    
    def _extract_params(self, normalized: str, intent: Intent) -> Dict[str, str]:
        """Extract parameters based on intent type."""
        params = {}
        
        if intent == Intent.AGENT_PROMPT_REQUEST:
            # Try to extract agent name
            for agent_key, aliases in self.AGENT_NAMES.items():
                for alias in aliases:
                    if alias in normalized:
                        params["agent_name"] = agent_key
                        break
                if "agent_name" in params:
                    break
        
        return params
    
    def get_supported_intents(self) -> List[str]:
        """Return list of supported intent names."""
        return [intent.value for intent in Intent if intent != Intent.UNKNOWN_COMMAND]
    
    def get_example_phrases(self, intent: Intent) -> List[str]:
        """Get example phrases for an intent."""
        return self.INTENT_PATTERNS.get(intent, [])
