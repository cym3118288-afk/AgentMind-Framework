"""Core type definitions for AgentMind framework.

This module contains all Pydantic models and type definitions used throughout
the framework, ensuring type safety and data validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class MessageRole(str, Enum):
    """Role of the message sender."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    AGENT = "agent"


class Message(BaseModel):
    """Represents a message in the multi-agent system.

    Attributes:
        content: The text content of the message
        sender: Name/ID of the agent or system that sent the message
        role: Role of the sender (system, user, assistant, agent)
        timestamp: When the message was created
        metadata: Optional additional data attached to the message
    """

    content: str = Field(..., description="The message content", min_length=1)
    sender: str = Field(..., description="Name or ID of the sender", min_length=1)
    role: MessageRole = Field(default=MessageRole.AGENT, description="Role of the sender")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Let's analyze this problem",
                    "sender": "analyst_agent",
                    "role": "agent",
                    "metadata": {"priority": "high"},
                }
            ]
        }
    }

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"[{self.sender}] {self.content}"


class AgentRole(str, Enum):
    """Predefined agent roles with specific behaviors."""

    ANALYST = "analyst"
    CREATIVE = "creative"
    COORDINATOR = "coordinator"
    CRITIC = "critic"
    RESEARCHER = "researcher"
    EXECUTOR = "executor"
    SUMMARIZER = "summarizer"
    DEBATER = "debater"
    SUPERVISOR = "supervisor"
    ASSISTANT = "assistant"


class AgentConfig(BaseModel):
    """Configuration for an agent.

    Attributes:
        name: Unique identifier for the agent
        role: The agent's role/specialty
        backstory: Optional background description for the agent
        temperature: LLM temperature for response generation (0.0-2.0)
        max_tokens: Maximum tokens for LLM responses
        tools: List of tool names this agent can use
        system_prompt: Optional custom system prompt override
        memory_limit: Maximum number of messages to keep in memory
    """

    name: str = Field(..., description="Unique agent name", min_length=1)
    role: Union[AgentRole, str] = Field(
        default=AgentRole.ASSISTANT, description="Agent role or custom role string"
    )
    backstory: Optional[str] = Field(
        default=None, description="Background description for the agent"
    )
    temperature: float = Field(
        default=0.7, description="LLM temperature", ge=0.0, le=2.0
    )
    max_tokens: int = Field(
        default=1000, description="Maximum tokens for responses", gt=0, le=100000
    )
    tools: List[str] = Field(default_factory=list, description="Available tool names")
    system_prompt: Optional[str] = Field(
        default=None, description="Custom system prompt override"
    )
    memory_limit: int = Field(
        default=50, description="Maximum messages in memory", gt=0, le=1000
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure agent name contains only valid characters."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Agent name must contain only alphanumeric, underscore, or dash")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "data_analyst",
                    "role": "analyst",
                    "backstory": "Expert in data analysis and pattern recognition",
                    "temperature": 0.5,
                    "max_tokens": 2000,
                    "tools": ["calculator", "web_search"],
                }
            ]
        }
    }


class CollaborationStrategy(str, Enum):
    """Strategy for agent collaboration."""

    BROADCAST = "broadcast"  # All agents receive all messages
    ROUND_ROBIN = "round_robin"  # Agents take turns
    HIERARCHICAL = "hierarchical"  # Supervisor delegates to sub-agents
    TOPIC_BASED = "topic_based"  # Route by message topic/metadata


class CollaborationResult(BaseModel):
    """Result of a collaboration session.

    Attributes:
        success: Whether the collaboration completed successfully
        total_rounds: Number of collaboration rounds executed
        total_messages: Total messages exchanged
        final_output: The final result or consensus
        agent_contributions: Summary of each agent's contributions
        error: Optional error message if collaboration failed
        metadata: Additional result metadata
    """

    success: bool = Field(..., description="Whether collaboration succeeded")
    total_rounds: int = Field(default=0, description="Number of rounds", ge=0)
    total_messages: int = Field(default=0, description="Total messages exchanged", ge=0)
    final_output: Optional[str] = Field(default=None, description="Final result or consensus")
    agent_contributions: Dict[str, int] = Field(
        default_factory=dict, description="Message count per agent"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "total_rounds": 5,
                    "total_messages": 15,
                    "final_output": "Analysis complete: recommendation is to proceed",
                    "agent_contributions": {"analyst": 5, "critic": 5, "coordinator": 5},
                }
            ]
        }
    }


class MemoryEntry(BaseModel):
    """A single entry in agent memory.

    Attributes:
        message: The stored message
        importance: Importance score (0.0-1.0)
        embedding: Optional vector embedding for semantic search
    """

    message: Message = Field(..., description="The stored message")
    importance: float = Field(default=0.5, description="Importance score", ge=0.0, le=1.0)
    embedding: Optional[List[float]] = Field(
        default=None, description="Vector embedding for semantic search"
    )


class ToolDefinition(BaseModel):
    """Definition of a tool that agents can use.

    Attributes:
        name: Unique tool identifier
        description: What the tool does
        parameters: JSON schema for tool parameters
        required: List of required parameter names
    """

    name: str = Field(..., description="Unique tool name", min_length=1)
    description: str = Field(..., description="Tool description", min_length=1)
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="JSON schema for parameters"
    )
    required: List[str] = Field(default_factory=list, description="Required parameter names")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "web_search",
                    "description": "Search the web for information",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string", "description": "Search query"}},
                    },
                    "required": ["query"],
                }
            ]
        }
    }
