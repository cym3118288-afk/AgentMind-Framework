"""LLM provider abstraction layer for AgentMind.

This module provides a unified interface for different LLM providers,
enabling agents to work with various models (OpenAI, Claude, Ollama, etc.)
through a consistent API.
"""

from .provider import LLMProvider, LLMResponse, LLMMessage
from .ollama_provider import OllamaProvider
from .litellm_provider import LiteLLMProvider

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "LLMMessage",
    "OllamaProvider",
    "LiteLLMProvider",
]
