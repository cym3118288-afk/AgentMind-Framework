"""AgentMind: Lightweight, controllable multi-agent collaboration framework.

AgentMind is a modern Python framework for building multi-agent systems with
a focus on simplicity, control, and local-first design. It provides:

- Lightweight core with minimal dependencies
- Full control over agent behavior and orchestration
- Local-first design with Ollama support
- Type-safe with Pydantic models
- Async-first architecture

Example:
    >>> from agentmind import Agent, AgentMind, Message
    >>>
    >>> # Create agents
    >>> analyst = Agent(name="analyst", role="analyst")
    >>> creative = Agent(name="creative", role="creative")
    >>>
    >>> # Create orchestrator
    >>> mind = AgentMind()
    >>> mind.add_agent(analyst)
    >>> mind.add_agent(creative)
    >>>
    >>> # Start collaboration
    >>> result = await mind.start_collaboration("Analyze this problem")
    >>> print(result.final_output)
"""

from .core.agent import Agent
from .core.mind import AgentMind
from .core.types import (
    AgentConfig,
    AgentRole,
    CollaborationResult,
    CollaborationStrategy,
    Message,
    MessageRole,
    MemoryEntry,
    ToolDefinition,
)

__version__ = "0.1.0"
__author__ = "Terry Carson"
__email__ = "cym3118288@gmail.com"

__all__ = [
    # Core classes
    "Agent",
    "AgentMind",
    # Message types
    "Message",
    "MessageRole",
    # Configuration
    "AgentConfig",
    "AgentRole",
    # Results
    "CollaborationResult",
    "CollaborationStrategy",
    # Memory and tools
    "MemoryEntry",
    "ToolDefinition",
    # Metadata
    "__version__",
    "__author__",
    "__email__",
]


def create_mind(**kwargs) -> AgentMind:
    """Convenience function to create an AgentMind instance.

    Args:
        **kwargs: Arguments to pass to AgentMind constructor

    Returns:
        A new AgentMind instance

    Example:
        >>> mind = create_mind(strategy="broadcast")
        >>> mind.add_agent(Agent(name="test", role="analyst"))
    """
    return AgentMind(**kwargs)
