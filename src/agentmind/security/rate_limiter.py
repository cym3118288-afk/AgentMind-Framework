"""Rate limiting for API requests."""

import asyncio
import time
from collections import defaultdict
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: float):
        """Initialize exception.

        Args:
            message: Error message
            retry_after: Seconds until retry is allowed
        """
        super().__init__(message)
        self.retry_after = retry_after


class RateLimiter:
    """Rate limiter using token bucket algorithm."""

    def __init__(
        self,
        max_requests: int = 100,
        time_window: float = 60.0,
        burst_size: Optional[int] = None
    ):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests per time window
            time_window: Time window in seconds
            burst_size: Maximum burst size (defaults to max_requests)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst_size = burst_size or max_requests

        # Track requests per identifier
        self._buckets: Dict[str, Tuple[float, int]] = {}
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limit.

        Args:
            identifier: Unique identifier (e.g., user ID, IP address)

        Returns:
            True if within limit, False otherwise

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        async with self._lock:
            now = time.time()

            if identifier not in self._buckets:
                # First request
                self._buckets[identifier] = (now, 1)
                return True

            last_time, count = self._buckets[identifier]
            time_passed = now - last_time

            # Refill tokens based on time passed
            tokens_to_add = (time_passed / self.time_window) * self.max_requests
            current_tokens = min(self.burst_size, count + int(tokens_to_add))

            if current_tokens >= 1:
                # Allow request
                self._buckets[identifier] = (now, current_tokens - 1)
                return True
            else:
                # Rate limit exceeded
                retry_after = (1 - current_tokens) * (self.time_window / self.max_requests)
                raise RateLimitExceeded(
                    f"Rate limit exceeded for {identifier}",
                    retry_after=retry_after
                )

    async def acquire(self, identifier: str, wait: bool = False) -> bool:
        """Acquire permission to make a request.

        Args:
            identifier: Unique identifier
            wait: If True, wait until rate limit allows request

        Returns:
            True if acquired, False if rate limited (when wait=False)

        Raises:
            RateLimitExceeded: If rate limited and wait=False
        """
        while True:
            try:
                await self.check_rate_limit(identifier)
                return True
            except RateLimitExceeded as e:
                if not wait:
                    raise
                logger.info(f"Rate limited, waiting {e.retry_after:.2f}s")
                await asyncio.sleep(e.retry_after)

    def reset(self, identifier: str) -> None:
        """Reset rate limit for identifier.

        Args:
            identifier: Unique identifier
        """
        if identifier in self._buckets:
            del self._buckets[identifier]

    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Number of remaining requests
        """
        if identifier not in self._buckets:
            return self.max_requests

        now = time.time()
        last_time, count = self._buckets[identifier]
        time_passed = now - last_time

        tokens_to_add = (time_passed / self.time_window) * self.max_requests
        current_tokens = min(self.burst_size, count + int(tokens_to_add))

        return max(0, int(current_tokens))

    def cleanup_old_entries(self, max_age: float = 3600.0) -> int:
        """Clean up old entries.

        Args:
            max_age: Maximum age in seconds

        Returns:
            Number of entries removed
        """
        now = time.time()
        to_remove = []

        for identifier, (last_time, _) in self._buckets.items():
            if now - last_time > max_age:
                to_remove.append(identifier)

        for identifier in to_remove:
            del self._buckets[identifier]

        return len(to_remove)


class SlidingWindowRateLimiter:
    """Rate limiter using sliding window algorithm."""

    def __init__(self, max_requests: int = 100, time_window: float = 60.0):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests per time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window

        # Track request timestamps per identifier
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limit.

        Args:
            identifier: Unique identifier

        Returns:
            True if within limit

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        async with self._lock:
            now = time.time()
            cutoff = now - self.time_window

            # Remove old requests
            self._requests[identifier] = [
                ts for ts in self._requests[identifier]
                if ts > cutoff
            ]

            if len(self._requests[identifier]) < self.max_requests:
                # Allow request
                self._requests[identifier].append(now)
                return True
            else:
                # Rate limit exceeded
                oldest = self._requests[identifier][0]
                retry_after = oldest + self.time_window - now
                raise RateLimitExceeded(
                    f"Rate limit exceeded for {identifier}",
                    retry_after=retry_after
                )

    async def acquire(self, identifier: str, wait: bool = False) -> bool:
        """Acquire permission to make a request.

        Args:
            identifier: Unique identifier
            wait: If True, wait until rate limit allows request

        Returns:
            True if acquired

        Raises:
            RateLimitExceeded: If rate limited and wait=False
        """
        while True:
            try:
                await self.check_rate_limit(identifier)
                return True
            except RateLimitExceeded as e:
                if not wait:
                    raise
                await asyncio.sleep(e.retry_after)

    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Number of remaining requests
        """
        now = time.time()
        cutoff = now - self.time_window

        # Count recent requests
        recent = sum(1 for ts in self._requests[identifier] if ts > cutoff)
        return max(0, self.max_requests - recent)

    def reset(self, identifier: str) -> None:
        """Reset rate limit for identifier.

        Args:
            identifier: Unique identifier
        """
        if identifier in self._requests:
            del self._requests[identifier]


class AdaptiveRateLimiter:
    """Rate limiter that adapts based on system load."""

    def __init__(
        self,
        base_max_requests: int = 100,
        time_window: float = 60.0,
        min_requests: int = 10,
        max_requests: int = 1000
    ):
        """Initialize adaptive rate limiter.

        Args:
            base_max_requests: Base maximum requests
            time_window: Time window in seconds
            min_requests: Minimum allowed requests
            max_requests: Maximum allowed requests
        """
        self.base_max_requests = base_max_requests
        self.time_window = time_window
        self.min_requests = min_requests
        self.max_requests = max_requests

        self.current_max = base_max_requests
        self._limiter = RateLimiter(base_max_requests, time_window)

    def adjust_limit(self, load_factor: float) -> None:
        """Adjust rate limit based on load.

        Args:
            load_factor: Load factor (0.0 to 1.0, where 1.0 is full load)
        """
        # Decrease limit as load increases
        adjusted = int(self.base_max_requests * (1.0 - load_factor * 0.5))
        self.current_max = max(
            self.min_requests,
            min(self.max_requests, adjusted)
        )

        # Update limiter
        self._limiter.max_requests = self.current_max
        logger.info(f"Adjusted rate limit to {self.current_max} requests")

    async def check_rate_limit(self, identifier: str) -> bool:
        """Check rate limit."""
        return await self._limiter.check_rate_limit(identifier)

    async def acquire(self, identifier: str, wait: bool = False) -> bool:
        """Acquire permission."""
        return await self._limiter.acquire(identifier, wait)

    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests."""
        return self._limiter.get_remaining(identifier)

    def reset(self, identifier: str) -> None:
        """Reset rate limit."""
        self._limiter.reset(identifier)
