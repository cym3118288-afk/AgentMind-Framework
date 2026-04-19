"""Memory manager for agents with short-term and long-term memory support.

This module provides the MemoryManager class that handles:
- Short-term memory (recent N rounds)
- Long-term memory (persistent storage)
- Auto-summarization every N rounds
"""

from typing import List, Optional
from ..core.types import Message, MemoryEntry
from .backend import MemoryBackend, InMemoryBackend


class MemoryManager:
    """Manages agent memory with short-term and long-term storage.

    Attributes:
        short_term_limit: Maximum number of recent messages in short-term memory
        summarization_interval: Number of rounds before auto-summarization
        backend: Storage backend for long-term memory
    """

    def __init__(
        self,
        backend: Optional[MemoryBackend] = None,
        short_term_limit: int = 10,
        summarization_interval: int = 5
    ):
        """Initialize memory manager.

        Args:
            backend: Storage backend (defaults to InMemoryBackend)
            short_term_limit: Max messages in short-term memory
            summarization_interval: Rounds before auto-summarization
        """
        self.backend = backend or InMemoryBackend()
        self.short_term_limit = short_term_limit
        self.summarization_interval = summarization_interval
        self._round_counter = 0
        self._summary: Optional[str] = None

    async def add_message(self, message: Message, importance: float = 0.5) -> None:
        """Add a message to memory.

        Args:
            message: The message to store
            importance: Importance score (0.0-1.0)
        """
        entry = MemoryEntry(
            message=message,
            importance=importance
        )
        await self.backend.add(entry)
        self._round_counter += 1

    async def get_short_term_memory(self) -> List[Message]:
        """Get recent messages from short-term memory.

        Returns:
            List of recent messages (up to short_term_limit)
        """
        entries = await self.backend.get_recent(self.short_term_limit)
        return [entry.message for entry in entries]

    async def get_all_messages(self) -> List[Message]:
        """Get all messages from long-term memory.

        Returns:
            List of all stored messages
        """
        entries = await self.backend.get_all()
        return [entry.message for entry in entries]

    async def get_important_messages(self, min_importance: float = 0.7, limit: int = 10) -> List[Message]:
        """Get important messages from memory.

        Args:
            min_importance: Minimum importance threshold
            limit: Maximum number of messages to return

        Returns:
            List of important messages
        """
        entries = await self.backend.search_by_importance(min_importance, limit)
        return [entry.message for entry in entries]

    async def should_summarize(self) -> bool:
        """Check if it's time to summarize memory.

        Returns:
            True if summarization should occur
        """
        return self._round_counter >= self.summarization_interval

    async def create_summary(self, llm_provider=None) -> Optional[str]:
        """Create a summary of conversation history.

        Args:
            llm_provider: Optional LLM provider for AI-powered summarization

        Returns:
            Summary text or None
        """
        messages = await self.get_all_messages()

        if not messages:
            return None

        if llm_provider:
            # Use LLM to create intelligent summary
            conversation_text = "\n".join([
                f"{msg.sender}: {msg.content}" for msg in messages
            ])

            summary_prompt = f"""Summarize the following conversation concisely, capturing key points and decisions:

{conversation_text}

Provide a brief summary (2-3 sentences):"""

            try:
                response = await llm_provider.generate(
                    messages=[{"role": "user", "content": summary_prompt}],
                    temperature=0.3,
                    max_tokens=200
                )
                self._summary = response.content
                self._round_counter = 0  # Reset counter after summarization
                return self._summary
            except Exception:
                # Fallback to simple summary
                pass

        # Simple summary without LLM
        self._summary = f"Conversation with {len(messages)} messages from {len(set(m.sender for m in messages))} participants."
        self._round_counter = 0
        return self._summary

    async def get_summary(self) -> Optional[str]:
        """Get the current conversation summary.

        Returns:
            Summary text or None
        """
        return self._summary

    async def clear(self) -> None:
        """Clear all memory."""
        await self.backend.clear()
        self._round_counter = 0
        self._summary = None

    async def get_context_for_agent(self, include_summary: bool = True) -> List[Message]:
        """Get relevant context for an agent.

        Args:
            include_summary: Whether to include conversation summary

        Returns:
            List of messages for agent context
        """
        messages = await self.get_short_term_memory()

        # If we have a summary and should include it, prepend as system message
        if include_summary and self._summary:
            from ..core.types import MessageRole
            summary_msg = Message(
                content=f"[Previous conversation summary: {self._summary}]",
                sender="system",
                role=MessageRole.SYSTEM
            )
            messages = [summary_msg] + messages

        return messages

    async def count(self) -> int:
        """Get total number of messages in memory.

        Returns:
            Total message count
        """
        return await self.backend.count()
