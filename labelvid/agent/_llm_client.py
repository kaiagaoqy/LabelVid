"""LLM client supporting multiple providers (OpenAI, Gemini, Claude)."""

from __future__ import annotations

import enum
import os
from typing import Any

from loguru import logger


class LLMProvider(enum.Enum):
    """Supported LLM providers."""
    
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"


class LLMClient:
    """Universal LLM client supporting multiple providers."""
    
    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OPENAI,
        api_key: str | None = None,
        model: str | None = None,
    ):
        """Initialize LLM client.
        
        Args:
            provider: LLM provider to use
            api_key: API key (if None, will try to get from environment)
            model: Model name (if None, uses default for provider)
        """
        self.provider = provider
        self._api_key = api_key
        self._model = model or self._get_default_model()
        self._client = None
        
        # Get API key from environment if not provided
        if not self._api_key:
            self._api_key = self._get_api_key_from_env()
    
    def _get_default_model(self) -> str:
        """Get default model for the provider."""
        defaults = {
            LLMProvider.OPENAI: "gpt-4o-mini",  # Fast and cost-effective default
            LLMProvider.GEMINI: "gemini-1.5-flash",  # Fast and cost-effective default
            LLMProvider.CLAUDE: "claude-3-5-sonnet-20241022",  # Balanced default
        }
        return defaults.get(self.provider, "gpt-4o-mini")
    
    def _get_api_key_from_env(self) -> str | None:
        """Get API key from environment variables."""
        env_vars = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.GEMINI: "GEMINI_API_KEY",
            LLMProvider.CLAUDE: "ANTHROPIC_API_KEY",
        }
        var_name = env_vars.get(self.provider)
        if var_name:
            return os.environ.get(var_name)
        return None
    
    def _init_client(self):
        """Initialize the provider-specific client."""
        if self._client is not None:
            return self._client
        
        if not self._api_key:
            raise ValueError(
                f"API key not found for {self.provider.value}. "
                f"Set environment variable or provide api_key parameter."
            )
        
        if self.provider == LLMProvider.OPENAI:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._api_key)
                logger.info("Initialized OpenAI client with model: {}", self._model)
            except ImportError:
                raise ImportError(
                    "OpenAI package not found. Install with: pip install openai"
                )
        
        elif self.provider == LLMProvider.GEMINI:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._api_key)
                self._client = genai.GenerativeModel(self._model)
                logger.info("Initialized Gemini client with model: {}", self._model)
            except ImportError:
                raise ImportError(
                    "Google Generative AI package not found. "
                    "Install with: pip install google-generativeai"
                )
        
        elif self.provider == LLMProvider.CLAUDE:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self._api_key)
                logger.info("Initialized Claude client with model: {}", self._model)
            except ImportError:
                raise ImportError(
                    "Anthropic package not found. Install with: pip install anthropic"
                )
        
        return self._client
    
    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Send a chat request to the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            
        Returns:
            Response text from the LLM
        """
        client = self._init_client()
        
        try:
            if self.provider == LLMProvider.OPENAI:
                # GPT-5 and o1 models have different parameter requirements
                is_new_model = self._model.startswith("gpt-5") or self._model.startswith("o1")
                
                # Log request details
                logger.debug("OpenAI request - model: {}, max_tokens: {}, temperature: {}", 
                           self._model, max_tokens, temperature if not is_new_model else "default(1)")
                
                if is_new_model:
                    # New models: use max_completion_tokens, no custom temperature
                    response = client.chat.completions.create(
                        model=self._model,
                        messages=messages,
                        max_completion_tokens=max_tokens,
                        # temperature not supported, uses default (1)
                    )
                else:
                    # Older models: use max_tokens with custom temperature
                    response = client.chat.completions.create(
                        model=self._model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                
                # Log response details
                logger.debug("OpenAI response - finish_reason: {}, usage: {}", 
                           response.choices[0].finish_reason, response.usage)
                
                # Get response content
                content = response.choices[0].message.content
                if not content:
                    logger.warning("Empty response from OpenAI model: {}", self._model)
                    logger.debug("Response object: {}", response)
                    logger.error("Finish reason: {}, this usually means the model hit token limit or refused to respond", 
                               response.choices[0].finish_reason)
                    raise ValueError(f"Empty response from LLM (finish_reason: {response.choices[0].finish_reason})")
                
                logger.debug("OpenAI response content length: {} chars", len(content))
                return content
            
            elif self.provider == LLMProvider.GEMINI:
                # Convert messages to Gemini format
                prompt_parts = []
                for msg in messages:
                    role = "user" if msg["role"] == "user" else "model"
                    prompt_parts.append({"role": role, "parts": [msg["content"]]})
                
                response = client.generate_content(
                    prompt_parts,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    }
                )
                return response.text
            
            elif self.provider == LLMProvider.CLAUDE:
                # Extract system message if present
                system = None
                user_messages = []
                for msg in messages:
                    if msg["role"] == "system":
                        system = msg["content"]
                    else:
                        user_messages.append(msg)
                
                response = client.messages.create(
                    model=self._model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=user_messages,
                )
                return response.content[0].text
            
        except Exception as e:
            logger.error("LLM request failed: {}", e)
            raise
    
    def is_available(self) -> bool:
        """Check if the LLM client is available and configured."""
        try:
            self._init_client()
            return True
        except Exception as e:
            logger.debug("LLM not available: {}", e)
            return False
    
    @property
    def model_name(self) -> str:
        """Get the current model name."""
        return self._model
    
    @model_name.setter
    def model_name(self, value: str) -> None:
        """Set the model name."""
        self._model = value
        self._client = None  # Reset client to use new model
