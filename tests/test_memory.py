"""Tests for memory backend system."""

import asyncio
import json
import tempfile
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
