"""Custom exceptions for AgentMind framework.

This module provides clear, actionable error messages for common issues.
"""


class AgentMindError(Exception):
    """Base exception for all AgentMind errors."""


class AgentConfigError(AgentMindError):
    """Raised when agent configuration is invalid."""

    def __init__(self, message: str, agent_name: str = None):
        self.agent_name = agent_name
        if agent_name:
            message = f"Agent '{agent_name}': {message}"
        super().__init__(message)


class CollaborationError(AgentMindError):
    """Raised when collaboration fails or encounters issues."""

    def __init__(self, message: str, round_number: int = None):
        self.round_number = round_number
        if round_number:
            message = f"Round {round_number}: {message}"
        super().__init__(message)


class LLMProviderError(AgentMindError):
    """Raised when LLM provider encounters an error."""

    def __init__(self, message: str, provider_name: str = None, original_error: Exception = None):
        self.provider_name = provider_name
        self.original_error = original_error

        if provider_name:
            message = f"LLM Provider '{provider_name}': {message}"

        if original_error:
            message = f"{message}\nOriginal error: {str(original_error)}"

        super().__init__(message)


class ToolExecutionError(AgentMindError):
    """Raised when tool execution fails."""

    def __init__(self, message: str, tool_name: str = None, original_error: Exception = None):
        self.tool_name = tool_name
        self.original_error = original_error

        if tool_name:
            message = f"Tool '{tool_name}': {message}"

        if original_error:
            message = f"{message}\nOriginal error: {str(original_error)}"

        super().__init__(message)


class MemoryError(AgentMindError):
    """Raised when memory operations fail."""

    def __init__(self, message: str, backend: str = None):
        self.backend = backend
        if backend:
            message = f"Memory backend '{backend}': {message}"
        super().__init__(message)


class ValidationError(AgentMindError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str = None, value=None):
        self.field = field
        self.value = value

        if field:
            message = f"Validation failed for '{field}': {message}"
            if value is not None:
                message = f"{message} (got: {repr(value)})"

        super().__init__(message)


# Helper functions for common validation scenarios


def validate_agent_name(name: str) -> None:
    """Validate agent name.

    Args:
        name: Agent name to validate

    Raises:
        ValidationError: If name is invalid
    """
    if not name or not isinstance(name, str):
        raise ValidationError("Agent name must be a non-empty string", field="name", value=name)

    if not name.strip():
        raise ValidationError("Agent name cannot be only whitespace", field="name", value=name)

    if len(name) > 100:
        raise ValidationError("Agent name too long (max 100 characters)", field="name", value=name)


def validate_max_rounds(max_rounds: int) -> None:
    """Validate max_rounds parameter.

    Args:
        max_rounds: Maximum rounds to validate

    Raises:
        ValidationError: If max_rounds is invalid
    """
    if not isinstance(max_rounds, int):
        raise ValidationError("max_rounds must be an integer", field="max_rounds", value=max_rounds)

    if max_rounds < 1:
        raise ValidationError("max_rounds must be at least 1", field="max_rounds", value=max_rounds)

    if max_rounds > 100:
        raise ValidationError(
            "max_rounds too high (max 100). Consider using a stop condition instead.",
            field="max_rounds",
            value=max_rounds,
        )


def validate_model_name(model: str) -> None:
    """Validate model name.

    Args:
        model: Model name to validate

    Raises:
        ValidationError: If model name is invalid
    """
    if not model or not isinstance(model, str):
        raise ValidationError("Model name must be a non-empty string", field="model", value=model)

    if not model.strip():
        raise ValidationError("Model name cannot be only whitespace", field="model", value=model)
