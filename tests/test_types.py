"""Test suite for type definitions and Pydantic models."""

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentmind.core.types import (
    AgentConfig,
    AgentRole,
    CollaborationResult,
    CollaborationStrategy,
    MemoryEntry,
    Message,
    MessageRole,
    ToolDefinition,
)


class TestMessageRole:
    """Test MessageRole enum."""

    def test_message_roles(self) -> None:
        """Test all message role values."""
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.AGENT == "agent"


class TestAgentRole:
    """Test AgentRole enum."""

    def test_agent_roles(self) -> None:
        """Test all agent role values."""
        assert AgentRole.ANALYST == "analyst"
        assert AgentRole.CREATIVE == "creative"
        assert AgentRole.COORDINATOR == "coordinator"
        assert AgentRole.CRITIC == "critic"


class TestCollaborationStrategy:
    """Test CollaborationStrategy enum."""

    def test_strategies(self) -> None:
        """Test all collaboration strategies."""
        assert CollaborationStrategy.BROADCAST == "broadcast"
        assert CollaborationStrategy.ROUND_ROBIN == "round_robin"
        assert CollaborationStrategy.HIERARCHICAL == "hierarchical"
        assert CollaborationStrategy.TOPIC_BASED == "topic_based"


class TestCollaborationResult:
    """Test CollaborationResult model."""

    def test_successful_result(self) -> None:
        """Test successful collaboration result."""
        result = CollaborationResult(
            success=True,
            total_rounds=5,
            total_messages=15,
            final_output="Task completed",
            agent_contributions={"agent1": 5, "agent2": 5, "agent3": 5},
        )
        assert result.success is True
        assert result.total_rounds == 5
        assert result.error is None

    def test_failed_result(self) -> None:
        """Test failed collaboration result."""
        result = CollaborationResult(
            success=False,
            error="Timeout exceeded",
            agent_contributions={},
        )
        assert result.success is False
        assert result.error == "Timeout exceeded"


class TestMemoryEntry:
    """Test MemoryEntry model."""

    def test_memory_entry_creation(self) -> None:
        """Test creating a memory entry."""
        msg = Message(content="Test", sender="agent1")
        entry = MemoryEntry(message=msg, importance=0.8)
        assert entry.message.content == "Test"
        assert entry.importance == 0.8
        assert entry.embedding is None

    def test_memory_entry_with_embedding(self) -> None:
        """Test memory entry with vector embedding."""
        msg = Message(content="Test", sender="agent1")
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        entry = MemoryEntry(message=msg, importance=0.9, embedding=embedding)
        assert entry.embedding == embedding


class TestToolDefinition:
    """Test ToolDefinition model."""

    def test_tool_definition(self) -> None:
        """Test creating a tool definition."""
        tool = ToolDefinition(
            name="web_search",
            description="Search the web",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
            },
            required=["query"],
        )
        assert tool.name == "web_search"
        assert "query" in tool.required


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
