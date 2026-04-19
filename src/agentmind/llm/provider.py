"""LLM Provider abstraction layer for AgentMind.

This module provides the abstract base class for LLM providers and common
types used across different provider implementations.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """Response from an LLM provider.

    Attributes:
        content: The generated text content
        model: The model that generated the response
        usage: Token usage information
        metadata: Additional provider-specific metadata
    """

    content: str = Field(..., description="Generated text content")
    model: str = Field(..., description="Model identifier")
    usage: Dict[str, int] = Field(
        default_factory=dict,
        description="Token usage (prompt_tokens, completion_tokens, total_tokens)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific metadata"
    )


class LLMMessage(BaseModel):
    """Message format for LLM conversations.

    Attributes:
        role: Message role (system, user, assistant)
        content: Message content
    """

    role: str = Field(..., description="Message role")
    content: str = Field(..., description="Message content")


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM providers (LiteLLM, Ollama, etc.) must implement this interface
    to ensure consistent behavior across different backends.
    """

    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any
    ) -> None:
        """Initialize the LLM provider.

        Args:
            model: Model identifier (e.g., "gpt-4", "llama3.2")
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse with generated content and metadata

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ):
        """Generate a streaming response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional generation parameters

        Yields:
            Chunks of generated text

        Raises:
            Exception: If generation fails
        """
        pass

    def build_messages(
        self,
        system_prompt: Optional[str] = None,
        user_message: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """Build a message list for the LLM.

        Args:
            system_prompt: Optional system prompt
            user_message: Optional user message
            history: Optional conversation history

        Returns:
            List of message dicts ready for generation
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if history:
            messages.extend(history)

        if user_message:
            messages.append({"role": "user", "content": user_message})

        return messages

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return (
            f"{self.__class__.__name__}(model='{self.model}', "
            f"temperature={self.temperature}, max_tokens={self.max_tokens})"
        )
