"""Testing Example

Demonstrates how to write tests for AgentMind applications using the testing utilities.

This example shows:
1. Using MockLLMProvider for fast tests
2. Testing agent behavior
3. Testing collaboration
4. Performance testing
5. Using pytest fixtures
"""

import asyncio

import pytest

from agentmind import Agent, AgentMind
from agentmind.core.types import CollaborationStrategy, Message, MessageRole
from agentmind.testing import (
    AgentTestCase,
    MockLLMProvider,
    PerformanceMonitor,
    assert_collaboration_success,
    assert_response_quality,
    measure_performance,
)


# Example 1: Basic agent testing
class TestBasicAgent(AgentTestCase):
    """Test basic agent functionality."""

    async def test_agent_responds(self):
        """Test that agent generates responses."""
        # Create mock provider with predefined response
        provider = MockLLMProvider(responses=["I analyzed the data carefully."])

        # Create agent
        agent = self.create_agent("analyst", "analyst", provider)

        # Send message
        message = self.create_message("Analyze this data")
        response = await agent.process_message(message)

        # Assert response
        assert response is not None
        self.assert_message_contains(response, "analyzed")
        self.assert_agent_called(provider, times=1)

    async def test_agent_memory(self):
        """Test that agent maintains memory."""
        provider = MockLLMProvider()
        agent = self.create_agent("test", "assistant", provider)

        # Send multiple messages
        msg1 = self.create_message("Hello")
        msg2 = self.create_message("How are you?")

        await agent.process_message(msg1)
        await agent.process_message(msg2)

        # Check memory
        assert len(agent.memory) == 4  # 2 user messages + 2 agent responses

    async def test_agent_with_custom_responses(self):
        """Test agent with multiple predefined responses."""
        provider = MockLLMProvider(
            responses=[
                "First response",
                "Second response",
                "Third response",
            ]
        )

        agent = self.create_agent("test", "assistant", provider)

        # Get multiple responses
        responses = []
        for i in range(3):
            msg = self.create_message(f"Message {i}")
            response = await agent.process_message(msg)
            responses.append(response.content)

        # Verify responses match
        assert "First response" in responses[0]
        assert "Second response" in responses[1]
        assert "Third response" in responses[2]


# Example 2: Collaboration testing
class TestCollaboration(AgentTestCase):
    """Test multi - agent collaboration."""

    async def test_basic_collaboration(self):
        """Test basic collaboration between agents."""
        # Create mock provider
        provider = MockLLMProvider(
            responses=[
                "I think we should proceed carefully.",
                "I agree, let's analyze the risks.",
                "Based on our discussion, I recommend moving forward.",
            ]
        )

        # Create agents
        agent1 = self.create_agent("analyst", "analyst", provider)
        agent2 = self.create_agent("advisor", "advisor", provider)

        # Create mind
        mind = self.create_mind([agent1, agent2], provider)

        # Collaborate
        result = await mind.collaborate("Should we proceed?", max_rounds=2)

        # Assert success
        assert_collaboration_success(result)
        assert result.rounds == 2
        assert len(result.participants) == 2

    async def test_broadcast_strategy(self):
        """Test broadcast collaboration strategy."""
        provider = MockLLMProvider(responses=["Response A", "Response B", "Response C"])

        mind = AgentMind(strategy=CollaborationStrategy.BROADCAST, llm_provider=provider)

        # Add multiple agents
        for i in range(3):
            agent = self.create_agent(f"agent_{i}", "analyst", provider)
            mind.add_agent(agent)

        # Collaborate
        result = await mind.collaborate("Analyze this", max_rounds=1)

        # All agents should respond in parallel
        assert_collaboration_success(result)
        assert len(result.participants) == 3


# Example 3: Response quality testing
@pytest.mark.asyncio
async def test_response_quality():
    """Test response quality criteria."""
    provider = MockLLMProvider(
        responses=["This is a detailed analysis of the problem with multiple insights."]
    )

    agent = Agent(name="analyst", role="analyst", llm_provider=provider)
    message = Message(content="Analyze this", sender="user", role=MessageRole.USER)
    response = await agent.process_message(message)

    # Check quality
    assert_response_quality(response.content, min_length=20, required_words=["analysis", "problem"])


# Example 4: Performance testing
@pytest.mark.asyncio
async def test_collaboration_performance():
    """Test collaboration performance."""
    provider = MockLLMProvider(
        responses=["Quick response"] * 10, delay=0.01  # 10ms simulated delay
    )

    mind = AgentMind(llm_provider=provider)
    mind.add_agent(Agent(name="agent1", role="analyst", llm_provider=provider))

    # Measure performance
    async def run_collaboration():
        await mind.collaborate("Test task", max_rounds=1)

    stats = await measure_performance(run_collaboration, iterations=5)

    # Assert performance
    assert stats["avg"] < 1.0  # Should complete in under 1 second
    assert stats["iterations"] == 5
    print(f"Average time: {stats['avg']:.3f}s")


# Example 5: Performance monitoring
@pytest.mark.asyncio
async def test_with_performance_monitor():
    """Test with performance monitoring."""
    monitor = PerformanceMonitor()
    provider = MockLLMProvider(responses=["Response"])

    agent = Agent(name="test", role="analyst", llm_provider=provider)
    message = Message(content="Test", sender="user", role=MessageRole.USER)

    # Track multiple operations
    for i in range(5):
        with monitor.track("process_message"):
            await agent.process_message(message)

    # Get statistics
    stats = monitor.get_stats("process_message")
    assert stats["count"] == 5
    assert stats["avg"] > 0
    print(f"Processed {stats['count']} messages in {stats['total']:.3f}s")


# Example 6: Testing error handling
@pytest.mark.asyncio
async def test_agent_error_handling():
    """Test agent error handling."""
    # Provider that simulates errors
    provider = MockLLMProvider(responses=["Error occurred"])

    agent = Agent(name="test", role="analyst", llm_provider=provider)

    # Agent should handle errors gracefully
    message = Message(content="Test", sender="user", role=MessageRole.USER)
    response = await agent.process_message(message)

    assert response is not None  # Should still return a response


# Example 7: Testing with pytest fixtures
@pytest.fixture
def mock_provider():
    """Fixture for mock LLM provider."""
    return MockLLMProvider(responses=["Test response"])


@pytest.fixture
def test_agent(mock_provider):
    """Fixture for test agent."""
    return Agent(name="test", role="analyst", llm_provider=mock_provider)


@pytest.mark.asyncio
async def test_with_fixtures(test_agent, mock_provider):
    """Test using pytest fixtures."""
    message = Message(content="Hello", sender="user", role=MessageRole.USER)
    response = await test_agent.process_message(message)

    assert response is not None
    assert mock_provider.call_count == 1


# Example 8: Integration test
@pytest.mark.asyncio
async def test_full_workflow():
    """Test complete workflow from start to finish."""
    # Setup
    provider = MockLLMProvider(
        responses=[
            "I'll research this topic.",
            "Based on research, here are the findings.",
            "I'll write the content.",
            "Here's the final content.",
        ]
    )

    mind = AgentMind(strategy=CollaborationStrategy.ROUND_ROBIN, llm_provider=provider)

    # Create team
    researcher = Agent(name="researcher", role="analyst", llm_provider=provider)
    writer = Agent(name="writer", role="creative", llm_provider=provider)

    mind.add_agent(researcher)
    mind.add_agent(writer)

    # Execute workflow
    result = await mind.collaborate("Create content about AI", max_rounds=2)

    # Verify results
    assert_collaboration_success(result)
    assert result.rounds == 2
    assert "researcher" in result.participants
    assert "writer" in result.participants
    assert len(result.final_output) > 0


# Run tests
if __name__ == "__main__":
    print("Running AgentMind tests...\n")

    # Run async tests manually (without pytest)
    async def run_all_tests():
        test_case = TestBasicAgent()

        print("Test 1: Agent responds")
        await test_case.test_agent_responds()
        print("✓ Passed\n")

        print("Test 2: Agent memory")
        await test_case.test_agent_memory()
        print("✓ Passed\n")

        print("Test 3: Custom responses")
        await test_case.test_agent_with_custom_responses()
        print("✓ Passed\n")

        collab_test = TestCollaboration()

        print("Test 4: Basic collaboration")
        await collab_test.test_basic_collaboration()
        print("✓ Passed\n")

        print("Test 5: Broadcast strategy")
        await collab_test.test_broadcast_strategy()
        print("✓ Passed\n")

        print("Test 6: Response quality")
        await test_response_quality()
        print("✓ Passed\n")

        print("Test 7: Performance testing")
        await test_collaboration_performance()
        print("✓ Passed\n")

        print("Test 8: Performance monitoring")
        await test_with_performance_monitor()
        print("✓ Passed\n")

        print("Test 9: Full workflow")
        await test_full_workflow()
        print("✓ Passed\n")

        print("All tests passed!")

    asyncio.run(run_all_tests())
