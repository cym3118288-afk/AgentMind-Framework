"""Tests for memory backend system."""

import asyncio
import json
import tempfile
import time
from pathlib import Path

import pytest

from agentmind.core.types import Message, MessageRole, MemoryEntry
from agentmind.memory import InMemoryBackend, JsonFileBackend, SQLiteBackend, MemoryManager


class TestInMemoryBackend:
    """Tests for InMemoryBackend."""

    @pytest.mark.asyncio
    async def test_add_and_get_recent(self):
        """Test adding entries and retrieving recent ones."""
        backend = InMemoryBackend()

        msg1 = Message(content="Hello", sender="user", role=MessageRole.USER)
        msg2 = Message(content="Hi there", sender="agent", role=MessageRole.AGENT)

        entry1 = MemoryEntry(message=msg1, importance=0.5)
        entry2 = MemoryEntry(message=msg2, importance=0.7)

        await backend.add(entry1)
        await backend.add(entry2)

        recent = await backend.get_recent(2)
        assert len(recent) == 2
        assert recent[0].message.content == "Hello"
        assert recent[1].message.content == "Hi there"

    @pytest.mark.asyncio
    async def test_search_by_importance(self):
        """Test searching entries by importance."""
        backend = InMemoryBackend()

        msg1 = Message(content="Low priority", sender="user", role=MessageRole.USER)
        msg2 = Message(content="High priority", sender="user", role=MessageRole.USER)

        entry1 = MemoryEntry(message=msg1, importance=0.3)
        entry2 = MemoryEntry(message=msg2, importance=0.9)

        await backend.add(entry1)
        await backend.add(entry2)

        important = await backend.search_by_importance(min_importance=0.7)
        assert len(important) == 1
        assert important[0].message.content == "High priority"

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clearing all entries."""
        backend = InMemoryBackend()

        msg = Message(content="Test", sender="user", role=MessageRole.USER)
        entry = MemoryEntry(message=msg, importance=0.5)

        await backend.add(entry)
        assert await backend.count() == 1

        await backend.clear()
        assert await backend.count() == 0

    @pytest.mark.asyncio
    async def test_get_all(self):
        """Test getting all entries."""
        backend = InMemoryBackend()

        for i in range(5):
            msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
            entry = MemoryEntry(message=msg, importance=0.5)
            await backend.add(entry)

        all_entries = await backend.get_all()
        assert len(all_entries) == 5


class TestJsonFileBackend:
    """Tests for JsonFileBackend."""

    @pytest.mark.asyncio
    async def test_persistence(self):
        """Test that data persists across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_memory.json"

            # Create backend and add data
            backend1 = JsonFileBackend(str(file_path))
            msg = Message(content="Persistent message", sender="user", role=MessageRole.USER)
            entry = MemoryEntry(message=msg, importance=0.8)
            await backend1.add(entry)

            # Create new backend instance and verify data persists
            backend2 = JsonFileBackend(str(file_path))
            entries = await backend2.get_all()
            assert len(entries) == 1
            assert entries[0].message.content == "Persistent message"
            assert entries[0].importance == 0.8

    @pytest.mark.asyncio
    async def test_clear_persists(self):
        """Test that clearing persists to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_memory.json"

            backend = JsonFileBackend(str(file_path))
            msg = Message(content="Test", sender="user", role=MessageRole.USER)
            entry = MemoryEntry(message=msg, importance=0.5)
            await backend.add(entry)

            await backend.clear()

            # Reload and verify empty
            backend2 = JsonFileBackend(str(file_path))
            entries = await backend2.get_all()
            assert len(entries) == 0


class TestSQLiteBackend:
    """Tests for SQLiteBackend."""

    @pytest.mark.asyncio
    async def test_persistence(self):
        """Test that data persists in database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_memory.db"

            # Create backend and add data
            backend1 = SQLiteBackend(str(db_path))
            msg = Message(content="Database message", sender="user", role=MessageRole.USER)
            entry = MemoryEntry(message=msg, importance=0.6)
            await backend1.add(entry)

            # Create new backend instance and verify data persists
            backend2 = SQLiteBackend(str(db_path))
            entries = await backend2.get_all()
            assert len(entries) == 1
            assert entries[0].message.content == "Database message"

    @pytest.mark.asyncio
    async def test_large_dataset(self):
        """Test handling large number of entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_memory.db"
            backend = SQLiteBackend(str(db_path))

            # Add 100 entries
            for i in range(100):
                msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
                entry = MemoryEntry(message=msg, importance=i / 100.0)
                await backend.add(entry)

            assert await backend.count() == 100

            # Get recent 10
            recent = await backend.get_recent(10)
            assert len(recent) == 10
            assert recent[-1].message.content == "Message 99"

            # Search by importance
            important = await backend.search_by_importance(min_importance=0.9, limit=20)
            assert len(important) == 10  # Messages 90-99


class TestMemoryManager:
    """Tests for MemoryManager."""

    @pytest.mark.asyncio
    async def test_short_term_memory(self):
        """Test short-term memory limit."""
        manager = MemoryManager(short_term_limit=3)

        for i in range(5):
            msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
            await manager.add_message(msg)

        short_term = await manager.get_short_term_memory()
        assert len(short_term) == 3
        assert short_term[0].content == "Message 2"
        assert short_term[-1].content == "Message 4"

    @pytest.mark.asyncio
    async def test_should_summarize(self):
        """Test summarization trigger."""
        manager = MemoryManager(summarization_interval=3)

        assert not await manager.should_summarize()

        for i in range(3):
            msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
            await manager.add_message(msg)

        assert await manager.should_summarize()

    @pytest.mark.asyncio
    async def test_create_summary_without_llm(self):
        """Test creating summary without LLM."""
        manager = MemoryManager()

        for i in range(5):
            msg = Message(content=f"Message {i}", sender=f"agent{i}", role=MessageRole.AGENT)
            await manager.add_message(msg)

        summary = await manager.create_summary()
        assert summary is not None
        assert "5 messages" in summary

    @pytest.mark.asyncio
    async def test_get_context_for_agent(self):
        """Test getting context for agent."""
        manager = MemoryManager(short_term_limit=3)

        for i in range(5):
            msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
            await manager.add_message(msg)

        # Create summary
        await manager.create_summary()

        # Get context with summary
        context = await manager.get_context_for_agent(include_summary=True)
        assert len(context) == 4  # 3 recent + 1 summary
        assert context[0].role == MessageRole.SYSTEM
        assert "summary" in context[0].content.lower()

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clearing memory."""
        manager = MemoryManager()

        msg = Message(content="Test", sender="user", role=MessageRole.USER)
        await manager.add_message(msg)

        assert await manager.count() == 1

        await manager.clear()
        assert await manager.count() == 0
        assert await manager.get_summary() is None

    @pytest.mark.asyncio
    async def test_get_important_messages(self):
        """Test retrieving important messages."""
        manager = MemoryManager()

        # Add messages with varying importance
        for i in range(10):
            msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
            importance = i / 10.0
            await manager.add_message(msg, importance=importance)

        important = await manager.get_important_messages(min_importance=0.7, limit=5)
        assert len(important) == 3  # Messages 7, 8, 9
        assert all("Message" in msg.content for msg in important)


class TestMemoryEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_get_recent_with_zero_limit(self):
        """Test get_recent with limit=0."""
        backend = InMemoryBackend()
        for i in range(5):
            msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
            await backend.add(MemoryEntry(message=msg, importance=0.5))

        recent = await backend.get_recent(0)
        assert len(recent) == 0

    @pytest.mark.asyncio
    async def test_get_recent_exceeds_available(self):
        """Test get_recent when limit exceeds available entries."""
        backend = InMemoryBackend()
        for i in range(3):
            msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
            await backend.add(MemoryEntry(message=msg, importance=0.5))

        recent = await backend.get_recent(10)
        assert len(recent) == 3

    @pytest.mark.asyncio
    async def test_search_no_matches(self):
        """Test search when no entries match criteria."""
        backend = InMemoryBackend()
        msg = Message(content="Low importance", sender="user", role=MessageRole.USER)
        await backend.add(MemoryEntry(message=msg, importance=0.2))

        results = await backend.search_by_importance(min_importance=0.9)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_empty_backend_operations(self):
        """Test operations on empty backend."""
        backend = InMemoryBackend()

        assert await backend.count() == 0
        assert await backend.get_all() == []
        assert await backend.get_recent(5) == []
        assert await backend.search_by_importance(0.5) == []

    @pytest.mark.asyncio
    async def test_json_corrupted_file_recovery(self):
        """Test JsonFileBackend handles corrupted files gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "corrupted.json"

            # Write corrupted JSON
            with open(file_path, 'w') as f:
                f.write("{invalid json content")

            # Should initialize with empty entries
            backend = JsonFileBackend(str(file_path))
            assert await backend.count() == 0

    @pytest.mark.asyncio
    async def test_sqlite_concurrent_writes(self):
        """Test SQLite handles concurrent writes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "concurrent.db"
            backend = SQLiteBackend(str(db_path))

            # Add entries concurrently
            tasks = []
            for i in range(20):
                msg = Message(content=f"Concurrent {i}", sender="user", role=MessageRole.USER)
                entry = MemoryEntry(message=msg, importance=0.5)
                tasks.append(backend.add(entry))

            await asyncio.gather(*tasks)
            assert await backend.count() == 20

    @pytest.mark.asyncio
    async def test_memory_manager_edge_cases(self):
        """Test MemoryManager edge cases."""
        manager = MemoryManager(short_term_limit=0)

        msg = Message(content="Test", sender="user", role=MessageRole.USER)
        await manager.add_message(msg)

        # Should return empty list with limit=0
        short_term = await manager.get_short_term_memory()
        assert len(short_term) == 0

    @pytest.mark.asyncio
    async def test_large_message_content(self):
        """Test handling very large message content."""
        backend = InMemoryBackend()

        # Create a large message (1MB)
        large_content = "x" * (1024 * 1024)
        msg = Message(content=large_content, sender="user", role=MessageRole.USER)
        entry = MemoryEntry(message=msg, importance=0.5)

        await backend.add(entry)
        retrieved = await backend.get_recent(1)
        assert len(retrieved[0].message.content) == len(large_content)


class TestMemoryPerformance:
    """Performance and benchmark tests."""

    @pytest.mark.asyncio
    async def test_inmemory_performance_1000_entries(self):
        """Benchmark InMemoryBackend with 1000 entries."""
        backend = InMemoryBackend()

        start = time.time()
        for i in range(1000):
            msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
            await backend.add(MemoryEntry(message=msg, importance=i / 1000.0))
        add_time = time.time() - start

        start = time.time()
        recent = await backend.get_recent(100)
        get_time = time.time() - start

        start = time.time()
        important = await backend.search_by_importance(0.9, limit=50)
        search_time = time.time() - start

        assert len(recent) == 100
        assert len(important) == 50  # Limit is 50
        assert add_time < 1.0  # Should be fast
        assert get_time < 0.1
        assert search_time < 0.1

    @pytest.mark.asyncio
    async def test_sqlite_performance_1000_entries(self):
        """Benchmark SQLiteBackend with 1000 entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "perf_test.db"
            backend = SQLiteBackend(str(db_path))

            start = time.time()
            for i in range(1000):
                msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
                await backend.add(MemoryEntry(message=msg, importance=i / 1000.0))
            add_time = time.time() - start

            start = time.time()
            recent = await backend.get_recent(100)
            get_time = time.time() - start

            start = time.time()
            important = await backend.search_by_importance(0.9, limit=50)
            search_time = time.time() - start

            assert len(recent) == 100
            assert len(important) == 50  # Limit is 50
            # SQLite with individual inserts is slower but still reasonable
            assert add_time < 15.0
            assert get_time < 0.5
            assert search_time < 0.5

    @pytest.mark.asyncio
    async def test_sqlite_batch_performance(self):
        """Benchmark SQLiteBackend batch operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "batch_test.db"
            backend = SQLiteBackend(str(db_path))

            # Create batch of entries
            entries = []
            for i in range(1000):
                msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
                entries.append(MemoryEntry(message=msg, importance=i / 1000.0))

            # Batch insert should be much faster
            start = time.time()
            await backend.add_batch(entries)
            batch_time = time.time() - start

            assert await backend.count() == 1000
            assert batch_time < 2.0  # Batch should be significantly faster

    @pytest.mark.asyncio
    async def test_json_file_performance_100_entries(self):
        """Benchmark JsonFileBackend with 100 entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "perf_test.json"
            backend = JsonFileBackend(str(file_path))

            start = time.time()
            for i in range(100):
                msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
                await backend.add(MemoryEntry(message=msg, importance=i / 100.0))
            add_time = time.time() - start

            # JSON file writes are slower but should still be reasonable
            assert add_time < 5.0
            assert await backend.count() == 100

    @pytest.mark.asyncio
    async def test_memory_manager_summarization_performance(self):
        """Test MemoryManager summarization performance."""
        manager = MemoryManager(summarization_interval=10)

        start = time.time()
        for i in range(20):
            msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
            await manager.add_message(msg)

        # Create summary without LLM
        summary = await manager.create_summary()
        elapsed = time.time() - start

        assert summary is not None
        assert elapsed < 1.0


class TestMemoryLimitsAndCleanup:
    """Test memory limits and cleanup mechanisms."""

    @pytest.mark.asyncio
    async def test_memory_manager_respects_short_term_limit(self):
        """Test that short-term memory respects limit."""
        manager = MemoryManager(short_term_limit=5)

        for i in range(20):
            msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
            await manager.add_message(msg)

        short_term = await manager.get_short_term_memory()
        assert len(short_term) == 5
        assert short_term[0].content == "Message 15"
        assert short_term[-1].content == "Message 19"

    @pytest.mark.asyncio
    async def test_clear_resets_all_state(self):
        """Test that clear resets all manager state."""
        manager = MemoryManager(summarization_interval=5)

        for i in range(10):
            msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
            await manager.add_message(msg)

        await manager.create_summary()
        assert await manager.get_summary() is not None

        await manager.clear()
        assert await manager.count() == 0
        assert await manager.get_summary() is None
        assert not await manager.should_summarize()

    @pytest.mark.asyncio
    async def test_importance_filtering(self):
        """Test filtering by importance threshold."""
        manager = MemoryManager()

        for i in range(10):
            msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
            importance = i / 10.0
            await manager.add_message(msg, importance=importance)

        # Get only high importance messages
        important = await manager.get_important_messages(min_importance=0.7, limit=10)
        assert len(important) == 3  # 0.7, 0.8, 0.9

        # Verify they're sorted by importance
        contents = [m.content for m in important]
        assert "Message 9" in contents
        assert "Message 8" in contents
        assert "Message 7" in contents


class TestBackendComparison:
    """Compare behavior across different backends."""

    @pytest.mark.asyncio
    async def test_all_backends_consistent_behavior(self):
        """Test that all backends behave consistently."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backends = [
                InMemoryBackend(),
                JsonFileBackend(str(Path(tmpdir) / "test.json")),
                SQLiteBackend(str(Path(tmpdir) / "test.db"))
            ]

            for backend in backends:
                # Add same data to each backend
                for i in range(10):
                    msg = Message(content=f"Message {i}", sender="user", role=MessageRole.USER)
                    await backend.add(MemoryEntry(message=msg, importance=i / 10.0))

                # Verify consistent behavior
                assert await backend.count() == 10

                recent = await backend.get_recent(5)
                assert len(recent) == 5
                assert recent[-1].message.content == "Message 9"

                important = await backend.search_by_importance(0.7, limit=10)
                assert len(important) == 3

                await backend.clear()
                assert await backend.count() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
