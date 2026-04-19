"""Tests for AgentMind orchestration strategies."""

import pytest
from agentmind.core import Agent, AgentMind, CollaborationStrategy, Message
from agentmind.llm import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, model="mock-model", response_prefix="Mock", **kwargs):
        super().__init__(model, **kwargs)
        self.response_prefix = response_prefix

    async def generate(self, messages, temperature=None, max_tokens=None, **kwargs):
        """Generate a mock response."""
        user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
        return LLMResponse(
            content=f"{self.response_prefix} response to: {user_msg}",
            model=self.model,
            usage={"total_tokens": 15},
            metadata={}
        )

    async def generate_stream(self, messages, temperature=None, max_tokens=None, **kwargs):
        """Generate a mock streaming response."""
        yield "Mock stream"


@pytest.mark.asyncio
async def test_agentmind_with_llm_provider():
    """Test AgentMind with LLM provider."""
    provider = MockLLMProvider()
    mind = AgentMind(llm_provider=provider)

    agent1 = Agent(name="agent1", role="analyst")
    agent2 = Agent(name="agent2", role="creative")

    mind.add_agent(agent1)
    mind.add_agent(agent2)

    # Agents should have LLM provider set
    assert agent1.llm_provider is provider
    assert agent2.llm_provider is provider


@pytest.mark.asyncio
async def test_broadcast_strategy_with_llm():
    """Test broadcast strategy with LLM."""
    provider = MockLLMProvider()
    mind = AgentMind(strategy=CollaborationStrategy.BROADCAST, llm_provider=provider)

    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    result = await mind.start_collaboration("Test task", use_llm=True)

    assert result.success
    assert result.total_messages >= 3  # Initial + 2 responses
    assert len(result.agent_contributions) == 2


@pytest.mark.asyncio
async def test_round_robin_strategy():
    """Test round-robin strategy."""
    provider = MockLLMProvider()
    mind = AgentMind(strategy=CollaborationStrategy.ROUND_ROBIN, llm_provider=provider)

    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))
    mind.add_agent(Agent(name="agent3", role="critic"))

    result = await mind.start_collaboration("Test task", max_rounds=3, use_llm=True)

    assert result.success
    # Round-robin should have agents take turns
    assert result.total_rounds <= 3


@pytest.mark.asyncio
async def test_hierarchical_strategy():
    """Test hierarchical strategy with supervisor."""
    provider = MockLLMProvider()
    mind = AgentMind(strategy=CollaborationStrategy.HIERARCHICAL, llm_provider=provider)

    # Add supervisor first
    mind.add_agent(Agent(name="supervisor", role="supervisor"))
    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    result = await mind.start_collaboration("Test task", use_llm=True)

    assert result.success
    # Supervisor should have contributed
    assert "supervisor" in result.agent_contributions


@pytest.mark.asyncio
async def test_hierarchical_without_supervisor():
    """Test hierarchical strategy falls back without supervisor."""
    provider = MockLLMProvider()
    mind = AgentMind(strategy=CollaborationStrategy.HIERARCHICAL, llm_provider=provider)

    # No supervisor, should fall back to broadcast
    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    result = await mind.start_collaboration("Test task", use_llm=True)

    assert result.success
    assert len(result.agent_contributions) == 2


@pytest.mark.asyncio
async def test_collaboration_without_llm():
    """Test collaboration without LLM (template mode)."""
    mind = AgentMind(strategy=CollaborationStrategy.BROADCAST)

    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    result = await mind.start_collaboration("Test task", use_llm=False)

    assert result.success
    assert result.total_messages >= 3


@pytest.mark.asyncio
async def test_stop_condition():
    """Test collaboration with stop condition."""
    provider = MockLLMProvider()
    mind = AgentMind(llm_provider=provider)

    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    # Stop condition that always triggers
    def stop_fn(messages):
        return True

    result = await mind.start_collaboration(
        "Test task",
        stop_condition=stop_fn,
        use_llm=True
    )

    assert result.success


@pytest.mark.asyncio
async def test_broadcast_message_with_llm():
    """Test broadcast_message with LLM."""
    provider = MockLLMProvider()
    mind = AgentMind(llm_provider=provider)

    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    message = Message(content="Test message", sender="system")
    responses = await mind.broadcast_message(message, use_llm=True)

    assert len(responses) == 2
    assert all("Mock response" in r.content for r in responses)


@pytest.mark.asyncio
async def test_agent_specific_llm_provider():
    """Test agents can have their own LLM providers."""
    global_provider = MockLLMProvider(response_prefix="Global")
    agent_provider = MockLLMProvider(response_prefix="Agent")

    mind = AgentMind(llm_provider=global_provider)

    # Agent with its own provider
    agent1 = Agent(name="agent1", role="analyst", llm_provider=agent_provider)
    # Agent that will use global provider
    agent2 = Agent(name="agent2", role="creative")

    mind.add_agent(agent1)
    mind.add_agent(agent2)

    # agent1 should keep its own provider
    assert agent1.llm_provider is agent_provider
    # agent2 should get global provider
    assert agent2.llm_provider is global_provider


@pytest.mark.asyncio
async def test_collaboration_result_metadata():
    """Test collaboration result contains proper metadata."""
    provider = MockLLMProvider()
    mind = AgentMind(llm_provider=provider)

    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    result = await mind.start_collaboration("Test task", use_llm=True)

    assert result.success
    assert result.total_rounds > 0
    assert result.total_messages > 0
    assert result.final_output is not None
    assert len(result.agent_contributions) == 2
    assert result.error is None


@pytest.mark.asyncio
async def test_multiple_rounds_round_robin():
    """Test multiple rounds in round-robin mode."""
    provider = MockLLMProvider()
    mind = AgentMind(strategy=CollaborationStrategy.ROUND_ROBIN, llm_provider=provider)

    mind.add_agent(Agent(name="agent1", role="analyst"))
    mind.add_agent(Agent(name="agent2", role="creative"))

    result = await mind.start_collaboration("Test task", max_rounds=5, use_llm=True)

    assert result.success
    # Should complete requested rounds or less
    assert result.total_rounds <= 5
