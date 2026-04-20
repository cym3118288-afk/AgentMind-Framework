"""Comprehensive test suite for AgentMind framework.

This module contains unit tests for all core components including agents,
messages, orchestration, and type validation.
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentmind import Agent, AgentMind, Message  # noqa: E402
from agentmind.core.types import (  # noqa: E402
    AgentConfig,
    AgentRole,
    CollaborationResult,
    MessageRole,
)


class TestMessage:
    """Test suite for Message model."""

    def test_message_creation(self) -> None:
        """Test basic message creation."""
        msg = Message(content="Hello", sender="TestAgent")
        assert msg.content == "Hello"
        assert msg.sender == "TestAgent"
        assert msg.role == MessageRole.AGENT
        assert isinstance(msg.timestamp, datetime)

    def test_message_with_metadata(self) -> None:
        """Test message with metadata."""
        msg = Message(
            content="Test",
            sender="Agent1",
            metadata={"priority": "high", "topic": "analysis"},
        )
        assert msg.metadata["priority"] == "high"
        assert msg.metadata["topic"] == "analysis"

    def test_message_validation(self) -> None:
        """Test message validation."""
        with pytest.raises(Exception):  # Pydantic validation error
            Message(content="", sender="Agent1")  # Empty content should fail

        with pytest.raises(Exception):
            Message(content="Test", sender="")  # Empty sender should fail

    def test_message_string_representation(self) -> None:
        """Test message string representation."""
        msg = Message(content="Hello World", sender="Agent1")
        assert str(msg) == "[Agent1] Hello World"


class TestAgentConfig:
    """Test suite for AgentConfig model."""

    def test_config_creation(self) -> None:
        """Test basic config creation."""
        config = AgentConfig(name="test_agent", role=AgentRole.ANALYST)
        assert config.name == "test_agent"
        assert config.role == AgentRole.ANALYST
        assert config.temperature == 0.7  # Default value
        assert config.max_tokens == 1000  # Default value

    def test_config_validation(self) -> None:
        """Test config validation."""
        with pytest.raises(Exception):
            AgentConfig(name="invalid name!", role=AgentRole.ANALYST)  # Invalid characters

        with pytest.raises(Exception):
            AgentConfig(
                name="test", role=AgentRole.ANALYST, temperature=3.0
            )  # Temperature too high

    def test_config_with_tools(self) -> None:
        """Test config with tools."""
        config = AgentConfig(
            name="researcher",
            role=AgentRole.RESEARCHER,
            tools=["web_search", "calculator"],
        )
        assert len(config.tools) == 2
        assert "web_search" in config.tools


class TestAgent:
    """Test suite for Agent class."""

    def test_agent_creation(self) -> None:
        """Test basic agent creation."""
        agent = Agent(name="TestAgent", role="analyst")
        assert agent.name == "TestAgent"
        assert agent.role == "analyst"
        assert agent.is_active is True
        assert len(agent.memory) == 0

    def test_agent_with_config(self) -> None:
        """Test agent creation with config."""
        config = AgentConfig(
            name="test_agent",
            role=AgentRole.ANALYST,
            temperature=0.5,
            max_tokens=2000,
        )
        agent = Agent(name="test_agent", role="analyst", config=config)
        assert agent.config.temperature == 0.5
        assert agent.config.max_tokens == 2000

    def test_agent_invalid_name(self) -> None:
        """Test agent creation with invalid name."""
        with pytest.raises(ValueError):
            Agent(name="", role="analyst")

        with pytest.raises(ValueError):
            Agent(name="   ", role="analyst")

    @pytest.mark.asyncio
    async def test_agent_process_message(self) -> None:
        """Test agent message processing."""
        agent = Agent(name="TestAgent", role="analyst")
        msg = Message(content="Test message", sender="User")

        response = await agent.process_message(msg)
        assert response is not None
        assert response.sender == "TestAgent"
        assert "Test message" in response.content
        assert len(agent.memory) == 2  # Original message + response

    @pytest.mark.asyncio
    async def test_agent_inactive(self) -> None:
        """Test that inactive agents don't process messages."""
        agent = Agent(name="TestAgent", role="analyst")
        agent.deactivate()

        msg = Message(content="Test", sender="User")
        response = await agent.process_message(msg)
        assert response is None

    def test_agent_memory_management(self) -> None:
        """Test agent memory retrieval and clearing."""
        agent = Agent(name="TestAgent", role="analyst")
        msg1 = Message(content="Message 1", sender="User")
        msg2 = Message(content="Message 2", sender="User")

        agent.memory.append(msg1)
        agent.memory.append(msg2)

        recent = agent.get_recent_memory(limit=1)
        assert len(recent) == 1
        assert recent[0].content == "Message 2"

        agent.clear_memory()
        assert len(agent.memory) == 0

    @pytest.mark.asyncio
    async def test_agent_memory_limit(self) -> None:
        """Test that agent respects memory limit."""
        config = AgentConfig(name="test", role=AgentRole.ANALYST, memory_limit=5)
        agent = Agent(name="test", role="analyst", config=config)

        # Process messages which will trigger memory trimming
        for i in range(6):
            msg = Message(content=f"Message {i}", sender="User")
            await agent.process_message(msg)

        # Memory should be trimmed to limit (each process adds 2 messages: input + response)
        assert len(agent.memory) <= config.memory_limit

    def test_agent_role_based_responses(self) -> None:
        """Test that different roles generate different responses."""
        analyst = Agent(name="Analyst", role=AgentRole.ANALYST.value)
        creative = Agent(name="Creative", role=AgentRole.CREATIVE.value)

        msg = Message(content="Test", sender="User")

        analyst_response = analyst._generate_response(msg)
        creative_response = creative._generate_response(msg)

        assert "Analysis" in analyst_response
        assert "Creative" in creative_response
        assert analyst_response != creative_response


class TestAgentMind:
    """Test suite for AgentMind orchestrator."""

    def test_agentmind_creation(self) -> None:
        """Test basic AgentMind creation."""
        mind = AgentMind()
        assert len(mind.agents) == 0
        assert len(mind.conversation_history) == 0
        assert mind.is_running is False

    def test_add_agent(self) -> None:
        """Test adding agents to AgentMind."""
        mind = AgentMind()
        agent = Agent(name="TestAgent", role="analyst")
        mind.add_agent(agent)
        assert len(mind.agents) == 1

    def test_add_duplicate_agent(self) -> None:
        """Test that duplicate agent names are rejected."""
        mind = AgentMind()
        agent1 = Agent(name="TestAgent", role="analyst")
        agent2 = Agent(name="TestAgent", role="creative")

        mind.add_agent(agent1)
        with pytest.raises(ValueError):
            mind.add_agent(agent2)

    def test_remove_agent(self) -> None:
        """Test removing agents."""
        mind = AgentMind()
        agent = Agent(name="TestAgent", role="analyst")
        mind.add_agent(agent)

        result = mind.remove_agent("TestAgent")
        assert result is True
        assert len(mind.agents) == 0

        result = mind.remove_agent("NonExistent")
        assert result is False

    def test_get_agent(self) -> None:
        """Test retrieving agents by name."""
        mind = AgentMind()
        agent = Agent(name="TestAgent", role="analyst")
        mind.add_agent(agent)

        retrieved = mind.get_agent("TestAgent")
        assert retrieved is not None
        assert retrieved.name == "TestAgent"

        not_found = mind.get_agent("NonExistent")
        assert not_found is None

    @pytest.mark.asyncio
    async def test_broadcast_message(self) -> None:
        """Test message broadcasting."""
        mind = AgentMind()
        agent1 = Agent(name="Agent1", role="analyst")
        agent2 = Agent(name="Agent2", role="creative")
        mind.add_agent(agent1)
        mind.add_agent(agent2)

        msg = Message(content="Test broadcast", sender="system")
        responses = await mind.broadcast_message(msg, exclude_sender=False)

        assert len(responses) == 2
        assert len(mind.conversation_history) == 3  # Original + 2 responses

    @pytest.mark.asyncio
    async def test_collaboration(self) -> None:
        """Test full collaboration session."""
        mind = AgentMind()
        agent1 = Agent(name="Agent1", role="analyst")
        agent2 = Agent(name="Agent2", role="creative")
        mind.add_agent(agent1)
        mind.add_agent(agent2)

        result = await mind.start_collaboration("Test collaboration")

        assert isinstance(result, CollaborationResult)
        assert result.success is True
        assert result.total_rounds >= 1
        assert result.total_messages > 0
        assert len(result.agent_contributions) == 2

    @pytest.mark.asyncio
    async def test_collaboration_no_agents(self) -> None:
        """Test collaboration with no agents."""
        mind = AgentMind()
        result = await mind.start_collaboration("Test")

        assert result.success is False
        assert result.error == "No agents available"

    def test_conversation_summary(self) -> None:
        """Test conversation summary generation."""
        mind = AgentMind()
        agent = Agent(name="TestAgent", role="analyst")
        mind.add_agent(agent)

        summary = mind.get_conversation_summary()
        assert summary["total_messages"] == 0
        assert summary["active_agents"] == 1
        assert summary["total_agents"] == 1

    def test_reset(self) -> None:
        """Test system reset."""
        mind = AgentMind()
        agent = Agent(name="TestAgent", role="analyst")
        mind.add_agent(agent)
        mind.conversation_history.append(Message(content="Test", sender="system"))

        mind.reset()
        assert len(mind.agents) == 0
        assert len(mind.conversation_history) == 0
        assert mind.is_running is False


class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_multi_agent_collaboration(self) -> None:
        """Test a complete multi - agent collaboration scenario."""
        mind = AgentMind()

        # Create a team of agents
        analyst = Agent(name="analyst", role=AgentRole.ANALYST.value)
        creative = Agent(name="creative", role=AgentRole.CREATIVE.value)
        coordinator = Agent(name="coordinator", role=AgentRole.COORDINATOR.value)

        mind.add_agent(analyst)
        mind.add_agent(creative)
        mind.add_agent(coordinator)

        # Start collaboration
        result = await mind.start_collaboration("How can we improve our product?", max_rounds=5)

        # Verify results
        assert result.success is True
        assert len(result.agent_contributions) == 3
        assert result.agent_contributions["analyst"] > 0
        assert result.agent_contributions["creative"] > 0
        assert result.agent_contributions["coordinator"] > 0
        assert result.final_output is not None

    @pytest.mark.asyncio
    async def test_agent_memory_persistence(self) -> None:
        """Test that agent memory persists across multiple messages."""
        agent = Agent(name="TestAgent", role="analyst")

        msg1 = Message(content="First message", sender="User")
        msg2 = Message(content="Second message", sender="User")

        await agent.process_message(msg1)
        await agent.process_message(msg2)

        assert len(agent.memory) == 4  # 2 messages + 2 responses
        recent = agent.get_recent_memory(limit=2)
        assert len(recent) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
