"""Memory optimization for long-running agent conversations.

Provides sliding window, compression, and summarization techniques
to manage memory usage in extended conversations.
"""

import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from ..core.types import Message


@dataclass
class CompressionStats:
    """Statistics about memory compression."""

    original_messages: int
    compressed_messages: int
    compression_ratio: float
    tokens_saved: int


class ConversationCompressor:
    """Compress conversation history using summarization."""

    def __init__(
        self,
        llm_provider: Optional[Any] = None,
        compression_ratio: float = 0.5,
    ):
        """Initialize conversation compressor.

        Args:
            llm_provider: LLM provider for summarization
            compression_ratio: Target compression ratio (0.0-1.0)
        """
        self.llm_provider = llm_provider
        self.compression_ratio = compression_ratio

    async def compress_messages(
        self,
        messages: List[Message],
        preserve_recent: int = 5,
    ) -> tuple[List[Message], CompressionStats]:
        """Compress message history using summarization.

        Args:
            messages: List of messages to compress
            preserve_recent: Number of recent messages to keep uncompressed

        Returns:
            Tuple of (compressed messages, stats)
        """
        if len(messages) <= preserve_recent:
            return messages, CompressionStats(
                original_messages=len(messages),
                compressed_messages=len(messages),
                compression_ratio=1.0,
                tokens_saved=0
            )

        # Split into compressible and recent
        to_compress = messages[:-preserve_recent]
        recent = messages[-preserve_recent:]

        # Estimate tokens (rough approximation)
        original_tokens = sum(len(m.content.split()) for m in to_compress)

        # Compress using LLM if available
        if self.llm_provider:
            summary = await self._summarize_with_llm(to_compress)
        else:
            summary = self._simple_summarize(to_compress)

        # Create summary message
        summary_msg = Message(
            role="system",
            content=f"[Conversation Summary]: {summary}",
            sender="system"
        )

        compressed = [summary_msg] + recent
        compressed_tokens = len(summary.split()) + sum(len(m.content.split()) for m in recent)

        return compressed, CompressionStats(
            original_messages=len(messages),
            compressed_messages=len(compressed),
            compression_ratio=len(compressed) / len(messages),
            tokens_saved=original_tokens - compressed_tokens
        )

    async def _summarize_with_llm(self, messages: List[Message]) -> str:
        """Summarize messages using LLM."""
        conversation = "\n".join([
            f"{m.sender} ({m.role}): {m.content}"
            for m in messages
        ])

        prompt = [
            {"role": "system", "content": "Summarize the following conversation concisely, preserving key information and decisions."},
            {"role": "user", "content": conversation}
        ]

        response = await self.llm_provider.generate(prompt, max_tokens=500)
        return response.content

    def _simple_summarize(self, messages: List[Message]) -> str:
        """Simple rule-based summarization."""
        # Extract key information
        participants = set(m.sender for m in messages)
        topics = []

        # Simple keyword extraction
        for msg in messages:
            words = msg.content.split()
            if len(words) > 10:
                topics.append(" ".join(words[:10]) + "...")

        summary = f"Conversation between {', '.join(participants)}. "
        summary += f"Discussed {len(topics)} topics. "

        if topics:
            summary += f"Including: {topics[0]}"

        return summary


class MemoryOptimizer:
    """Optimize memory usage for long conversations."""

    def __init__(
        self,
        max_messages: int = 100,
        sliding_window: int = 50,
        compression_threshold: int = 75,
        compressor: Optional[ConversationCompressor] = None,
    ):
        """Initialize memory optimizer.

        Args:
            max_messages: Maximum messages before optimization
            sliding_window: Size of sliding window
            compression_threshold: Threshold to trigger compression
            compressor: Optional conversation compressor
        """
        self.max_messages = max_messages
        self.sliding_window = sliding_window
        self.compression_threshold = compression_threshold
        self.compressor = compressor or ConversationCompressor()
        self._total_messages_processed = 0
        self._total_messages_removed = 0

    async def optimize(
        self,
        messages: List[Message],
        strategy: str = "sliding_window",
    ) -> List[Message]:
        """Optimize message list using specified strategy.

        Args:
            messages: List of messages to optimize
            strategy: Optimization strategy ('sliding_window', 'compress', 'hybrid')

        Returns:
            Optimized message list
        """
        self._total_messages_processed += len(messages)

        if len(messages) <= self.max_messages:
            return messages

        if strategy == "sliding_window":
            optimized = self._sliding_window_optimize(messages)
        elif strategy == "compress":
            optimized, _ = await self.compressor.compress_messages(
                messages,
                preserve_recent=self.sliding_window
            )
        elif strategy == "hybrid":
            # Use sliding window first, then compress if still too large
            optimized = self._sliding_window_optimize(messages)
            if len(optimized) > self.compression_threshold:
                optimized, _ = await self.compressor.compress_messages(
                    optimized,
                    preserve_recent=self.sliding_window // 2
                )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        self._total_messages_removed += len(messages) - len(optimized)
        return optimized

    def _sliding_window_optimize(self, messages: List[Message]) -> List[Message]:
        """Apply sliding window optimization."""
        if len(messages) <= self.sliding_window:
            return messages

        # Keep system messages and recent messages
        system_messages = [m for m in messages if m.role == "system"]
        recent_messages = messages[-self.sliding_window:]

        # Combine, removing duplicates
        seen = set()
        optimized = []

        for msg in system_messages + recent_messages:
            msg_id = id(msg)
            if msg_id not in seen:
                seen.add(msg_id)
                optimized.append(msg)

        return optimized

    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        return {
            "total_messages_processed": self._total_messages_processed,
            "total_messages_removed": self._total_messages_removed,
            "removal_rate": (
                self._total_messages_removed / self._total_messages_processed
                if self._total_messages_processed > 0 else 0
            ),
            "max_messages": self.max_messages,
            "sliding_window": self.sliding_window,
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._total_messages_processed = 0
        self._total_messages_removed = 0


class ConnectionPool:
    """Connection pool for LLM providers to reuse connections."""

    def __init__(self, max_connections: int = 10):
        """Initialize connection pool.

        Args:
            max_connections: Maximum number of connections
        """
        self.max_connections = max_connections
        self._pool: List[Any] = []
        self._in_use: set = set()
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_connections)

    async def acquire(self, factory: callable) -> Any:
        """Acquire a connection from the pool.

        Args:
            factory: Function to create new connection

        Returns:
            Connection object
        """
        await self._semaphore.acquire()

        async with self._lock:
            # Try to get from pool
            if self._pool:
                conn = self._pool.pop()
                self._in_use.add(id(conn))
                return conn

            # Create new connection
            conn = await factory()
            self._in_use.add(id(conn))
            return conn

    async def release(self, conn: Any) -> None:
        """Release a connection back to the pool.

        Args:
            conn: Connection to release
        """
        async with self._lock:
            conn_id = id(conn)
            if conn_id in self._in_use:
                self._in_use.remove(conn_id)
                self._pool.append(conn)

        self._semaphore.release()

    async def close_all(self) -> None:
        """Close all connections in the pool."""
        async with self._lock:
            for conn in self._pool:
                if hasattr(conn, 'close'):
                    await conn.close()
            self._pool.clear()
            self._in_use.clear()

    def get_stats(self) -> Dict[str, int]:
        """Get pool statistics."""
        return {
            "available": len(self._pool),
            "in_use": len(self._in_use),
            "total": len(self._pool) + len(self._in_use),
            "max_connections": self.max_connections,
        }
