"""Utility functions and helpers for AgentMind.

This module provides various utility functions for async operations,
prompt templates, tracing, and other common tasks.

This is a placeholder for Phase 1-2 implementation.
"""

import asyncio
from typing import Any, Coroutine, List, TypeVar

T = TypeVar("T")


async def gather_with_timeout(
    *coroutines: Coroutine[Any, Any, T], timeout: float = 30.0
) -> List[T]:
    """Gather coroutines with a timeout.

    Args:
        *coroutines: Coroutines to execute
        timeout: Timeout in seconds

    Returns:
        List of results

    Raises:
        asyncio.TimeoutError: If timeout is exceeded
    """
    return await asyncio.wait_for(asyncio.gather(*coroutines), timeout=timeout)


def format_prompt(template: str, **kwargs: Any) -> str:
    """Format a prompt template with variables.

    Args:
        template: Prompt template string
        **kwargs: Variables to substitute

    Returns:
        Formatted prompt string

    Example:
        >>> prompt = format_prompt("Hello {name}!", name="World")
        >>> print(prompt)
        Hello World!
    """
    return template.format(**kwargs)


# Placeholder for future utilities
class Tracer:
    """Tracing utility for observability.

    To be implemented in Phase 3.
    """

    def __init__(self) -> None:
        """Initialize tracer."""
        self.traces: List[Any] = []

    def trace(self, event: str, data: Any) -> None:
        """Record a trace event."""
        # Placeholder implementation
        pass


__all__ = ["gather_with_timeout", "format_prompt", "Tracer"]
