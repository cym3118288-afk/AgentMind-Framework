"""Streaming performance optimizations for AgentMind.

Provides optimized streaming implementations with buffering and backpressure.
"""

import asyncio
from typing import AsyncIterator, Optional, Callable, Any
from collections import deque


class StreamBuffer:
    """Buffered stream for improved streaming performance."""

    def __init__(
        self,
        buffer_size: int = 100,
        flush_interval: float = 0.1,
    ):
        """Initialize stream buffer.

        Args:
            buffer_size: Maximum buffer size before flush
            flush_interval: Time interval to flush buffer (seconds)
        """
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self._buffer: deque = deque()
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None

    async def add(self, item: Any) -> None:
        """Add item to buffer."""
        async with self._lock:
            self._buffer.append(item)

            if len(self._buffer) >= self.buffer_size:
                await self._flush()

    async def _flush(self) -> list:
        """Flush buffer and return items."""
        items = list(self._buffer)
        self._buffer.clear()
        return items

    async def get_buffered(self) -> list:
        """Get all buffered items."""
        async with self._lock:
            return await self._flush()

    async def start_auto_flush(self, callback: Callable) -> None:
        """Start automatic flushing at intervals."""
        async def auto_flush():
            while True:
                await asyncio.sleep(self.flush_interval)
                async with self._lock:
                    if self._buffer:
                        items = await self._flush()
                        await callback(items)

        self._flush_task = asyncio.create_task(auto_flush())

    async def stop_auto_flush(self) -> None:
        """Stop automatic flushing."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass


class BackpressureManager:
    """Manage backpressure in streaming operations."""

    def __init__(
        self,
        max_queue_size: int = 1000,
        high_watermark: float = 0.8,
        low_watermark: float = 0.5,
    ):
        """Initialize backpressure manager.

        Args:
            max_queue_size: Maximum queue size
            high_watermark: Threshold to apply backpressure (0.0-1.0)
            low_watermark: Threshold to release backpressure (0.0-1.0)
        """
        self.max_queue_size = max_queue_size
        self.high_watermark = int(max_queue_size * high_watermark)
        self.low_watermark = int(max_queue_size * low_watermark)
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._backpressure_active = False
        self._backpressure_event = asyncio.Event()
        self._backpressure_event.set()

    async def put(self, item: Any) -> None:
        """Put item in queue with backpressure."""
        # Wait if backpressure is active
        await self._backpressure_event.wait()

        await self._queue.put(item)

        # Check if we should apply backpressure
        if self._queue.qsize() >= self.high_watermark:
            self._backpressure_active = True
            self._backpressure_event.clear()

    async def get(self) -> Any:
        """Get item from queue and manage backpressure."""
        item = await self._queue.get()

        # Check if we should release backpressure
        if self._backpressure_active and self._queue.qsize() <= self.low_watermark:
            self._backpressure_active = False
            self._backpressure_event.set()

        return item

    def qsize(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def is_backpressure_active(self) -> bool:
        """Check if backpressure is active."""
        return self._backpressure_active


class OptimizedStreamProcessor:
    """Optimized processor for streaming LLM responses."""

    def __init__(
        self,
        chunk_size: int = 10,
        buffer_timeout: float = 0.05,
    ):
        """Initialize optimized stream processor.

        Args:
            chunk_size: Number of tokens to buffer before yielding
            buffer_timeout: Maximum time to wait before yielding buffer
        """
        self.chunk_size = chunk_size
        self.buffer_timeout = buffer_timeout

    async def process_stream(
        self,
        stream: AsyncIterator[str],
        callback: Optional[Callable[[str], None]] = None,
    ) -> AsyncIterator[str]:
        """Process stream with buffering and optimization.

        Args:
            stream: Input stream
            callback: Optional callback for each chunk

        Yields:
            Buffered chunks
        """
        buffer = []
        last_yield = asyncio.get_event_loop().time()

        async for token in stream:
            buffer.append(token)

            # Yield if buffer is full or timeout reached
            current_time = asyncio.get_event_loop().time()
            should_yield = (
                len(buffer) >= self.chunk_size or
                (current_time - last_yield) >= self.buffer_timeout
            )

            if should_yield and buffer:
                chunk = "".join(buffer)
                buffer.clear()
                last_yield = current_time

                if callback:
                    callback(chunk)

                yield chunk

        # Yield remaining buffer
        if buffer:
            chunk = "".join(buffer)
            if callback:
                callback(chunk)
            yield chunk


async def stream_with_timeout(
    stream: AsyncIterator,
    timeout: float,
    default: Any = None,
) -> AsyncIterator:
    """Add timeout to stream operations.

    Args:
        stream: Input stream
        timeout: Timeout in seconds
        default: Default value on timeout

    Yields:
        Stream items or default on timeout
    """
    async for item in stream:
        try:
            yield await asyncio.wait_for(
                asyncio.coroutine(lambda: item)(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            if default is not None:
                yield default
            break
