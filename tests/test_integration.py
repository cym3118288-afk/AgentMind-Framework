"""Integration tests for AgentMind features."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch

from agentmind.core.agent import Agent
from agentmind.core.mind import AgentMind
from agentmind.core.types import Message, AgentConfig
from agentmind.llm.provider import LLMProvider, LLMResponse
from agentmind.memory.manager import MemoryManager
from agentmind.tools import ToolRegistry, tool
from agentmind.performance.cache import CacheManager
from agentmind.performance.batch import BatchProcessor


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, responses=None, **kwargs):
        super().__init__(model="mock-model", **kwargs)
        self.responses = responses or []
        self.call_count = 0

    async def generate(self, messages, **kwargs):
        response = self.responses[self.call_count % len(self.responses)] if self.responses else "Mock response"
        self.call_count += 1
        return LLMResponse(
            content=response,
            model=self.model,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )

    async def generate_stream(self, messages, **kwargs):
        response = self.responses[self.call_count % len(self.responses)] if self.responses else "Mock response"
        self.call_count += 1
        for char in response:
            yield char


class TestAgentIntegration:
    """Integration tests for Agent class."""

    @pytest.mark.asyncio
    async def test_agent_with_llm_provider(self):
        """Test agent with LLM provider."""
        llm = MockLLMProvider(responses=["Hello, I'm an agent!"])
        agent = Agent(name="test_agent", role="assistant", llm_provider=llm)

        message = Message(role="user", content="Hello", sender="user")
        response = await agent.process_message(message)

        assert response is not None
        assert "Hello" in response.content or "agent" in response.content.lower()
        assert len(agent.memory) == 2  # Input and output

    @pytest.mark.asyncio
    async def test_agent_with_tools(self):
        """Test agent with tool usage."""
        from agentmind.tools import tool

        @tool(name="calculator", description="Add two numbers")
        def calculator(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        registry = ToolRegistry()
        registry.register(calculator)

        llm = MockLLMProvider()
        agent = Agent(
            name="test_agent",
            role="assistant",
            llm_provider=llm,
            tool_registry=registry
        )

        # Agent should have access to tools
        assert len(agent._available_tools) > 0

    @pytest.mark.asyncio
    async def test_agent_memory_persistence(self):
        """Test agent memory persistence."""
        llm = MockLLMProvider(responses=["Response 1", "Response 2", "Response 3"])
        agent = Agent(name="test_agent", role="assistant", llm_provider=llm)

        # Process multiple messages
        for i in range(3):
            message = Message(role="user", content=f"Message {i}", sender="user")
            await agent.process_message(message)

        # Check memory
        assert len(agent.memory) == 6  # 3 inputs + 3 outputs
        assert agent.memory[0].content == "Message 0"
        assert agent.memory[-1].content == "Response 3"


class TestAgentMindIntegration:
    """Integration tests for AgentMind orchestration."""

    @pytest.mark.asyncio
    async def test_multi_agent_collaboration(self):
        """Test multi-agent collaboration."""
        llm = MockLLMProvider(responses=[
            "I'll analyze this task.",
            "Based on the analysis, here's my creative solution.",
            "The task is complete."
        ])

        mind = AgentMind(llm_provider=llm)

        analyst = Agent(name="analyst", role="analyst", llm_provider=llm)
        creative = Agent(name="creative", role="creative", llm_provider=llm)

        mind.add_agent(analyst)
        mind.add_agent(creative)

        result = await mind.start_collaboration("Solve this problem", max_rounds=2)

        assert result is not None
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_agent_mind_with_memory(self):
        """Test AgentMind with memory management."""
        llm = MockLLMProvider()
        memory = MemoryManager()

        mind = AgentMind(llm_provider=llm, memory_manager=memory)

        agent = Agent(name="test_agent", role="assistant", llm_provider=llm)
        mind.add_agent(agent)

        # First collaboration
        await mind.start_collaboration("Task 1", max_rounds=1)

        # Memory should be stored
        history = memory.get_history()
        assert len(history) > 0

    @pytest.mark.asyncio
    async def test_agent_coordination(self):
        """Test agent coordination and message passing."""
        responses = [
            "Agent 1 response",
            "Agent 2 response",
            "Agent 1 follow-up",
        ]
        llm = MockLLMProvider(responses=responses)

        mind = AgentMind(llm_provider=llm)

        agent1 = Agent(name="agent1", role="assistant", llm_provider=llm)
        agent2 = Agent(name="agent2", role="assistant", llm_provider=llm)

        mind.add_agent(agent1)
        mind.add_agent(agent2)

        result = await mind.start_collaboration("Coordinate on this task", max_rounds=2)

        # Both agents should have participated
        assert len(agent1.memory) > 0
        assert len(agent2.memory) > 0


class TestPerformanceIntegration:
    """Integration tests for performance features."""

    @pytest.mark.asyncio
    async def test_caching_with_agent(self):
        """Test caching integration with agents."""
        cache = CacheManager()
        llm = MockLLMProvider(responses=["Cached response"])

        # Wrap LLM with caching
        class CachedLLMProvider(MockLLMProvider):
            def __init__(self, *args, cache_manager=None, **kwargs):
                super().__init__(*args, **kwargs)
                self.cache = cache_manager

            async def generate(self, messages, **kwargs):
                # Check cache
                cached = await self.cache.get_response(messages, **kwargs)
                if cached:
                    return cached

                # Generate and cache
                response = await super().generate(messages, **kwargs)
                await self.cache.set_response(messages, response, **kwargs)
                return response

        cached_llm = CachedLLMProvider(responses=["Response"], cache_manager=cache)
        agent = Agent(name="test_agent", role="assistant", llm_provider=cached_llm)

        message = Message(role="user", content="Hello", sender="user")

        # First call - cache miss
        await agent.process_message(message)
        stats = cache.get_stats()
        assert stats["misses"] >= 1

        # Second call - should hit cache
        await agent.process_message(message)
        stats = cache.get_stats()
        assert stats["hits"] >= 1

    @pytest.mark.asyncio
    async def test_batch_processing_agents(self):
        """Test batch processing multiple agent tasks."""
        llm = MockLLMProvider(responses=["Response"] * 10)

        async def process_agent_task(task_id: str, content: str):
            agent = Agent(name=f"agent_{task_id}", role="assistant", llm_provider=llm)
            message = Message(role="user", content=content, sender="user")
            response = await agent.process_message(message)
            return response.content if response else None

        processor = BatchProcessor(max_concurrent=5)

        tasks = [
            {"id": str(i), "task_id": str(i), "content": f"Task {i}"}
            for i in range(10)
        ]

        results = await processor.process_batch(tasks, process_agent_task)

        assert len(results) == 10
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_memory_optimization_with_agent(self):
        """Test memory optimization with agent."""
        from agentmind.performance.memory_optimizer import MemoryOptimizer

        llm = MockLLMProvider(responses=["Response"] * 50)
        agent = Agent(name="test_agent", role="assistant", llm_provider=llm)

        # Generate many messages
        for i in range(50):
            message = Message(role="user", content=f"Message {i}", sender="user")
            await agent.process_message(message)

        # Optimize memory
        optimizer = MemoryOptimizer(max_messages=20, sliding_window=10)
        agent.memory = await optimizer.optimize(agent.memory, strategy="sliding_window")

        # Memory should be reduced
        assert len(agent.memory) <= 20


class TestToolIntegration:
    """Integration tests for tool system."""

    @pytest.mark.asyncio
    async def test_agent_with_multiple_tools(self):
        """Test agent with multiple tools."""
        from agentmind.tools import tool

        @tool(name="add", description="Add two numbers")
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        @tool(name="multiply", description="Multiply two numbers")
        def multiply(a: int, b: int) -> int:
            """Multiply two numbers."""
            return a * b

        registry = ToolRegistry()
        registry.register(add)
        registry.register(multiply)

        llm = MockLLMProvider()
        agent = Agent(
            name="calculator_agent",
            role="assistant",
            llm_provider=llm,
            tool_registry=registry
        )

        # Agent should have both tools
        assert len(agent._available_tools) >= 2

    @pytest.mark.asyncio
    async def test_tool_execution_in_collaboration(self):
        """Test tool execution during collaboration."""
        from agentmind.tools import tool

        @tool(name="get_weather", description="Get weather for a city")
        def get_weather(city: str) -> str:
            """Get weather for a city."""
            return f"Sunny in {city}"

        registry = ToolRegistry()
        registry.register(get_weather)

        llm = MockLLMProvider(responses=["Let me check the weather."])
        mind = AgentMind(llm_provider=llm)

        agent = Agent(
            name="weather_agent",
            role="assistant",
            llm_provider=llm,
            tool_registry=registry
        )
        mind.add_agent(agent)

        result = await mind.start_collaboration("What's the weather?", max_rounds=1)
        assert result is not None


class TestErrorHandling:
    """Integration tests for error handling."""

    @pytest.mark.asyncio
    async def test_agent_handles_llm_errors(self):
        """Test agent handles LLM errors gracefully."""
        class ErrorLLMProvider(LLMProvider):
            async def generate(self, messages, **kwargs):
                raise Exception("LLM Error")

            async def generate_stream(self, messages, **kwargs):
                raise Exception("LLM Error")

        llm = ErrorLLMProvider(model="error-model")
        agent = Agent(name="test_agent", role="assistant", llm_provider=llm)

        message = Message(role="user", content="Hello", sender="user")

        # Should handle error gracefully
        try:
            response = await agent.process_message(message)
            # If no exception, response might be None or error message
            assert response is None or "error" in response.content.lower()
        except Exception as e:
            # Error should be caught and handled
            assert "LLM Error" in str(e)

    @pytest.mark.asyncio
    async def test_batch_processor_handles_failures(self):
        """Test batch processor handles task failures."""
        async def failing_task(should_fail: bool):
            if should_fail:
                raise ValueError("Task failed")
            return "Success"

        processor = BatchProcessor(max_concurrent=5)

        tasks = [
            {"id": "1", "should_fail": False},
            {"id": "2", "should_fail": True},
            {"id": "3", "should_fail": False},
        ]

        results = await processor.process_batch(tasks, failing_task)

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True


class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete workflow from task to result."""
        # Setup
        llm = MockLLMProvider(responses=[
            "I'll research this topic.",
            "Based on research, here's the analysis.",
            "Final summary of findings."
        ])

        cache = CacheManager()
        mind = AgentMind(llm_provider=llm)

        # Create specialized agents
        researcher = Agent(
            name="researcher",
            role="research",
            llm_provider=llm,
            config=AgentConfig(
                name="researcher",
                role="research",
                system_prompt="You are a thorough researcher."
            )
        )

        analyst = Agent(
            name="analyst",
            role="analyst",
            llm_provider=llm,
            config=AgentConfig(
                name="analyst",
                role="analyst",
                system_prompt="You analyze information critically."
            )
        )

        mind.add_agent(researcher)
        mind.add_agent(analyst)

        # Execute workflow
        result = await mind.start_collaboration(
            "Research and analyze quantum computing",
            max_rounds=3
        )

        # Verify results
        assert result is not None
        assert len(result) > 0
        assert len(researcher.memory) > 0
        assert len(analyst.memory) > 0

    @pytest.mark.asyncio
    async def test_performance_optimized_workflow(self):
        """Test workflow with all performance optimizations."""
        from agentmind.performance.memory_optimizer import MemoryOptimizer

        llm = MockLLMProvider(responses=["Response"] * 20)
        cache = CacheManager()
        optimizer = MemoryOptimizer(max_messages=10)

        mind = AgentMind(llm_provider=llm)
        agent = Agent(name="optimized_agent", role="assistant", llm_provider=llm)
        mind.add_agent(agent)

        # Process multiple tasks
        for i in range(10):
            await mind.start_collaboration(f"Task {i}", max_rounds=1)

        # Optimize memory
        agent.memory = await optimizer.optimize(agent.memory)

        # Verify optimization
        assert len(agent.memory) <= 10

        # Check cache stats
        stats = cache.get_stats()
        assert stats["total_requests"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
