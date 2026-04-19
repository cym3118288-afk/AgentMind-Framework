"""Property-based tests using Hypothesis for AgentMind.

These tests use property-based testing to verify system behavior
across a wide range of inputs and edge cases.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant

from agentmind.core.types import Message, AgentConfig, MessageRole
from agentmind.performance.cache import InMemoryCache, CacheManager
from agentmind.performance.batch import BatchProcessor
from agentmind.performance.memory_optimizer import MemoryOptimizer


# Strategies for generating test data
message_strategy = st.builds(
    Message,
    role=st.sampled_from(["user", "assistant", "system"]),
    content=st.text(min_size=1, max_size=1000),
    sender=st.text(min_size=1, max_size=50),
)

agent_config_strategy = st.builds(
    AgentConfig,
    name=st.text(min_size=1, max_size=50),
    role=st.text(min_size=1, max_size=50),
    system_prompt=st.text(max_size=500),
    temperature=st.floats(min_value=0.0, max_value=2.0),
    max_tokens=st.integers(min_value=1, max_value=4000),
)


class TestMessageProperties:
    """Property-based tests for Message type."""

    @given(message_strategy)
    def test_message_creation(self, message):
        """Test that any valid message can be created."""
        assert isinstance(message, Message)
        assert len(message.content) > 0
        assert len(message.sender) > 0
        assert message.role in ["user", "assistant", "system"]

    @given(st.lists(message_strategy, min_size=0, max_size=100))
    def test_message_list_operations(self, messages):
        """Test operations on message lists."""
        # Should be able to filter by role
        user_messages = [m for m in messages if m.role == "user"]
        assert all(m.role == "user" for m in user_messages)

        # Should be able to get unique senders
        senders = set(m.sender for m in messages)
        assert len(senders) <= len(messages)

    @given(
        role=st.sampled_from(["user", "assistant", "system"]),
        content=st.text(min_size=1),
        sender=st.text(min_size=1),
    )
    def test_message_immutability(self, role, content, sender):
        """Test that message fields are properly set."""
        message = Message(role=role, content=content, sender=sender)
        assert message.role == role
        assert message.content == content
        assert message.sender == sender


class TestAgentConfigProperties:
    """Property-based tests for AgentConfig."""

    @given(agent_config_strategy)
    def test_agent_config_creation(self, config):
        """Test that any valid config can be created."""
        assert isinstance(config, AgentConfig)
        assert len(config.name) > 0
        assert 0.0 <= config.temperature <= 2.0
        assert config.max_tokens > 0

    @given(
        name=st.text(min_size=1, max_size=50),
        temperature=st.floats(min_value=0.0, max_value=2.0),
    )
    def test_temperature_bounds(self, name, temperature):
        """Test that temperature is always within valid bounds."""
        config = AgentConfig(name=name, role="test", temperature=temperature)
        assert 0.0 <= config.temperature <= 2.0


class TestCacheProperties:
    """Property-based tests for caching."""

    @pytest.mark.asyncio
    @given(
        key=st.text(min_size=1, max_size=100),
        value=st.text(max_size=1000),
    )
    @settings(max_examples=50)
    async def test_cache_set_get_consistency(self, key, value):
        """Test that cached values can always be retrieved."""
        cache = InMemoryCache()
        await cache.set(key, value)
        retrieved = await cache.get(key)
        assert retrieved == value

    @pytest.mark.asyncio
    @given(
        keys=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=20, unique=True),
        values=st.lists(st.text(max_size=100), min_size=1, max_size=20),
    )
    @settings(max_examples=30)
    async def test_cache_multiple_keys(self, keys, values):
        """Test cache with multiple keys."""
        assume(len(keys) == len(values))

        cache = InMemoryCache(max_size=100)

        # Set all values
        for key, value in zip(keys, values):
            await cache.set(key, value)

        # Retrieve and verify
        for key, expected_value in zip(keys, values):
            retrieved = await cache.get(key)
            assert retrieved == expected_value

    @pytest.mark.asyncio
    @given(
        messages=st.lists(
            st.dictionaries(
                st.sampled_from(["role", "content"]),
                st.text(min_size=1, max_size=100),
                min_size=2,
                max_size=2,
            ),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=30)
    async def test_cache_manager_key_generation(self, messages):
        """Test that cache key generation is deterministic."""
        manager = CacheManager()

        key1 = manager._generate_key(messages)
        key2 = manager._generate_key(messages)

        # Same input should generate same key
        assert key1 == key2

        # Key should be a valid hash
        assert len(key1) == 64  # SHA256 hex digest


class TestMemoryOptimizerProperties:
    """Property-based tests for memory optimization."""

    @pytest.mark.asyncio
    @given(
        messages=st.lists(message_strategy, min_size=1, max_size=200),
        max_messages=st.integers(min_value=10, max_value=100),
        sliding_window=st.integers(min_value=5, max_value=50),
    )
    @settings(max_examples=30, deadline=1000)
    async def test_optimizer_reduces_memory(self, messages, max_messages, sliding_window):
        """Test that optimizer always reduces memory when needed."""
        assume(sliding_window <= max_messages)

        optimizer = MemoryOptimizer(
            max_messages=max_messages,
            sliding_window=sliding_window
        )

        optimized = await optimizer.optimize(messages, strategy="sliding_window")

        # Should not exceed max_messages
        if len(messages) > max_messages:
            assert len(optimized) <= max_messages

        # Should preserve some messages
        assert len(optimized) > 0

    @pytest.mark.asyncio
    @given(
        messages=st.lists(message_strategy, min_size=1, max_size=50),
    )
    @settings(max_examples=30)
    async def test_optimizer_preserves_recent(self, messages):
        """Test that optimizer preserves recent messages."""
        optimizer = MemoryOptimizer(max_messages=100, sliding_window=10)

        optimized = await optimizer.optimize(messages, strategy="sliding_window")

        # If we have messages, last message should be preserved
        if messages:
            assert optimized[-1].content == messages[-1].content


class TestBatchProcessorProperties:
    """Property-based tests for batch processing."""

    @pytest.mark.asyncio
    @given(
        task_count=st.integers(min_value=1, max_value=50),
        max_concurrent=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=20, deadline=2000)
    async def test_batch_processes_all_tasks(self, task_count, max_concurrent):
        """Test that batch processor handles all tasks."""
        async def simple_task(value: int) -> int:
            return value * 2

        processor = BatchProcessor(max_concurrent=max_concurrent)
        tasks = [{"id": str(i), "value": i} for i in range(task_count)]

        results = await processor.process_batch(tasks, simple_task)

        # Should process all tasks
        assert len(results) == task_count

        # All should succeed
        assert all(r.success for r in results)

        # Results should be correct
        assert [r.result for r in results] == [i * 2 for i in range(task_count)]

    @pytest.mark.asyncio
    @given(
        task_count=st.integers(min_value=1, max_value=30),
    )
    @settings(max_examples=20, deadline=2000)
    async def test_batch_stats_consistency(self, task_count):
        """Test that batch statistics are consistent."""
        async def simple_task(value: int) -> int:
            return value

        processor = BatchProcessor(max_concurrent=5)
        tasks = [{"id": str(i), "value": i} for i in range(task_count)]

        results = await processor.process_batch(tasks, simple_task)
        stats = processor.get_stats(results)

        # Stats should be consistent
        assert stats["total_tasks"] == task_count
        assert stats["successful"] + stats["failed"] == task_count
        assert 0.0 <= stats["success_rate"] <= 1.0
        assert stats["avg_duration"] >= 0


class CacheStateMachine(RuleBasedStateMachine):
    """Stateful testing for cache operations."""

    def __init__(self):
        super().__init__()
        self.cache = None
        self.expected_state = {}

    @rule()
    def initialize_cache(self):
        """Initialize a new cache."""
        self.cache = InMemoryCache(max_size=100)
        self.expected_state = {}

    @rule(
        key=st.text(min_size=1, max_size=50),
        value=st.text(max_size=100),
    )
    async def set_value(self, key, value):
        """Set a value in cache."""
        if self.cache is None:
            self.initialize_cache()

        await self.cache.set(key, value)
        self.expected_state[key] = value

    @rule(key=st.text(min_size=1, max_size=50))
    async def get_value(self, key):
        """Get a value from cache."""
        if self.cache is None:
            return

        result = await self.cache.get(key)
        expected = self.expected_state.get(key)

        if expected is not None:
            assert result == expected

    @rule(key=st.text(min_size=1, max_size=50))
    async def delete_value(self, key):
        """Delete a value from cache."""
        if self.cache is None:
            return

        await self.cache.delete(key)
        self.expected_state.pop(key, None)

    @invariant()
    def cache_size_reasonable(self):
        """Cache size should never exceed max_size."""
        if self.cache is not None:
            assert self.cache.size() <= 100


# Note: Stateful tests need to be run differently
# TestCacheStateMachine.TestCase.settings = settings(max_examples=50, stateful_step_count=10)


class TestEdgeCases:
    """Property-based tests for edge cases."""

    @pytest.mark.asyncio
    @given(st.lists(message_strategy, min_size=0, max_size=0))
    async def test_empty_message_list(self, messages):
        """Test handling of empty message lists."""
        optimizer = MemoryOptimizer()
        optimized = await optimizer.optimize(messages, strategy="sliding_window")
        assert len(optimized) == 0

    @pytest.mark.asyncio
    @given(
        content=st.text(min_size=10000, max_size=50000),
    )
    @settings(max_examples=5)
    async def test_large_message_content(self, content):
        """Test handling of very large messages."""
        message = Message(role="user", content=content, sender="user")
        assert len(message.content) >= 10000

        # Should be able to store in cache
        cache = InMemoryCache()
        await cache.set("large", message)
        retrieved = await cache.get("large")
        assert retrieved.content == content

    @pytest.mark.asyncio
    @given(
        key=st.text(min_size=1, max_size=10),
        ttl=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=10, deadline=6000)
    async def test_cache_ttl_expiration(self, key, ttl):
        """Test that cache TTL works correctly."""
        import asyncio

        cache = InMemoryCache()
        await cache.set(key, "value", ttl=ttl)

        # Should exist immediately
        assert await cache.exists(key)

        # Wait for expiration
        await asyncio.sleep(ttl + 0.5)

        # Should be expired
        assert not await cache.exists(key)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
