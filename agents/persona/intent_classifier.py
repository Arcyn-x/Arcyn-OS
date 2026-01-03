"""
Intent Classifier module for Persona Agent.

Classifies user input into intents and extracts entities.
"""

import re
from typing import Dict, Any, List, Tuple


class IntentClassifier:
    """
    Classifies user input into system intents.
    
    Responsibilities:
    - Classify user input into intents (build, design, integrate, status, explain, help)
    - Extract entities (modules, agents, goals)
    
    Rule-based first, LLM hooks later.
    
    TODO: Add LLM-based classification for complex queries
    TODO: Implement confidence scoring
    TODO: Add entity extraction improvements
    TODO: Support multi-intent detection
    """
    
    def __init__(self):
        """Initialize the intent classifier."""
        self.intent_patterns = self._load_intent_patterns()
        self.entity_patterns = self._load_entity_patterns()
    
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
    
    def classify(self, user_input: str) -> Dict[str, Any]:
        """
        Classify user input into intent and extract entities.
        
        Args:
            user_input: User's natural language input
        
        Returns:
            Dictionary containing:
            {
                "intent": str,
                "entities": Dict[str, Any],
                "confidence": float
            }
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
            confidence = min(1.0, intent_scores[primary_intent] / 3.0)  # Normalize confidence
        else:
            primary_intent = "help"  # Default to help if no intent detected
            confidence = 0.1
        
        # Extract entities
        entities = self._extract_entities(user_input)
        
        return {
            "intent": primary_intent,
            "entities": entities,
            "confidence": confidence,
            "raw_input": user_input
        }
    
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
            # Use the longest match as the goal
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

