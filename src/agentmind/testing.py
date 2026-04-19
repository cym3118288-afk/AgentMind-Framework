"""Testing utilities for AgentMind applications.

This module provides helpers for testing agent systems, including:
- Mock LLM providers
- Test fixtures
- Assertion helpers
- Performance testing utilities
"""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import AsyncMock, Mock

from agentmind import Agent, AgentMind
from agentmind.core.types import Message, MessageRole
from agentmind.llm.provider import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing.

    This provider returns predefined responses without calling real LLM APIs.
    Useful for fast, deterministic tests.

    Example:
        >>> provider = MockLLMProvider(responses=["Response 1", "Response 2"])
        >>> agent = Agent(name="test", role="analyst", llm_provider=provider)
        >>> response = await agent.think_and_respond("test")
    """

    def __init__(
        self,
        responses: Optional[List[str]] = None,
        default_response: str = "Mock response",
        delay: float = 0.0,
    ):
        """Initialize mock provider.

        Args:
            responses: List of responses to return in sequence
            default_response: Response to return when responses list is exhausted
            delay: Simulated delay in seconds (for testing timeouts)
        """
        super().__init__(model="mock-model")
        self.responses = responses or []
        self.default_response = default_response
        self.delay = delay
        self.call_count = 0
        self.call_history: List[Dict[str, Any]] = []

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a mock response.

        Args:
            messages: Input messages
            temperature: Temperature parameter (recorded but not used)
            max_tokens: Max tokens (recorded but not used)
            **kwargs: Additional parameters

        Returns:
            Mock LLM response
        """
        # Record call
        self.call_history.append({
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "kwargs": kwargs,
        })

        # Simulate delay
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        # Get response
        if self.call_count < len(self.responses):
            content = self.responses[self.call_count]
        else:
            content = self.default_response

        self.call_count += 1

        return LLMResponse(
            content=content,
            model=self.model,
            metadata={
                "call_count": self.call_count,
                "mock": True,
            },
        )

    async def stream(self, messages: List[Dict[str, str]], **kwargs):
        """Mock streaming (not implemented)."""
        raise NotImplementedError("Streaming not supported in mock provider")


class AgentTestCase:
    """Base class for agent testing with common utilities.

    Example:
        >>> class MyAgentTest(AgentTestCase):
        ...     async def test_my_agent(self):
        ...         agent = self.create_agent("test", "analyst")
        ...         response = await agent.process_message(
        ...             self.create_message("Hello")
        ...         )
        ...         self.assert_message_contains(response, "hello")
    """

    def create_agent(
        self,
        name: str,
        role: str = "assistant",
        llm_provider: Optional[LLMProvider] = None,
    ) -> Agent:
        """Create a test agent.

        Args:
            name: Agent name
            role: Agent role
            llm_provider: Optional LLM provider (uses mock if not provided)

        Returns:
            Configured agent
        """
        if llm_provider is None:
            llm_provider = MockLLMProvider()

        return Agent(name=name, role=role, llm_provider=llm_provider)

    def create_message(
        self,
        content: str,
        sender: str = "user",
        role: MessageRole = MessageRole.USER,
    ) -> Message:
        """Create a test message.

        Args:
            content: Message content
            sender: Sender name
            role: Message role

        Returns:
            Message instance
        """
        return Message(content=content, sender=sender, role=role)

    def create_mind(
        self,
        agents: Optional[List[Agent]] = None,
        llm_provider: Optional[LLMProvider] = None,
    ) -> AgentMind:
        """Create a test AgentMind instance.

        Args:
            agents: Optional list of agents to add
            llm_provider: Optional LLM provider

        Returns:
            AgentMind instance
        """
        mind = AgentMind(llm_provider=llm_provider)

        if agents:
            for agent in agents:
                mind.add_agent(agent)

        return mind

    def assert_message_contains(self, message: Optional[Message], text: str) -> None:
        """Assert that message contains text.

        Args:
            message: Message to check
            text: Text to find

        Raises:
            AssertionError: If text not found
        """
        assert message is not None, "Message is None"
        assert text.lower() in message.content.lower(), \
            f"Expected '{text}' in message content: {message.content}"

    def assert_agent_called(self, provider: MockLLMProvider, times: int = 1) -> None:
        """Assert that mock provider was called specific number of times.

        Args:
            provider: Mock provider to check
            times: Expected number of calls

        Raises:
            AssertionError: If call count doesn't match
        """
        assert provider.call_count == times, \
            f"Expected {times} calls, got {provider.call_count}"


async def measure_performance(
    func: Callable,
    *args,
    iterations: int = 10,
    **kwargs,
) -> Dict[str, float]:
    """Measure performance of an async function.

    Args:
        func: Async function to measure
        *args: Function arguments
        iterations: Number of iterations to run
        **kwargs: Function keyword arguments

    Returns:
        Performance statistics (avg, min, max, total)

    Example:
        >>> async def my_task():
        ...     await mind.collaborate("test")
        >>> stats = await measure_performance(my_task, iterations=5)
        >>> print(f"Average: {stats['avg']:.2f}s")
    """
    times = []

    for _ in range(iterations):
        start = time.time()
        await func(*args, **kwargs)
        duration = time.time() - start
        times.append(duration)

    return {
        "avg": sum(times) / len(times),
        "min": min(times),
        "max": max(times),
        "total": sum(times),
        "iterations": iterations,
    }


def assert_collaboration_success(result) -> None:
    """Assert that collaboration completed successfully.

    Args:
        result: CollaborationResult to check

    Raises:
        AssertionError: If collaboration failed
    """
    assert result is not None, "Collaboration result is None"
    assert result.final_output, "No final output generated"
    assert result.rounds > 0, "No rounds completed"
    assert len(result.participants) > 0, "No participants"


def assert_response_quality(
    response: str,
    min_length: int = 10,
    required_words: Optional[List[str]] = None,
) -> None:
    """Assert response meets quality criteria.

    Args:
        response: Response text to check
        min_length: Minimum response length
        required_words: Words that must appear in response

    Raises:
        AssertionError: If quality criteria not met
    """
    assert len(response) >= min_length, \
        f"Response too short: {len(response)} < {min_length}"

    if required_words:
        response_lower = response.lower()
        for word in required_words:
            assert word.lower() in response_lower, \
                f"Required word '{word}' not found in response"


class PerformanceMonitor:
    """Monitor performance metrics during testing.

    Example:
        >>> monitor = PerformanceMonitor()
        >>> with monitor.track("collaboration"):
        ...     await mind.collaborate("test")
        >>> print(monitor.get_stats())
    """

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: Dict[str, List[float]] = {}

    def track(self, name: str):
        """Context manager to track operation duration.

        Args:
            name: Name of the operation

        Returns:
            Context manager
        """
        return _PerformanceContext(self, name)

    def record(self, name: str, duration: float) -> None:
        """Record a performance metric.

        Args:
            name: Metric name
            duration: Duration in seconds
        """
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(duration)

    def get_stats(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics.

        Args:
            name: Optional metric name (returns all if None)

        Returns:
            Statistics dictionary
        """
        if name:
            if name not in self.metrics:
                return {}
            times = self.metrics[name]
            return {
                "count": len(times),
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
                "total": sum(times),
            }

        return {
            name: self.get_stats(name)
            for name in self.metrics.keys()
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()


class _PerformanceContext:
    """Context manager for performance tracking."""

    def __init__(self, monitor: PerformanceMonitor, name: str):
        self.monitor = monitor
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.monitor.record(self.name, duration)


# Pytest fixtures (if pytest is available)
try:
    import pytest

    @pytest.fixture
    def mock_llm():
        """Pytest fixture for mock LLM provider."""
        return MockLLMProvider(responses=["Test response"])

    @pytest.fixture
    def test_agent(mock_llm):
        """Pytest fixture for test agent."""
        return Agent(name="test", role="analyst", llm_provider=mock_llm)

    @pytest.fixture
    def test_mind(mock_llm):
        """Pytest fixture for test AgentMind."""
        return AgentMind(llm_provider=mock_llm)

except ImportError:
    # pytest not available, skip fixtures
    pass


__all__ = [
    "MockLLMProvider",
    "AgentTestCase",
    "measure_performance",
    "assert_collaboration_success",
    "assert_response_quality",
    "PerformanceMonitor",
]
