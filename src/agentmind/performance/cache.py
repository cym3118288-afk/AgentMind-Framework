"""Caching layer for LLM responses and agent interactions.

Provides in-memory and Redis-based caching to reduce redundant LLM calls
and improve response times.
"""

import asyncio
import hashlib
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    aioredis = None
    REDIS_AVAILABLE = False


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL in seconds."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a value from cache."""

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""


class InMemoryCache(CacheBackend):
    """In-memory cache implementation with TTL support."""

    def __init__(self, max_size: int = 1000):
        """Initialize in-memory cache.

        Args:
            max_size: Maximum number of entries (LRU eviction)
        """
        self.max_size = max_size
        self._cache: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        async with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]

            # Check if expired
            if expiry is not None and time.time() > expiry:
                del self._cache[key]
                del self._access_times[key]
                return None

            # Update access time for LRU
            self._access_times[key] = time.time()
            return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL."""
        async with self._lock:
            # Evict oldest entry if at max size
            if len(self._cache) >= self.max_size and key not in self._cache:
                oldest_key = min(self._access_times, key=self._access_times.get)
                del self._cache[oldest_key]
                del self._access_times[oldest_key]

            expiry = time.time() + ttl if ttl else None
            self._cache[key] = (value, expiry)
            self._access_times[key] = time.time()

    async def delete(self, key: str) -> None:
        """Delete a value from cache."""
        async with self._lock:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._access_times.clear()

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        value = await self.get(key)
        return value is not None

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


class RedisCache(CacheBackend):
    """Redis-based cache implementation for distributed caching."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "agentmind:",
    ):
        """Initialize Redis cache.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            prefix: Key prefix for namespacing
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis package required for RedisCache. Install with: pip install redis"
            )

        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.prefix = prefix
        self._client: Optional[Any] = None

    async def _get_client(self):
        """Get or create Redis client."""
        if self._client is None:
            self._client = await aioredis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                password=self.password,
                decode_responses=True,
            )
        return self._client

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        client = await self._get_client()
        value = await client.get(self._make_key(key))
        if value is None:
            return None
        return json.loads(value)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL."""
        client = await self._get_client()
        serialized = json.dumps(value)
        if ttl:
            await client.setex(self._make_key(key), ttl, serialized)
        else:
            await client.set(self._make_key(key), serialized)

    async def delete(self, key: str) -> None:
        """Delete a value from cache."""
        client = await self._get_client()
        await client.delete(self._make_key(key))

    async def clear(self) -> None:
        """Clear all cache entries with prefix."""
        client = await self._get_client()
        pattern = f"{self.prefix}*"
        async for key in client.scan_iter(match=pattern):
            await client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        client = await self._get_client()
        return await client.exists(self._make_key(key)) > 0

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()


class CacheManager:
    """High-level cache manager for LLM responses."""

    def __init__(
        self,
        backend: Optional[CacheBackend] = None,
        default_ttl: int = 3600,
        enabled: bool = True,
    ):
        """Initialize cache manager.

        Args:
            backend: Cache backend (defaults to InMemoryCache)
            default_ttl: Default TTL in seconds
            enabled: Whether caching is enabled
        """
        self.backend = backend or InMemoryCache()
        self.default_ttl = default_ttl
        self.enabled = enabled
        self._hits = 0
        self._misses = 0

    def _generate_key(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate cache key from messages and parameters."""
        # Create deterministic hash from messages and params
        content = json.dumps(
            {"messages": messages, "params": sorted(kwargs.items())}, sort_keys=True
        )
        return hashlib.sha256(content.encode()).hexdigest()

    async def get_response(self, messages: List[Dict[str, str]], **kwargs) -> Optional[Any]:
        """Get cached LLM response.

        Args:
            messages: Message list
            **kwargs: Additional parameters used in cache key

        Returns:
            Cached response or None if not found
        """
        if not self.enabled:
            return None

        key = self._generate_key(messages, **kwargs)
        result = await self.backend.get(key)

        if result is not None:
            self._hits += 1
        else:
            self._misses += 1

        return result

    async def set_response(
        self, messages: List[Dict[str, str]], response: Any, ttl: Optional[int] = None, **kwargs
    ) -> None:
        """Cache an LLM response.

        Args:
            messages: Message list
            response: Response to cache
            ttl: TTL in seconds (uses default if None)
            **kwargs: Additional parameters used in cache key
        """
        if not self.enabled:
            return

        key = self._generate_key(messages, **kwargs)
        await self.backend.set(key, response, ttl or self.default_ttl)

    async def invalidate(self, messages: List[Dict[str, str]], **kwargs) -> None:
        """Invalidate a cached response."""
        if not self.enabled:
            return

        key = self._generate_key(messages, **kwargs)
        await self.backend.delete(key)

    async def clear(self) -> None:
        """Clear all cached responses."""
        await self.backend.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total,
            "hit_rate": hit_rate,
            "enabled": self.enabled,
        }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._hits = 0
        self._misses = 0
