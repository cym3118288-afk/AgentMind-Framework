"""Base plugin interface and types."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PluginType(str, Enum):
    """Types of plugins supported by AgentMind."""

    TOOL = "tool"
    INTEGRATION = "integration"
    MEMORY = "memory"
    LLM_PROVIDER = "llm_provider"
    ORCHESTRATION = "orchestration"
    MIDDLEWARE = "middleware"
    UI = "ui"


class PluginMetadata(BaseModel):
    """Metadata for a plugin."""

    name: str = Field(..., description="Plugin name")
    version: str = Field(..., description="Plugin version")
    description: str = Field(..., description="Plugin description")
    author: str = Field(..., description="Plugin author")
    plugin_type: PluginType = Field(..., description="Type of plugin")
    dependencies: List[str] = Field(default_factory=list, description="Required dependencies")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="Configuration schema")
    tags: List[str] = Field(default_factory=list, description="Plugin tags")
    homepage: Optional[str] = Field(None, description="Plugin homepage URL")
    license: Optional[str] = Field(None, description="Plugin license")


class PluginConfig(BaseModel):
    """Base configuration for plugins."""

    enabled: bool = Field(default=True, description="Whether plugin is enabled")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Plugin-specific settings")


class Plugin(ABC):
    """Base class for all AgentMind plugins."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize plugin with configuration.

        Args:
            config: Plugin configuration dictionary
        """
        self.config = config or {}
        self._initialized = False

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata.

        Returns:
            Plugin metadata
        """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the plugin.

        Called when the plugin is loaded. Use this to set up
        connections, load resources, etc.
        """

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the plugin.

        Called when the plugin is unloaded. Use this to clean up
        resources, close connections, etc.
        """

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if valid, False otherwise
        """
        metadata = self.get_metadata()
        if metadata.config_schema is None:
            return True

        # Basic validation - can be extended with jsonschema
        required_keys = metadata.config_schema.get("required", [])
        return all(key in config for key in required_keys)

    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized

    def __repr__(self) -> str:
        """String representation of plugin."""
        metadata = self.get_metadata()
        return f"<Plugin: {metadata.name} v{metadata.version}>"


class ToolPlugin(Plugin):
    """Base class for tool plugins."""

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool.

        Args:
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """

    @abstractmethod
    def get_tool_definition(self) -> Dict[str, Any]:
        """Get tool definition for LLM function calling.

        Returns:
            Tool definition dictionary
        """


class IntegrationPlugin(Plugin):
    """Base class for integration plugins."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to external service."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from external service."""

    @abstractmethod
    async def send_message(self, message: str, **kwargs) -> Any:
        """Send message to external service.

        Args:
            message: Message to send
            **kwargs: Additional parameters

        Returns:
            Response from service
        """


class MemoryPlugin(Plugin):
    """Base class for memory backend plugins."""

    @abstractmethod
    async def store(self, key: str, value: Any) -> None:
        """Store value in memory.

        Args:
            key: Storage key
            value: Value to store
        """

    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from memory.

        Args:
            key: Storage key

        Returns:
            Retrieved value or None
        """

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from memory.

        Args:
            key: Storage key
        """

    @abstractmethod
    async def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        """List all keys matching pattern.

        Args:
            pattern: Optional pattern to match

        Returns:
            List of matching keys
        """


class LLMProviderPlugin(Plugin):
    """Base class for LLM provider plugins."""

    @abstractmethod
    async def generate(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """Generate response from LLM.

        Args:
            messages: List of messages
            **kwargs: Generation parameters

        Returns:
            Generated text
        """

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Check if provider supports streaming."""

    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name."""


class OrchestrationPlugin(Plugin):
    """Base class for orchestration strategy plugins."""

    @abstractmethod
    async def orchestrate(self, agents: List[Any], task: str, **kwargs) -> Any:
        """Orchestrate agent collaboration.

        Args:
            agents: List of agents
            task: Task to accomplish
            **kwargs: Additional parameters

        Returns:
            Orchestration result
        """


class MiddlewarePlugin(Plugin):
    """Base class for middleware plugins."""

    @abstractmethod
    async def before_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process request before agent execution.

        Args:
            context: Request context

        Returns:
            Modified context
        """

    @abstractmethod
    async def after_response(self, context: Dict[str, Any], response: Any) -> Any:
        """Process response after agent execution.

        Args:
            context: Request context
            response: Agent response

        Returns:
            Modified response
        """


class UIPlugin(Plugin):
    """Base class for UI plugins."""

    @abstractmethod
    def get_routes(self) -> List[Dict[str, Any]]:
        """Get UI routes.

        Returns:
            List of route definitions
        """

    @abstractmethod
    def get_static_files(self) -> Optional[str]:
        """Get path to static files directory.

        Returns:
            Path to static files or None
        """

    @abstractmethod
    def get_templates(self) -> Optional[str]:
        """Get path to templates directory.

        Returns:
            Path to templates or None
        """
