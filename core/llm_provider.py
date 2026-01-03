"""
LLM Provider for Arcyn OS.

Provides a unified interface to Large Language Models for all agents.
Primary provider: Google Gemini (using google-genai package)

This module handles:
- LLM API connections
- Prompt formatting
- Structured output parsing
- Rate limiting and error handling
- Response caching (optional)

Configuration:
    Set GEMINI_API_KEY environment variable or pass directly.

Example:
    from core.llm_provider import LLMProvider
    
    llm = LLMProvider()
    response = llm.complete("Explain Python decorators")
    
    # Structured output
    result = llm.structured_output(
        "Plan a REST API project",
        schema={"milestones": [], "tasks": []}
    )
"""

import os
import json
import time
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Load .env file automatically
try:
    from dotenv import load_dotenv
    # Look for .env in project root
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()  # Try current directory
except ImportError:
    pass  # python-dotenv not installed, rely on system env vars


class LLMModel(Enum):
    """Available Gemini models (2026)."""
    # Gemini 3 Family (Preview)
    GEMINI_3_PRO_PREVIEW = "gemini-3-pro-preview"
    GEMINI_3_FLASH_PREVIEW = "gemini-3-flash-preview"
    
    # Gemini 2.5 Family (Stable)
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"
    
    # Gemini 2.0 Family
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_0_FLASH_LITE = "gemini-2.0-flash-lite"
    
    # Latest aliases (auto-updated by Google)
    GEMINI_FLASH_LATEST = "gemini-flash-latest"
    GEMINI_PRO_LATEST = "gemini-pro-latest"


@dataclass
class LLMResponse:
    """Structured response from LLM."""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    raw_response: Any


class LLMProvider:
    """
    Unified LLM provider interface for Arcyn OS.
    
    Uses Google Gemini as the primary provider (google-genai package).
    Designed to be extended for other providers (OpenAI, Anthropic, etc.)
    
    Example:
        >>> llm = LLMProvider()
        >>> response = llm.complete("What is Python?")
        >>> print(response.content)
    
    Attributes:
        model: The Gemini model to use
        api_key: Google API key
        temperature: Sampling temperature (0.0 - 1.0)
        max_tokens: Maximum tokens in response
    """
    
    DEFAULT_MODEL = LLMModel.GEMINI_2_5_FLASH
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 8192
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Union[str, LLMModel] = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout: int = 60
    ):
        """
        Initialize the LLM provider.
        
        Args:
            api_key: Gemini API key (uses GEMINI_API_KEY env var if not provided)
            model: Model to use (default: gemini-2.5-flash)
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Model configuration
        if isinstance(model, LLMModel):
            self.model = model.value
        else:
            self.model = model
        
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # Initialize the Gemini client
        self._init_client()
        
        # Logging
        self.logger = logging.getLogger("LLMProvider")
        
        # Statistics
        self._request_count = 0
        self._total_tokens = 0
        self._last_request_time = 0
    
    def _init_client(self):
        """Initialize the Gemini client using google-genai package."""
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            self._genai = genai
        except ImportError:
            raise ImportError(
                "google-genai package not installed. "
                "Run: pip install google-genai"
            )
    
    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.
        
        Args:
            prompt: The user prompt
            system: Optional system instruction
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            LLMResponse with content and metadata
        """
        from google.genai import types
        
        # Build config
        config = types.GenerateContentConfig(
            temperature=temperature or self.temperature,
            max_output_tokens=max_tokens or self.max_tokens,
        )
        
        # Add system instruction if provided
        if system:
            config.system_instruction = system
        
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
            
            # Track statistics
            self._request_count += 1
            self._last_request_time = time.time()
            
            # Extract token count if available
            tokens = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                tokens = getattr(response.usage_metadata, 'total_token_count', 0)
            self._total_tokens += tokens
            
            # Get finish reason
            finish_reason = "completed"
            if response.candidates and response.candidates[0].finish_reason:
                finish_reason = str(response.candidates[0].finish_reason)
            
            return LLMResponse(
                content=response.text,
                model=self.model,
                tokens_used=tokens,
                finish_reason=finish_reason,
                raw_response=response
            )
            
        except Exception as e:
            self.logger.error(f"LLM request failed: {str(e)}")
            raise LLMError(f"Gemini API error: {str(e)}") from e
    
    def structured_output(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        retries: int = 2
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output from the LLM.
        
        Args:
            prompt: The user prompt
            schema: Expected output schema (for validation hints)
            system: Optional system instruction
            retries: Number of retries on parse failure
            
        Returns:
            Parsed JSON dictionary
        """
        # Build structured prompt
        schema_hint = ""
        if schema:
            schema_hint = f"\n\nExpected JSON structure:\n```json\n{json.dumps(schema, indent=2)}\n```"
        
        structured_prompt = f"""{prompt}{schema_hint}

Respond with valid JSON only. No markdown, no explanations, just the JSON object."""
        
        system_instruction = system or "You are a helpful assistant that always responds with valid JSON."
        
        for attempt in range(retries + 1):
            try:
                response = self.complete(
                    prompt=structured_prompt,
                    system=system_instruction,
                    temperature=0.3  # Lower temperature for structured output
                )
                
                # Parse JSON from response
                content = response.content.strip()
                
                # Remove markdown code blocks if present
                if content.startswith("```"):
                    lines = content.split('\n')
                    # Remove first line (```json) and last line (```)
                    if lines[-1].strip() == '```':
                        content = '\n'.join(lines[1:-1])
                    else:
                        content = '\n'.join(lines[1:])
                
                return json.loads(content)
                
            except json.JSONDecodeError as e:
                if attempt < retries:
                    self.logger.warning(f"JSON parse failed, retrying ({attempt + 1}/{retries})")
                    continue
                raise LLMError(f"Failed to parse JSON after {retries} retries: {str(e)}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None
    ) -> LLMResponse:
        """
        Multi-turn chat completion.
        
        Args:
            messages: List of {"role": "user"|"model", "content": "..."}
            system: Optional system instruction
            
        Returns:
            LLMResponse with assistant's reply
        """
        from google.genai import types
        
        # Build contents
        contents = []
        for msg in messages:
            role = msg["role"]
            if role == "assistant":
                role = "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])]
            ))
        
        config = types.GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
        )
        
        if system:
            config.system_instruction = system
        
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )
            
            self._request_count += 1
            
            return LLMResponse(
                content=response.text,
                model=self.model,
                tokens_used=0,
                finish_reason="completed",
                raw_response=response
            )
        except Exception as e:
            self.logger.error(f"Chat request failed: {str(e)}")
            raise LLMError(f"Gemini API error: {str(e)}") from e
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            result = self._client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            return result.embeddings[0].values
        except Exception as e:
            self.logger.error(f"Embedding failed: {str(e)}")
            raise LLMError(f"Embedding error: {str(e)}") from e
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            result = self._client.models.embed_content(
                model="text-embedding-004",
                contents=texts
            )
            return [e.values for e in result.embeddings]
        except Exception as e:
            self.logger.error(f"Batch embedding failed: {str(e)}")
            # Fallback to individual embedding
            embeddings = []
            for text in texts:
                embeddings.append(self.embed(text))
            return embeddings
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "request_count": self._request_count,
            "total_tokens": self._total_tokens,
            "model": self.model,
            "last_request_time": self._last_request_time
        }


class LLMError(Exception):
    """Exception raised for LLM-related errors."""
    pass


# =============================================================================
# Agent-Specific Prompt Builders
# =============================================================================

class PromptBuilder:
    """
    Helper class for building agent-specific prompts.
    
    Each agent can use these templates for consistent prompting.
    """
    
    @staticmethod
    def architect_plan(goal: str, context: Optional[Dict] = None) -> str:
        """Build prompt for Architect planning."""
        context_str = ""
        if context:
            context_str = f"\nContext:\n{json.dumps(context, indent=2)}"
        
        return f"""You are the Architect Agent (A-1) of Arcyn OS.

Your task is to create a structured development plan for the following goal:

Goal: {goal}
{context_str}

Create a comprehensive plan that includes:
1. Technology decisions with reasoning (e.g., framework, database, auth method)
2. Rejected alternatives and why they were not chosen
3. Milestones (3-5) with descriptions
4. Tasks for each milestone with dependencies
5. Architectural constraints that Builders must follow
6. Open questions that need clarification

Output JSON with this structure:
{{
  "goal": "...",
  "decisions": {{
    "framework": {{"choice": "...", "reasoning": "..."}},
    "database": {{"choice": "...", "reasoning": "..."}}
  }},
  "rejected_options": [
    {{"category": "...", "option": "...", "reason": "..."}}
  ],
  "milestones": [
    {{"id": "M1", "name": "...", "description": "...", "tasks": ["T1", "T2"]}}
  ],
  "tasks": [
    {{"id": "T1", "name": "...", "description": "...", "milestone_id": "M1", "dependencies": [], "effort": "low|medium|high"}}
  ],
  "execution_order": ["T1", "T2", "..."],
  "architectural_constraints": ["..."],
  "open_questions": ["..."]
}}"""
    
    @staticmethod
    def builder_code(task: Dict[str, Any], context: Optional[Dict] = None) -> str:
        """Build prompt for Builder code generation."""
        context_str = ""
        if context:
            context_str = f"\nProject Context:\n{json.dumps(context, indent=2)}"
        
        return f"""You are the Builder Agent (F-1) of Arcyn OS.

Your task is to generate production-ready code for the following task:

Task: {task.get('name', 'Unknown')}
Description: {task.get('description', 'No description')}
{context_str}

Requirements:
1. Generate complete, runnable code
2. Include proper type hints
3. Include docstrings for all classes and functions
4. Follow PEP 8 style guidelines
5. Include error handling
6. Add TODO comments for future enhancements

Output JSON with this structure:
{{
  "files": [
    {{
      "path": "relative/path/to/file.py",
      "content": "# Full file content here..."
    }}
  ],
  "dependencies": ["package-name"],
  "notes": ["Any important notes about the implementation"]
}}"""
    
    @staticmethod
    def persona_classify(user_input: str) -> str:
        """Build prompt for Persona intent classification."""
        return f"""You are the Persona Agent (S-1) of Arcyn OS.

Analyze this user input and classify the intent:

User Input: "{user_input}"

Determine:
1. Primary intent (build, design, integrate, query, explain, help, unknown)
2. Confidence level (0.0 to 1.0)
3. Extracted entities (modules, agents, files, goals mentioned)
4. Assumptions you're making
5. Missing information needed
6. Risk flags (ambiguity, scope issues, etc.)

Output JSON:
{{
  "intent": "build|design|integrate|query|explain|help|unknown",
  "confidence": 0.85,
  "entities": {{
    "goal": "...",
    "module": null,
    "agent": null
  }},
  "assumptions": ["..."],
  "missing_info": ["..."],
  "risk_flags": [
    {{"flag": "...", "detail": "...", "mitigation": "..."}}
  ],
  "route_to": "architect_agent|builder_agent|...",
  "clarification_required": false,
  "clarification_prompt": null
}}"""
    
    @staticmethod
    def evolution_analyze(observation: Dict[str, Any]) -> str:
        """Build prompt for Evolution analysis."""
        return f"""You are the Evolution Agent (S-3) of Arcyn OS.

Analyze this system observation and provide strategic recommendations:

Observation:
{json.dumps(observation, indent=2)}

Provide a thorough analysis including:
1. Architectural risks and concerns
2. Performance inefficiencies
3. Scalability limits
4. Maintenance forecast
5. Strategic recommendations with priority and effort

Be critical and strategic, not just safe observations.

Output JSON:
{{
  "risks": [
    {{
      "component": "...",
      "issue": "...",
      "impact": "...",
      "recommendation": "...",
      "risk_level": "low|medium|high|critical",
      "effort_to_fix_now": "low|medium|high",
      "effort_to_fix_later": "low|medium|high"
    }}
  ],
  "inefficiencies": [...],
  "architectural_concerns": [...],
  "scalability_limits": [...],
  "maintenance_forecast": {{
    "6_months": "...",
    "12_months": "...",
    "risk_trajectory": "stable|increasing|decreasing"
  }},
  "suggested_changes": [
    {{
      "title": "...",
      "scope": "...",
      "risk": "low|medium|high",
      "effort": "low|medium|high",
      "priority": "low|medium|high",
      "rationale": "..."
    }}
  ],
  "priority": "low|medium|high",
  "confidence": 0.85
}}"""


# =============================================================================
# Convenience Functions
# =============================================================================

_default_provider: Optional[LLMProvider] = None


def get_llm(api_key: Optional[str] = None) -> LLMProvider:
    """
    Get or create the default LLM provider instance.
    
    Args:
        api_key: Optional API key override
        
    Returns:
        LLMProvider instance
    """
    global _default_provider
    if _default_provider is None or api_key:
        _default_provider = LLMProvider(api_key=api_key)
    return _default_provider


def complete(prompt: str, system: Optional[str] = None) -> str:
    """
    Quick completion using default provider.
    
    Args:
        prompt: The prompt
        system: Optional system instruction
        
    Returns:
        Response content string
    """
    return get_llm().complete(prompt, system).content


def structured(prompt: str, schema: Optional[Dict] = None) -> Dict:
    """
    Quick structured output using default provider.
    
    Args:
        prompt: The prompt
        schema: Optional expected schema
        
    Returns:
        Parsed JSON dictionary
    """
    return get_llm().structured_output(prompt, schema)
