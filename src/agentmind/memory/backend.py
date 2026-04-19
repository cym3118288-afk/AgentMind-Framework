"""Memory backend implementations for AgentMind.

This module provides different storage backends for agent memory:
- InMemoryBackend: Fast, volatile storage (default)
- JsonFileBackend: Persistent JSON file storage
- SQLiteBackend: Persistent SQLite database storage
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import sqlite3

from ..core.types import Message, MemoryEntry


class MemoryBackend(ABC):
    """Abstract base class for memory storage backends."""

    @abstractmethod
    async def add(self, entry: MemoryEntry) -> None:
        """Add a memory entry to storage."""
        pass

    @abstractmethod
    async def get_recent(self, limit: int) -> List[MemoryEntry]:
        """Get the most recent N memory entries."""
        pass

    @abstractmethod
    async def get_all(self) -> List[MemoryEntry]:
        """Get all memory entries."""
        pass

    @abstractmethod
    async def search_by_importance(self, min_importance: float, limit: int = 10) -> List[MemoryEntry]:
        """Search entries by minimum importance score."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all memory entries."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Get total number of entries."""
        pass


class InMemoryBackend(MemoryBackend):
    """In-memory storage backend (default, fast but volatile)."""

    def __init__(self):
        self._entries: List[MemoryEntry] = []

    async def add(self, entry: MemoryEntry) -> None:
        """Add a memory entry to storage."""
        self._entries.append(entry)

    async def get_recent(self, limit: int) -> List[MemoryEntry]:
        """Get the most recent N memory entries."""
        return self._entries[-limit:] if limit > 0 else []

    async def get_all(self) -> List[MemoryEntry]:
        """Get all memory entries."""
        return self._entries.copy()

    async def search_by_importance(self, min_importance: float, limit: int = 10) -> List[MemoryEntry]:
        """Search entries by minimum importance score."""
        filtered = [e for e in self._entries if e.importance >= min_importance]
        # Sort by importance descending
        filtered.sort(key=lambda x: x.importance, reverse=True)
        return filtered[:limit]

    async def clear(self) -> None:
        """Clear all memory entries."""
        self._entries.clear()

    async def count(self) -> int:
        """Get total number of entries."""
        return len(self._entries)


class JsonFileBackend(MemoryBackend):
    """JSON file storage backend (persistent, human-readable)."""

    def __init__(self, file_path: str):
        """Initialize with a file path.

        Args:
            file_path: Path to the JSON file for storage
        """
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: List[MemoryEntry] = []
        self._load()

    def _load(self) -> None:
        """Load entries from JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._entries = [
                        MemoryEntry(
                            message=Message(**entry['message']),
                            importance=entry.get('importance', 0.5),
                            embedding=entry.get('embedding')
                        )
                        for entry in data
                    ]
            except (json.JSONDecodeError, KeyError) as e:
                # If file is corrupted, start fresh
                self._entries = []

    def _save(self) -> None:
        """Save entries to JSON file."""
        data = []
        for entry in self._entries:
            data.append({
                'message': entry.message.model_dump(mode='json'),
                'importance': entry.importance,
                'embedding': entry.embedding
            })

        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    async def add(self, entry: MemoryEntry) -> None:
        """Add a memory entry to storage."""
        self._entries.append(entry)
        self._save()

    async def get_recent(self, limit: int) -> List[MemoryEntry]:
        """Get the most recent N memory entries."""
        return self._entries[-limit:] if limit > 0 else []

    async def get_all(self) -> List[MemoryEntry]:
        """Get all memory entries."""
        return self._entries.copy()

    async def search_by_importance(self, min_importance: float, limit: int = 10) -> List[MemoryEntry]:
        """Search entries by minimum importance score."""
        filtered = [e for e in self._entries if e.importance >= min_importance]
        filtered.sort(key=lambda x: x.importance, reverse=True)
        return filtered[:limit]

    async def clear(self) -> None:
        """Clear all memory entries."""
        self._entries.clear()
        self._save()

    async def count(self) -> int:
        """Get total number of entries."""
        return len(self._entries)


class SQLiteBackend(MemoryBackend):
    """SQLite database storage backend (persistent, efficient for large datasets)."""

    def __init__(self, db_path: str):
        """Initialize with a database path.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                sender TEXT NOT NULL,
                role TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                importance REAL DEFAULT 0.5,
                embedding TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_importance ON memory_entries(importance DESC)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON memory_entries(timestamp DESC)
        ''')

        conn.commit()
        conn.close()

    async def add(self, entry: MemoryEntry) -> None:
        """Add a memory entry to storage."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        msg = entry.message
        cursor.execute('''
            INSERT INTO memory_entries
            (content, sender, role, timestamp, metadata, importance, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            msg.content,
            msg.sender,
            msg.role.value,
            msg.timestamp.isoformat(),
            json.dumps(msg.metadata),
            entry.importance,
            json.dumps(entry.embedding) if entry.embedding else None
        ))

        conn.commit()
        conn.close()

    async def get_recent(self, limit: int) -> List[MemoryEntry]:
        """Get the most recent N memory entries."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            SELECT content, sender, role, timestamp, metadata, importance, embedding
            FROM memory_entries
            ORDER BY id DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        # Reverse to get chronological order
        entries = []
        for row in reversed(rows):
            entries.append(self._row_to_entry(row))

        return entries

    async def get_all(self) -> List[MemoryEntry]:
        """Get all memory entries."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            SELECT content, sender, role, timestamp, metadata, importance, embedding
            FROM memory_entries
            ORDER BY id ASC
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_entry(row) for row in rows]

    async def search_by_importance(self, min_importance: float, limit: int = 10) -> List[MemoryEntry]:
        """Search entries by minimum importance score."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            SELECT content, sender, role, timestamp, metadata, importance, embedding
            FROM memory_entries
            WHERE importance >= ?
            ORDER BY importance DESC
            LIMIT ?
        ''', (min_importance, limit))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_entry(row) for row in rows]

    async def clear(self) -> None:
        """Clear all memory entries."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('DELETE FROM memory_entries')
        conn.commit()
        conn.close()

    async def count(self) -> int:
        """Get total number of entries."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM memory_entries')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def _row_to_entry(self, row: tuple) -> MemoryEntry:
        """Convert database row to MemoryEntry."""
        content, sender, role, timestamp, metadata, importance, embedding = row

        return MemoryEntry(
            message=Message(
                content=content,
                sender=sender,
                role=role,
                timestamp=datetime.fromisoformat(timestamp),
                metadata=json.loads(metadata) if metadata else {}
            ),
            importance=importance,
            embedding=json.loads(embedding) if embedding else None
        )
