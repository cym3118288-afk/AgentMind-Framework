"""Standardized plugin interfaces for AgentMind.

This module defines the core interfaces that all plugins must implement
to ensure compatibility with the AgentMind framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncIterator
from pydantic import BaseModel, Field

from ..core.types import Message


class LLMProvider(ABC):
    """Standard interface for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            Dict with 'content', 'model', 'usage', and 'metadata'
        """

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate a streaming response.

        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Yields:
            Text chunks
        """

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model.

        Returns:
            Dict with model name, capabilities, limits, etc.
        """


class MemoryBackend(ABC):
    """Standard interface for memory backends."""

    @abstractmethod
    async def store(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store a value in memory.

        Args:
            key: Storage key
            value: Value to store
            metadata: Optional metadata
        """

    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value from memory.

        Args:
            key: Storage key

        Returns:
            Retrieved value or None
        """

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search memory with semantic or keyword search.

        Args:
            query: Search query
            limit: Maximum results
            filters: Optional filters

        Returns:
            List of matching entries
        """

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from memory.

        Args:
            key: Storage key

        Returns:
            True if deleted, False if not found
        """

    @abstractmethod
    async def clear(self) -> None:
        """Clear all memory."""

    @abstractmethod
    async def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        """List all keys matching pattern.

        Args:
            pattern: Optional pattern to match

        Returns:
            List of matching keys
        """


class ToolRegistry(ABC):
    """Standard interface for tool registries."""

    @abstractmethod
    def register_tool(
        self,
        name: str,
        function: Any,
        description: str,
        parameters: Dict[str, Any],
    ) -> None:
        """Register a tool.

        Args:
            name: Tool name
            function: Tool function
            description: Tool description
            parameters: Parameter schema
        """

    @abstractmethod
    async def execute_tool(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a tool.

        Args:
            name: Tool name
            **kwargs: Tool parameters

        Returns:
            Execution result
        """

    @abstractmethod
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions.

        Returns:
            List of tool definitions
        """

    @abstractmethod
    def list_tools(self) -> List[str]:
        """List all registered tool names.

        Returns:
            List of tool names
        """


class Orchestrator(ABC):
    """Standard interface for orchestration strategies."""

    @abstractmethod
    async def orchestrate(
        self,
        agents: List[Any],
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Orchestrate agent collaboration.

        Args:
            agents: List of agents
            task: Task to accomplish
            context: Optional context
            **kwargs: Strategy-specific parameters

        Returns:
            Orchestration result
        """

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the strategy name.

        Returns:
            Strategy name
        """

    @abstractmethod
    def supports_parallel(self) -> bool:
        """Check if strategy supports parallel execution.

        Returns:
            True if parallel execution is supported
        """


class Observer(ABC):
    """Standard interface for observers/middleware."""

    @abstractmethod
    async def on_agent_start(self, agent_name: str, task: str, context: Dict[str, Any]) -> None:
        """Called when an agent starts processing.

        Args:
            agent_name: Agent name
            task: Task description
            context: Execution context
        """

    @abstractmethod
    async def on_agent_end(
        self,
        agent_name: str,
        result: Any,
        context: Dict[str, Any],
    ) -> None:
        """Called when an agent finishes processing.

        Args:
            agent_name: Agent name
            result: Agent result
            context: Execution context
        """

    @abstractmethod
    async def on_agent_error(
        self,
        agent_name: str,
        error: Exception,
        context: Dict[str, Any],
    ) -> None:
        """Called when an agent encounters an error.

        Args:
            agent_name: Agent name
            error: Exception that occurred
            context: Execution context
        """

    @abstractmethod
    async def on_message(self, message: Message, context: Dict[str, Any]) -> None:
        """Called when a message is sent.

        Args:
            message: Message object
            context: Execution context
        """


class PluginMetadata(BaseModel):
    """Metadata for a plugin."""

    name: str = Field(..., description="Plugin name")
    version: str = Field(..., description="Plugin version")
    description: str = Field(..., description="Plugin description")
    author: str = Field(..., description="Plugin author")
    plugin_type: str = Field(..., description="Plugin type")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies")
    homepage: Optional[str] = Field(None, description="Homepage URL")
    license: Optional[str] = Field(None, description="License")


class PluginInterface(ABC):
    """Base interface for all plugins."""

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata.

        Returns:
            Plugin metadata
        """

    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the plugin.

        Args:
            config: Optional configuration
        """

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the plugin."""

    @abstractmethod
    def health_check(self) -> bool:
        """Check if plugin is healthy.

        Returns:
            True if healthy
        """
