"""Tests for performance optimization features."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch

from agentmind.performance.cache import (
    InMemoryCache,
    CacheManager,
    RedisCache,
)
from agentmind.performance.batch import BatchProcessor, BatchResult
from agentmind.performance.memory_optimizer import (
    MemoryOptimizer,
    ConversationCompressor,
    ConnectionPool,
)
from agentmind.core.types import Message


class TestInMemoryCache:
    """Test in-memory cache implementation."""

    @pytest.mark.asyncio
    async def test_basic_operations(self):
        """Test basic cache operations."""
        cache = InMemoryCache(max_size=10)

        # Test set and get
        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"

        # Test non-existent key
        assert await cache.get("nonexistent") is None

        # Test exists
        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = InMemoryCache()

        # Set with short TTL
        await cache.set("key1", "value1", ttl=1)
        assert await cache.get("key1") == "value1"

        # Wait for expiration
        await asyncio.sleep(1.1)
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = InMemoryCache(max_size=3)

        # Fill cache
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Access key1 to make it recently used
        await cache.get("key1")

        # Add new key, should evict key2 (least recently used)
        await cache.set("key4", "value4")

        assert await cache.exists("key1") is True
        assert await cache.exists("key2") is False
        assert await cache.exists("key3") is True
        assert await cache.exists("key4") is True

    @pytest.mark.asyncio
    async def test_delete_and_clear(self):
        """Test delete and clear operations."""
        cache = InMemoryCache()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        # Test delete
        await cache.delete("key1")
        assert await cache.exists("key1") is False
        assert await cache.exists("key2") is True

        # Test clear
        await cache.clear()
        assert await cache.exists("key2") is False
        assert cache.size() == 0


class TestCacheManager:
    """Test cache manager."""

    @pytest.mark.asyncio
    async def test_cache_hit_and_miss(self):
        """Test cache hit and miss tracking."""
        manager = CacheManager()

        messages = [{"role": "user", "content": "Hello"}]

        # First call should be a miss
        result = await manager.get_response(messages)
        assert result is None

        # Set response
        await manager.set_response(messages, "Response")

        # Second call should be a hit
        result = await manager.get_response(messages)
        assert result == "Response"

        # Check stats
        stats = manager.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation is deterministic."""
        manager = CacheManager()

        messages1 = [{"role": "user", "content": "Hello"}]
        messages2 = [{"role": "user", "content": "Hello"}]
        messages3 = [{"role": "user", "content": "World"}]

        key1 = manager._generate_key(messages1)
        key2 = manager._generate_key(messages2)
        key3 = manager._generate_key(messages3)

        # Same messages should generate same key
        assert key1 == key2

        # Different messages should generate different key
        assert key1 != key3

    @pytest.mark.asyncio
    async def test_cache_disabled(self):
        """Test cache when disabled."""
        manager = CacheManager(enabled=False)

        messages = [{"role": "user", "content": "Hello"}]

        await manager.set_response(messages, "Response")
        result = await manager.get_response(messages)

        # Should not cache when disabled
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate(self):
        """Test cache invalidation."""
        manager = CacheManager()

        messages = [{"role": "user", "content": "Hello"}]

        await manager.set_response(messages, "Response")
        assert await manager.get_response(messages) == "Response"

        # Invalidate
        await manager.invalidate(messages)
        assert await manager.get_response(messages) is None


class TestBatchProcessor:
    """Test batch processing."""

    @pytest.mark.asyncio
    async def test_basic_batch_processing(self):
        """Test basic batch processing."""
        async def process_task(value: int) -> int:
            await asyncio.sleep(0.01)
            return value * 2

        processor = BatchProcessor(max_concurrent=5)
        tasks = [{"id": str(i), "value": i} for i in range(10)]

        results = await processor.process_batch(tasks, process_task)

        assert len(results) == 10
        assert all(r.success for r in results)
        assert [r.result for r in results] == [i * 2 for i in range(10)]

    @pytest.mark.asyncio
    async def test_batch_with_failures(self):
        """Test batch processing with failures."""
        async def process_task(value: int) -> int:
            if value == 5:
                raise ValueError("Test error")
            return value * 2

        processor = BatchProcessor(max_concurrent=5)
        tasks = [{"id": str(i), "value": i} for i in range(10)]

        results = await processor.process_batch(tasks, process_task)

        assert len(results) == 10
        assert sum(1 for r in results if r.success) == 9
        assert sum(1 for r in results if not r.success) == 1

        # Check failed task
        failed = [r for r in results if not r.success][0]
        assert "Test error" in failed.error

    @pytest.mark.asyncio
    async def test_batch_timeout(self):
        """Test batch processing with timeout."""
        async def slow_task(value: int) -> int:
            await asyncio.sleep(2)
            return value

        processor = BatchProcessor(max_concurrent=5, timeout=0.1)
        tasks = [{"id": "1", "value": 1}]

        results = await processor.process_batch(tasks, slow_task)

        assert len(results) == 1
        assert not results[0].success
        assert "timed out" in results[0].error

    @pytest.mark.asyncio
    async def test_batch_stats(self):
        """Test batch statistics."""
        async def process_task(value: int) -> int:
            await asyncio.sleep(0.01)
            if value == 5:
                raise ValueError("Error")
            return value * 2

        processor = BatchProcessor(max_concurrent=5)
        tasks = [{"id": str(i), "value": i} for i in range(10)]

        results = await processor.process_batch(tasks, process_task)
        stats = processor.get_stats(results)

        assert stats["total_tasks"] == 10
        assert stats["successful"] == 9
        assert stats["failed"] == 1
        assert stats["success_rate"] == 0.9
        assert stats["avg_duration"] > 0


class TestMemoryOptimizer:
    """Test memory optimization."""

    @pytest.mark.asyncio
    async def test_sliding_window_optimization(self):
        """Test sliding window optimization."""
        optimizer = MemoryOptimizer(max_messages=10, sliding_window=5)

        # Create messages
        messages = [
            Message(role="user", content=f"Message {i}", sender="user")
            for i in range(20)
        ]

        optimized = await optimizer.optimize(messages, strategy="sliding_window")

        # Should keep only recent messages
        assert len(optimized) <= optimizer.sliding_window
        assert optimized[-1].content == "Message 19"

    @pytest.mark.asyncio
    async def test_no_optimization_needed(self):
        """Test when no optimization is needed."""
        optimizer = MemoryOptimizer(max_messages=100)

        messages = [
            Message(role="user", content=f"Message {i}", sender="user")
            for i in range(10)
        ]

        optimized = await optimizer.optimize(messages, strategy="sliding_window")

        # Should return all messages
        assert len(optimized) == len(messages)

    @pytest.mark.asyncio
    async def test_system_message_preservation(self):
        """Test that system messages are preserved."""
        optimizer = MemoryOptimizer(max_messages=10, sliding_window=5)

        messages = [
            Message(role="system", content="System prompt", sender="system"),
        ] + [
            Message(role="user", content=f"Message {i}", sender="user")
            for i in range(20)
        ]

        optimized = await optimizer.optimize(messages, strategy="sliding_window")

        # System message should be preserved
        system_messages = [m for m in optimized if m.role == "system"]
        assert len(system_messages) >= 1
        assert system_messages[0].content == "System prompt"

    @pytest.mark.asyncio
    async def test_optimizer_stats(self):
        """Test optimizer statistics."""
        optimizer = MemoryOptimizer(max_messages=10, sliding_window=5)

        messages = [
            Message(role="user", content=f"Message {i}", sender="user")
            for i in range(20)
        ]

        await optimizer.optimize(messages, strategy="sliding_window")

        stats = optimizer.get_stats()
        assert stats["total_messages_processed"] == 20
        assert stats["total_messages_removed"] > 0
        assert stats["removal_rate"] > 0


class TestConversationCompressor:
    """Test conversation compression."""

    @pytest.mark.asyncio
    async def test_simple_compression(self):
        """Test simple compression without LLM."""
        compressor = ConversationCompressor()

        messages = [
            Message(role="user", content=f"Message {i}", sender="user")
            for i in range(20)
        ]

        compressed, stats = await compressor.compress_messages(
            messages,
            preserve_recent=5
        )

        # Should have summary + recent messages
        assert len(compressed) < len(messages)
        assert stats.compression_ratio < 1.0
        assert stats.tokens_saved > 0

    @pytest.mark.asyncio
    async def test_compression_with_llm(self):
        """Test compression with LLM provider."""
        # Mock LLM provider
        mock_llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = "Summary of conversation"
        mock_llm.generate.return_value = mock_response

        compressor = ConversationCompressor(llm_provider=mock_llm)

        messages = [
            Message(role="user", content=f"Message {i}", sender="user")
            for i in range(20)
        ]

        compressed, stats = await compressor.compress_messages(
            messages,
            preserve_recent=5
        )

        # Should use LLM for summarization
        assert mock_llm.generate.called
        assert len(compressed) < len(messages)
        assert any("Summary" in m.content for m in compressed)


class TestConnectionPool:
    """Test connection pooling."""

    @pytest.mark.asyncio
    async def test_acquire_and_release(self):
        """Test acquiring and releasing connections."""
        pool = ConnectionPool(max_connections=3)

        async def create_connection():
            return Mock()

        # Acquire connections
        conn1 = await pool.acquire(create_connection)
        conn2 = await pool.acquire(create_connection)

        stats = pool.get_stats()
        assert stats["in_use"] == 2
        assert stats["available"] == 0

        # Release connection
        await pool.release(conn1)

        stats = pool.get_stats()
        assert stats["in_use"] == 1
        assert stats["available"] == 1

    @pytest.mark.asyncio
    async def test_connection_reuse(self):
        """Test connection reuse from pool."""
        pool = ConnectionPool(max_connections=3)

        connections_created = []

        async def create_connection():
            conn = Mock()
            connections_created.append(conn)
            return conn

        # Acquire and release
        conn1 = await pool.acquire(create_connection)
        await pool.release(conn1)

        # Acquire again - should reuse
        conn2 = await pool.acquire(create_connection)

        assert conn1 is conn2
        assert len(connections_created) == 1

    @pytest.mark.asyncio
    async def test_max_connections_limit(self):
        """Test max connections limit."""
        pool = ConnectionPool(max_connections=2)

        async def create_connection():
            return Mock()

        # Acquire max connections
        conn1 = await pool.acquire(create_connection)
        conn2 = await pool.acquire(create_connection)

        # Try to acquire one more - should block
        acquire_task = asyncio.create_task(pool.acquire(create_connection))

        # Give it a moment
        await asyncio.sleep(0.1)
        assert not acquire_task.done()

        # Release one connection
        await pool.release(conn1)

        # Now acquire should complete
        conn3 = await acquire_task
        assert conn3 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
