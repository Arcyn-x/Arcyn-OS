"""
Intent Classifier module for Persona Agent.

Classifies user input into intents and extracts entities.
Uses rule-based classification first, falls back to LLM for complex queries.
"""

import re
from typing import Dict, Any, List, Tuple, Optional


class IntentClassifier:
    """
    Classifies user input into system intents.
    
    Responsibilities:
    - Classify user input into intents (build, design, integrate, status, explain, help)
    - Extract entities (modules, agents, goals)
    - Use LLM for ambiguous or complex queries
    
    Strategy:
    1. Try rule-based classification first (fast, deterministic)
    2. If confidence is low, use LLM for better classification
    
    All LLM calls route through the central gateway.
    """
    
    # Confidence threshold for using LLM
    LLM_THRESHOLD = 0.5
    
    def __init__(self, agent_name: str = "Persona"):
        """
        Initialize the intent classifier.
        
        Args:
            agent_name: Agent identifier for gateway routing
        """
        self.agent_name = agent_name
        self.intent_patterns = self._load_intent_patterns()
        self.entity_patterns = self._load_entity_patterns()
        self._use_llm = True  # Enable LLM fallback
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """
        Load intent classification patterns.
        
        Returns:
            Dictionary mapping intents to pattern lists
        """
        return {
            "build": [
                r"\bbuild\b", r"\bcreate\b", r"\bwrite\b", r"\bgenerate\b",
                r"\bmake\b", r"\bscaffold\b", r"\bimplement\b"
            ],
            "design": [
                r"\bdesign\b", r"\barchitecture\b", r"\bplan\b", r"\bstructure\b",
                r"\bschema\b", r"\blayout\b"
            ],
            "integrate": [
                r"\bintegrate\b", r"\bvalidate\b", r"\bcheck\b", r"\bverify\b",
                r"\bapprove\b", r"\bblock\b"
            ],
            "status": [
                r"\bstatus\b", r"\bstate\b", r"\bprogress\b", r"\bcheck\b",
                r"\bwhat\b.*\bstatus\b", r"\bhow\b.*\bgoing\b"
            ],
            "explain": [
                r"\bexplain\b", r"\bwhat\b.*\bis\b", r"\bdescribe\b", r"\btell\b.*\babout\b",
                r"\bhow\b.*\bworks\b", r"\bshow\b.*\bme\b"
            ],
            "help": [
                r"\bhelp\b", r"\bcommands\b", r"\bwhat\b.*\bcan\b", r"\bhow\b.*\bto\b",
                r"\bguide\b", r"\bmanual\b"
            ]
        }
    
    def _load_entity_patterns(self) -> Dict[str, List[str]]:
        """
        Load entity extraction patterns.
        
        Returns:
            Dictionary mapping entity types to pattern lists
        """
        return {
            "module": [
                r"\bmodule\s+(\w+)", r"\b(\w+)\s+module", r"modules?/(\w+)"
            ],
            "agent": [
                r"\bagent\s+(\w+)", r"\b(\w+)\s+agent", r"agents?/(\w+)"
            ],
            "goal": [
                r"goal[:\s]+(.+)", r"design[:\s]+(.+)", r"build[:\s]+(.+)",
                r"create[:\s]+(.+)", r'"([^"]+)"', r"'([^']+)'"
            ],
            "file": [
                r"file[:\s]+([^\s]+)", r"path[:\s]+([^\s]+)", r"([^\s]+\.py)"
            ]
        }
    
    def classify(self, user_input: str, task_id: str = "classify") -> Dict[str, Any]:
        """
        Classify user input into intent and extract entities.
        
        Args:
            user_input: User's natural language input
            task_id: Task identifier for tracking
        
        Returns:
            Dictionary containing:
            {
                "intent": str,
                "entities": Dict[str, Any],
                "confidence": float,
                "assumptions": List[str],
                "missing_info": List[str],
                "clarification_required": bool,
                "clarification_prompt": Optional[str]
            }
        """
        # Try rule-based first
        result = self._classify_rule_based(user_input)
        
        # If confidence is low and LLM is enabled, use LLM
        if result["confidence"] < self.LLM_THRESHOLD and self._use_llm:
            llm_result = self._classify_with_llm(user_input, task_id)
            if llm_result:
                return llm_result
        
        return result
    
    def _classify_rule_based(self, user_input: str) -> Dict[str, Any]:
        """
        Rule-based classification.
        
        Args:
            user_input: User's input text
        
        Returns:
            Classification result dictionary
        """
        user_input_lower = user_input.lower().strip()
        
        # Classify intent
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, user_input_lower, re.IGNORECASE))
                score += matches
            if score > 0:
                intent_scores[intent] = score
        
        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(1.0, intent_scores[primary_intent] / 3.0)
        else:
            primary_intent = "help"
            confidence = 0.1
        
        # Extract entities
        entities = self._extract_entities(user_input)
        
        return {
            "intent": primary_intent,
            "entities": entities,
            "confidence": confidence,
            "assumptions": [],
            "missing_info": [],
            "clarification_required": confidence < 0.3,
            "clarification_prompt": "Could you be more specific about what you want?" if confidence < 0.3 else None,
            "raw_input": user_input,
            "source": "rule_based"
        }
    
    def _classify_with_llm(self, user_input: str, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Classify using LLM (via gateway).
        
        Args:
            user_input: User's input text
            task_id: Task identifier for tracking
        
        Returns:
            Classification result or None if LLM fails
        """
        try:
            from core.llm_gateway import request_structured
            
            prompt = f"""You are the Persona Agent (S-1) of Arcyn OS.

Analyze this user input and classify the intent:

User Input: "{user_input}"

Determine:
1. Primary intent (build, design, integrate, status, explain, help, unknown)
2. Confidence level (0.0 to 1.0)
3. Extracted entities (modules, agents, files, goals mentioned)
4. Assumptions you're making
5. Missing information needed

Output JSON:
{{
  "intent": "build|design|integrate|status|explain|help|unknown",
  "confidence": 0.85,
  "entities": {{
    "goal": "...",
    "module": null,
    "agent": null
  }},
  "assumptions": ["..."],
  "missing_info": ["..."],
  "clarification_required": false,
  "clarification_prompt": null
}}"""
            
            response = request_structured(
                agent=self.agent_name,
                task_id=task_id,
                prompt=prompt,
                schema={
                    "intent": "",
                    "confidence": 0.0,
                    "entities": {},
                    "assumptions": [],
                    "missing_info": []
                },
                config={"max_tokens": 500, "temperature": 0.3}
            )
            
            if response.success and response.parsed_json:
                result = response.parsed_json
                result["raw_input"] = user_input
                result["source"] = "llm"
                return result
            
            return None
            
        except Exception:
            return None
    
    def _extract_entities(self, user_input: str) -> Dict[str, Any]:
        """
        Extract entities from user input.
        
        Args:
            user_input: User's input text
        
        Returns:
            Dictionary of extracted entities
        """
        entities = {
            "module": None,
            "agent": None,
            "goal": None,
            "file": None
        }
        
        # Extract modules
        for pattern in self.entity_patterns["module"]:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                entities["module"] = match.group(1) if match.groups() else match.group(0)
                break
        
        # Extract agents
        for pattern in self.entity_patterns["agent"]:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                entities["agent"] = match.group(1) if match.groups() else match.group(0)
                break
        
        # Extract goals (longer text)
        goal_candidates = []
        for pattern in self.entity_patterns["goal"]:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            goal_candidates.extend(matches)
        
        if goal_candidates:
            entities["goal"] = max(goal_candidates, key=len).strip()
        
        # Extract file paths
        for pattern in self.entity_patterns["file"]:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                entities["file"] = match.group(1) if match.groups() else match.group(0)
                break
        
        # Clean up None values
        entities = {k: v for k, v in entities.items() if v is not None}
        
        return entities
    
    def get_intent_description(self, intent: str) -> str:
        """
        Get a human-readable description of an intent.
        
        Args:
            intent: Intent name
        
        Returns:
            Description string
        """
        descriptions = {
            "build": "Create or scaffold code files",
            "design": "Design system architecture",
            "integrate": "Validate and integrate agent outputs",
            "status": "Check system or agent status",
            "explain": "Explain system components or concepts",
            "help": "Get help or list available commands"
        }
        return descriptions.get(intent, "Unknown intent")
    
    def enable_llm(self) -> None:
        """Enable LLM fallback for complex queries."""
        self._use_llm = True
    
    def disable_llm(self) -> None:
        """Disable LLM fallback (rule-based only)."""
        self._use_llm = False
