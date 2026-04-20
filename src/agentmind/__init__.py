"""AgentMind: Lightweight, controllable multi-agent collaboration framework.

AgentMind is a modern Python framework for building multi-agent systems with
a focus on simplicity, control, and local-first design. It provides:

- Lightweight core with minimal dependencies
- Full control over agent behavior and orchestration
- Local-first design with Ollama support
- Type-safe with Pydantic models
- Async-first architecture
- Plugin system with entry_points support
- Advanced orchestration modes
- Multi-modal support
- State machine and checkpointing

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

from .core.mind import AgentMind

# Enhanced classes (optional imports)
try:
    pass

    __all_enhanced__ = [
        "EnhancedAgent",
        "AgentState",
        "EnhancedAgentMind",
        "SystemState",
        "TaskPriority",
    ]
except ImportError:
    __all_enhanced__ = []

# Plugin system
try:
    pass

    __all_plugins__ = [
        "discover_plugins",
        "load_plugin",
        "list_plugins",
        "LLMProviderInterface",
        "MemoryBackendInterface",
        "ToolRegistryInterface",
        "OrchestratorInterface",
        "ObserverInterface",
    ]
except ImportError:
    __all_plugins__ = []

__version__ = "0.2.0"
__author__ = "Terry Carson"
__email__ = "cym3118288@gmail.com"

__all__ = (
    [
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
    + __all_enhanced__
    + __all_plugins__
)


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
