"""Tests for Agent with LLM integration."""

import pytest
from agentmind.core import Agent, Message, MessageRole
from agentmind.llm import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, model="mock-model", **kwargs):
        super().__init__(model, **kwargs)
        self.call_count = 0

    async def generate(self, messages, temperature=None, max_tokens=None, **kwargs):
        """Generate a mock response."""
        self.call_count += 1
        # Extract user message
        user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
        return LLMResponse(
            content=f"Mock response to: {user_msg}",
            model=self.model,
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            metadata={}
        )

    async def generate_stream(self, messages, temperature=None, max_tokens=None, **kwargs):
        """Generate a mock streaming response."""
        yield "Mock stream"


@pytest.mark.asyncio
async def test_agent_with_llm_provider():
    """Test agent with LLM provider."""
    provider = MockLLMProvider()
    agent = Agent(name="test_agent", role="analyst", llm_provider=provider)

    message = Message(content="Analyze this data", sender="user")
    response = await agent.think_and_respond(message)

    assert response is not None
    assert response.sender == "test_agent"
    assert "Mock response" in response.content
    assert provider.call_count == 1


@pytest.mark.asyncio
async def test_agent_without_llm_provider():
    """Test agent falls back to template when no LLM provider."""
    agent = Agent(name="test_agent", role="analyst")

    message = Message(content="Test message", sender="user")
    response = await agent.think_and_respond(message)

    assert response is not None
    assert response.sender == "test_agent"
    # Should use template response
    assert "test_agent" in response.content


@pytest.mark.asyncio
async def test_agent_llm_error_fallback():
    """Test agent falls back to template on LLM error."""

    class ErrorLLMProvider(LLMProvider):
        async def generate(self, messages, **kwargs):
            raise Exception("LLM error")

        async def generate_stream(self, messages, **kwargs):
            raise Exception("LLM error")

    provider = ErrorLLMProvider(model="error-model")
    agent = Agent(name="test_agent", role="analyst", llm_provider=provider)

    message = Message(content="Test", sender="user")
    response = await agent.think_and_respond(message)

    # Should fall back to template
    assert response is not None
    assert response.sender == "test_agent"


@pytest.mark.asyncio
async def test_agent_memory_with_llm():
    """Test that agent memory is updated with LLM responses."""
    provider = MockLLMProvider()
    agent = Agent(name="test_agent", role="analyst", llm_provider=provider)

    message1 = Message(content="First message", sender="user")
    message2 = Message(content="Second message", sender="user")

    await agent.think_and_respond(message1)
    await agent.think_and_respond(message2)

    # Should have 4 messages in memory (2 incoming + 2 responses)
    assert len(agent.memory) == 4
    assert agent.memory[0].content == "First message"
    assert agent.memory[2].content == "Second message"


@pytest.mark.asyncio
async def test_agent_system_prompt_generation():
    """Test agent system prompt generation."""
    agent = Agent(name="test_agent", role="analyst")

    system_prompt = agent.get_system_prompt()

    assert isinstance(system_prompt, str)
    assert len(system_prompt) > 0
    # Should contain role-specific information
    assert "analyt" in system_prompt.lower() or "data" in system_prompt.lower()


@pytest.mark.asyncio
async def test_agent_system_prompt_with_backstory():
    """Test system prompt includes backstory."""
    from agentmind.core.types import AgentConfig

    config = AgentConfig(
        name="test_agent",
        role="analyst",
        backstory="Expert in financial analysis with 10 years experience"
    )
    agent = Agent(name="test_agent", role="analyst", config=config)

    system_prompt = agent.get_system_prompt()

    assert "financial analysis" in system_prompt.lower()
    assert "10 years" in system_prompt.lower()


@pytest.mark.asyncio
async def test_agent_system_prompt_with_memory():
    """Test system prompt includes recent memory context."""
    agent = Agent(name="test_agent", role="analyst")

    # Add some messages to memory
    msg1 = Message(content="Previous context", sender="user")
    msg2 = Message(content="Agent response", sender="test_agent")
    agent.memory.extend([msg1, msg2])

    system_prompt = agent.get_system_prompt()

    # Should include recent context
    assert "Previous context" in system_prompt or "recent" in system_prompt.lower()


@pytest.mark.asyncio
async def test_agent_llm_metadata():
    """Test that LLM response metadata is stored."""
    provider = MockLLMProvider()
    agent = Agent(name="test_agent", role="analyst", llm_provider=provider)

    message = Message(content="Test", sender="user")
    response = await agent.think_and_respond(message)

    assert "model" in response.metadata
    assert "usage" in response.metadata
    assert response.metadata["model"] == "mock-model"


@pytest.mark.asyncio
async def test_agent_temperature_config():
    """Test agent uses configured temperature."""
    from agentmind.core.types import AgentConfig

    config = AgentConfig(
        name="test_agent",
        role="analyst",
        temperature=0.9,
        max_tokens=2000
    )
    agent = Agent(name="test_agent", role="analyst", config=config)

    assert agent.config.temperature == 0.9
    assert agent.config.max_tokens == 2000
