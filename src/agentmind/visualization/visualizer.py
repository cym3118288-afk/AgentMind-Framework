"""Message flow and memory visualizers."""

from typing import Any, Dict, List

from ..core.types import Message


class MessageFlowVisualizer:
    """Visualizes message flow between agents.

    Creates visual representations of agent communication patterns.
    """

    def __init__(self):
        """Initialize the visualizer."""
        self.messages: List[Message] = []

    def add_message(self, message: Message) -> None:
        """Add a message to the visualization.

        Args:
            message: Message to add
        """
        self.messages.append(message)

    def get_flow_diagram(self) -> str:
        """Generate a text-based flow diagram.

        Returns:
            String representation of message flow
        """
        if not self.messages:
            return "No messages to display"

        lines = ["Message Flow:", "=" * 60]

        for i, msg in enumerate(self.messages, 1):
            sender = msg.sender or "unknown"
            role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content

            lines.append(f"\n{i}. [{role}] {sender}")
            lines.append(f"   {content_preview}")

        return "\n".join(lines)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about message flow.

        Returns:
            Dictionary with flow statistics
        """
        if not self.messages:
            return {}

        senders = {}
        roles = {}

        for msg in self.messages:
            sender = msg.sender or "unknown"
            senders[sender] = senders.get(sender, 0) + 1

            role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            roles[role] = roles.get(role, 0) + 1

        return {
            "total_messages": len(self.messages),
            "unique_senders": len(senders),
            "messages_by_sender": senders,
            "messages_by_role": roles,
        }

    def get_mermaid_diagram(self) -> str:
        """Generate a Mermaid diagram of message flow.

        Returns:
            Mermaid diagram syntax
        """
        if not self.messages:
            return "graph LR\n    A[No messages]"

        lines = ["graph LR"]

        # Track unique senders
        senders = set()
        for msg in self.messages:
            sender = msg.sender or "unknown"
            senders.add(sender)

        # Add nodes
        for sender in senders:
            node_id = sender.replace(" ", "_")
            lines.append(f"    {node_id}[{sender}]")

        # Add edges (simplified - show communication patterns)
        prev_sender = None
        for msg in self.messages:
            sender = msg.sender or "unknown"
            if prev_sender and prev_sender != sender:
                from_id = prev_sender.replace(" ", "_")
                to_id = sender.replace(" ", "_")
                lines.append(f"    {from_id} --> {to_id}")
            prev_sender = sender

        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []


class MemoryVisualizer:
    """Visualizes agent memory and context.

    Provides inspection of agent memory states and conversation history.
    """

    def __init__(self):
        """Initialize the memory visualizer."""
        self.agent_memories: Dict[str, List[Message]] = {}

    def update_agent_memory(self, agent_name: str, memory: List[Message]) -> None:
        """Update memory for an agent.

        Args:
            agent_name: Name of the agent
            memory: List of messages in agent's memory
        """
        self.agent_memories[agent_name] = memory

    def get_memory_summary(self, agent_name: str) -> str:
        """Get a summary of an agent's memory.

        Args:
            agent_name: Name of the agent

        Returns:
            String summary of memory
        """
        memory = self.agent_memories.get(agent_name, [])

        if not memory:
            return f"No memory for agent: {agent_name}"

        lines = [
            f"Memory for {agent_name}:",
            "=" * 60,
            f"Total messages: {len(memory)}",
            "",
            "Recent messages:",
        ]

        # Show last 5 messages
        for msg in memory[-5:]:
            role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            sender = msg.sender or "unknown"
            content_preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content

            lines.append(f"\n[{role}] {sender}:")
            lines.append(f"  {content_preview}")

        return "\n".join(lines)

    def get_all_memories_summary(self) -> str:
        """Get summary of all agent memories.

        Returns:
            String summary of all memories
        """
        if not self.agent_memories:
            return "No agent memories available"

        lines = ["Agent Memories Summary:", "=" * 60]

        for agent_name, memory in self.agent_memories.items():
            lines.append(f"\n{agent_name}: {len(memory)} messages")

        return "\n".join(lines)

    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get statistics about agent memories.

        Returns:
            Dictionary with memory statistics
        """
        if not self.agent_memories:
            return {}

        total_messages = sum(len(memory) for memory in self.agent_memories.values())
        avg_memory_size = total_messages / len(self.agent_memories) if self.agent_memories else 0

        return {
            "total_agents": len(self.agent_memories),
            "total_messages": total_messages,
            "avg_memory_size": avg_memory_size,
            "agents": {
                name: len(memory)
                for name, memory in self.agent_memories.items()
            },
        }

    def clear(self) -> None:
        """Clear all memory data."""
        self.agent_memories = {}
