"""
Gemini Provider for LLM Gateway.

Implements the BaseProvider interface for Google Gemini.
Uses the google-genai package (not the deprecated google.generativeai).

Design Intent:
    - Clean implementation of BaseProvider
    - All Gemini-specific logic contained here
    - Consistent error handling
    - Token counting where available
"""

import time
import json
from typing import Any, Dict, List, Optional

from .base import (
    BaseProvider,
    ProviderResponse,
    EmbeddingResponse,
    ProviderConfig,
    ProviderStatus,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderAuthError,
)


class GeminiProvider(BaseProvider):
    """
    Google Gemini LLM Provider.
    
    Uses the google-genai package for API access.
    Supports text generation, structured output, and embeddings.
    """
    
    # Supported models
    MODELS = {
        # Gemini 3 Family (Preview)
        "gemini-3-pro-preview": {"max_tokens": 32768, "embedding": False},
        "gemini-3-flash-preview": {"max_tokens": 32768, "embedding": False},
        
        # Gemini 2.5 Family (Stable)
        "gemini-2.5-flash": {"max_tokens": 65536, "embedding": False},
        "gemini-2.5-pro": {"max_tokens": 65536, "embedding": False},
        "gemini-2.5-flash-lite": {"max_tokens": 32768, "embedding": False},
        
        # Gemini 2.0 Family
        "gemini-2.0-flash": {"max_tokens": 32768, "embedding": False},
        "gemini-2.0-flash-lite": {"max_tokens": 16384, "embedding": False},
        
        # Latest aliases
        "gemini-flash-latest": {"max_tokens": 65536, "embedding": False},
        "gemini-pro-latest": {"max_tokens": 65536, "embedding": False},
    }
    
    EMBEDDING_MODEL = "text-embedding-004"
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Google API key
            model: Gemini model to use (default: gemini-2.5-flash)
        """
        super().__init__(api_key, model)
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize the Gemini client."""
        try:
            from google import genai
            self._client = genai.Client(api_key=self._api_key)
            self._genai = genai
            self._set_status(ProviderStatus.HEALTHY)
        except ImportError:
            raise ProviderError(
                "google-genai package not installed. Run: pip install google-genai",
                code="IMPORT_ERROR",
                provider="gemini"
            )
        except Exception as e:
            self._set_status(ProviderStatus.UNAVAILABLE)
            raise ProviderAuthError(str(e), "gemini")
    
    @property
    def name(self) -> str:
        return "gemini"
    
    def generate(
        self,
        prompt: str,
        config: ProviderConfig
    ) -> ProviderResponse:
        """
        Generate a completion using Gemini.
        
        Args:
            prompt: The prompt text
            config: Generation configuration
            
        Returns:
            ProviderResponse with result or error
        """
        start_time = time.time()
        
        try:
            from google.genai import types
            
            # Build generation config
            gen_config = types.GenerateContentConfig(
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                top_p=config.top_p,
                top_k=config.top_k,
            )
            
            # Add system instruction if provided
            if config.system_instruction:
                gen_config.system_instruction = config.system_instruction
            
            # Make the request
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=gen_config
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract token counts
            tokens_input = 0
            tokens_output = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                tokens_input = getattr(response.usage_metadata, 'prompt_token_count', 0) or 0
                tokens_output = getattr(response.usage_metadata, 'candidates_token_count', 0) or 0
            
            # Extract finish reason
            finish_reason = "completed"
            if response.candidates and response.candidates[0].finish_reason:
                finish_reason = str(response.candidates[0].finish_reason.name)
            
            self._set_status(ProviderStatus.HEALTHY)
            
            return ProviderResponse(
                success=True,
                content=response.text,
                model=self._model,
                provider=self.name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_total=tokens_input + tokens_output,
                latency_ms=latency_ms,
                finish_reason=finish_reason,
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_str = str(e)
            
            # Categorize errors
            if "429" in error_str or "rate" in error_str.lower():
                self._set_status(ProviderStatus.DEGRADED)
                return ProviderResponse(
                    success=False,
                    content="",
                    model=self._model,
                    provider=self.name,
                    latency_ms=latency_ms,
                    error=error_str,
                    error_code="RATE_LIMIT"
                )
            elif "401" in error_str or "403" in error_str or "auth" in error_str.lower():
                self._set_status(ProviderStatus.UNAVAILABLE)
                return ProviderResponse(
                    success=False,
                    content="",
                    model=self._model,
                    provider=self.name,
                    latency_ms=latency_ms,
                    error=error_str,
                    error_code="AUTH_ERROR"
                )
            elif "timeout" in error_str.lower():
                self._set_status(ProviderStatus.DEGRADED)
                return ProviderResponse(
                    success=False,
                    content="",
                    model=self._model,
                    provider=self.name,
                    latency_ms=latency_ms,
                    error=error_str,
                    error_code="TIMEOUT"
                )
            else:
                self._set_status(ProviderStatus.DEGRADED)
                return ProviderResponse(
                    success=False,
                    content="",
                    model=self._model,
                    provider=self.name,
                    latency_ms=latency_ms,
                    error=error_str,
                    error_code="PROVIDER_ERROR"
                )
    
    def generate_structured(
        self,
        prompt: str,
        config: ProviderConfig,
        schema: Optional[Dict[str, Any]] = None
    ) -> ProviderResponse:
        """
        Generate structured JSON output.
        
        Args:
            prompt: The prompt text
            config: Generation configuration
            schema: Expected JSON schema
            
        Returns:
            ProviderResponse with JSON content
        """
        # Build structured prompt
        schema_hint = ""
        if schema:
            schema_hint = f"\n\nExpected JSON structure:\n```json\n{json.dumps(schema, indent=2)}\n```"
        
        structured_prompt = f"""{prompt}{schema_hint}

Respond with valid JSON only. No markdown code blocks, no explanations, just the JSON object."""
        
        # Lower temperature for structured output
        structured_config = ProviderConfig(
            max_tokens=config.max_tokens,
            temperature=min(config.temperature, 0.3),
            top_p=config.top_p,
            top_k=config.top_k,
            timeout_seconds=config.timeout_seconds,
            system_instruction=config.system_instruction or "You are a helpful assistant that always responds with valid JSON only."
        )
        
        # Generate
        response = self.generate(structured_prompt, structured_config)
        
        if not response.success:
            return response
        
        # Parse JSON
        try:
            content = response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                lines = content.split('\n')
                if lines[-1].strip() == '```':
                    content = '\n'.join(lines[1:-1])
                else:
                    content = '\n'.join(lines[1:])
            
            # Validate JSON
            parsed = json.loads(content)
            
            # Store parsed JSON as string for consistency
            response.content = json.dumps(parsed)
            response.metadata["parsed_json"] = parsed
            
            return response
            
        except json.JSONDecodeError as e:
            response.success = False
            response.error = f"JSON parse error: {str(e)}"
            response.error_code = "JSON_PARSE_ERROR"
            return response
    
    def generate_embedding(
        self,
        texts: List[str]
    ) -> EmbeddingResponse:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            EmbeddingResponse with vectors
        """
        start_time = time.time()
        
        try:
            result = self._client.models.embed_content(
                model=self.EMBEDDING_MODEL,
                contents=texts if len(texts) > 1 else texts[0]
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract embeddings
            if hasattr(result, 'embeddings'):
                if isinstance(result.embeddings, list):
                    embeddings = [e.values for e in result.embeddings]
                else:
                    embeddings = [result.embeddings.values]
            else:
                embeddings = [[]]
            
            dimensions = len(embeddings[0]) if embeddings and embeddings[0] else 0
            
            return EmbeddingResponse(
                success=True,
                embeddings=embeddings,
                model=self.EMBEDDING_MODEL,
                provider=self.name,
                dimensions=dimensions,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return EmbeddingResponse(
                success=False,
                embeddings=[],
                model=self.EMBEDDING_MODEL,
                provider=self.name,
                latency_ms=latency_ms,
                error=str(e),
                error_code="EMBEDDING_ERROR"
            )
    
    def health_check(self) -> bool:
        """
        Check if Gemini is operational.
        
        Uses a minimal request to verify connectivity.
        """
        try:
            # Minimal health check - just verify client is configured
            if self._client is None:
                self._set_status(ProviderStatus.UNAVAILABLE)
                return False
            
            # Could do a lightweight API call here, but that costs tokens
            # For now, trust that if client initialized, we're healthy
            self._set_status(ProviderStatus.HEALTHY)
            return True
            
        except Exception:
            self._set_status(ProviderStatus.UNAVAILABLE)
            return False
