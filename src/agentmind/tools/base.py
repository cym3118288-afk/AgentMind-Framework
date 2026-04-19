"""Tool system for AgentMind agents.

This module provides a flexible tool system that allows agents to use
external functions and APIs during their reasoning process.
"""

import asyncio
import inspect
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, get_type_hints
from pydantic import BaseModel, Field, create_model

from ..core.types import ToolDefinition


class ToolResult(BaseModel):
    """Result from a tool execution.

    Attributes:
        success: Whether the tool executed successfully
        output: The tool's output (string or structured data)
        error: Error message if execution failed
        metadata: Additional metadata about the execution
    """

    success: bool = Field(..., description="Whether execution succeeded")
    output: Any = Field(default=None, description="Tool output")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Tool(ABC):
    """Abstract base class for tools.

    All tools must implement the execute method and provide metadata.
    """

    def __init__(self):
        self.name: str = self.__class__.__name__
        self.description: str = self.__doc__ or "No description provided"

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with execution outcome
        """
        pass

    def get_definition(self) -> ToolDefinition:
        """Get the tool definition for LLM function calling.

        Returns:
            ToolDefinition with name, description, and parameter schema
        """
        # Get the execute method signature
        sig = inspect.signature(self.execute)
        hints = get_type_hints(self.execute)

        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'kwargs'):
                continue

            param_type = hints.get(param_name, str)
            param_schema = self._type_to_schema(param_type)

            properties[param_name] = param_schema

            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        parameters = {
            "type": "object",
            "properties": properties
        }

        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=parameters,
            required=required
        )

    def _type_to_schema(self, python_type) -> Dict[str, Any]:
        """Convert Python type to JSON schema.

        Args:
            python_type: Python type annotation

        Returns:
            JSON schema dict
        """
        type_mapping = {
            str: {"type": "string"},
            int: {"type": "integer"},
            float: {"type": "number"},
            bool: {"type": "boolean"},
            list: {"type": "array"},
            dict: {"type": "object"},
        }

        return type_mapping.get(python_type, {"type": "string"})


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool.

        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """Get list of registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_definitions(self) -> List[ToolDefinition]:
        """Get definitions for all registered tools.

        Returns:
            List of ToolDefinition objects
        """
        return [tool.get_definition() for tool in self._tools.values()]

    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name.

        Args:
            name: Tool name
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution outcome
        """
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found"
            )

        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )

    async def execute_parallel(self, tool_calls: List[Dict[str, Any]]) -> List[ToolResult]:
        """Execute multiple tools in parallel.

        Args:
            tool_calls: List of dicts with 'name' and 'parameters' keys

        Returns:
            List of ToolResult objects
        """
        tasks = []
        for call in tool_calls:
            name = call.get('name')
            params = call.get('parameters', {})
            tasks.append(self.execute(name, **params))

        return await asyncio.gather(*tasks)


# Global tool registry
_global_registry = ToolRegistry()


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None
):
    """Decorator to convert a function into a tool.

    Args:
        name: Optional tool name (defaults to function name)
        description: Optional tool description (defaults to docstring)

    Returns:
        Decorated function that creates a Tool instance

    Example:
        @tool(name="calculator", description="Perform calculations")
        async def calculate(expression: str) -> ToolResult:
            result = eval(expression)
            return ToolResult(success=True, output=str(result))
    """
    def decorator(func: Callable) -> Tool:
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or "No description"

        # Create a Tool class dynamically
        class FunctionTool(Tool):
            def __init__(self):
                super().__init__()
                self.name = tool_name
                self.description = tool_description
                self._func = func

            async def execute(self, **kwargs) -> ToolResult:
                try:
                    if asyncio.iscoroutinefunction(self._func):
                        result = await self._func(**kwargs)
                    else:
                        result = self._func(**kwargs)

                    # If function returns ToolResult, use it directly
                    if isinstance(result, ToolResult):
                        return result

                    # Otherwise wrap the result
                    return ToolResult(success=True, output=result)
                except Exception as e:
                    return ToolResult(success=False, error=str(e))

            def get_definition(self) -> ToolDefinition:
                """Get the tool definition by inspecting the original function."""
                sig = inspect.signature(self._func)
                hints = get_type_hints(self._func)

                properties = {}
                required = []

                for param_name, param in sig.parameters.items():
                    if param_name in ('self', 'kwargs'):
                        continue

                    param_type = hints.get(param_name, str)
                    param_schema = self._type_to_schema(param_type)

                    properties[param_name] = param_schema

                    if param.default == inspect.Parameter.empty:
                        required.append(param_name)

                parameters = {
                    "type": "object",
                    "properties": properties
                }

                return ToolDefinition(
                    name=self.name,
                    description=self.description,
                    parameters=parameters,
                    required=required
                )

        tool_instance = FunctionTool()
        _global_registry.register(tool_instance)
        return tool_instance

    return decorator


def get_global_registry() -> ToolRegistry:
    """Get the global tool registry.

    Returns:
        Global ToolRegistry instance
    """
    return _global_registry
