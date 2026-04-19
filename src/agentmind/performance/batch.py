"""Batch processing for multiple agent tasks.

Enables efficient processing of multiple tasks in parallel with
resource management and error handling.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, TypeVar
from dataclasses import dataclass
from datetime import datetime

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class BatchResult:
    """Result of a batch operation."""

    task_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    duration: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BatchProcessor:
    """Process multiple tasks in batches with concurrency control."""

    def __init__(
        self,
        max_concurrent: int = 10,
        timeout: Optional[float] = None,
        retry_failed: bool = False,
        max_retries: int = 3,
    ):
        """Initialize batch processor.

        Args:
            max_concurrent: Maximum concurrent tasks
            timeout: Timeout per task in seconds
            retry_failed: Whether to retry failed tasks
            max_retries: Maximum retry attempts
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.retry_failed = retry_failed
        self.max_retries = max_retries
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def _process_single(
        self,
        task_id: str,
        func: Callable,
        *args,
        **kwargs
    ) -> BatchResult:
        """Process a single task with error handling."""
        start_time = asyncio.get_event_loop().time()

        async with self._semaphore:
            try:
                if self.timeout:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=self.timeout
                    )
                else:
                    result = await func(*args, **kwargs)

                duration = asyncio.get_event_loop().time() - start_time
                return BatchResult(
                    task_id=task_id,
                    success=True,
                    result=result,
                    duration=duration
                )

            except asyncio.TimeoutError:
                duration = asyncio.get_event_loop().time() - start_time
                return BatchResult(
                    task_id=task_id,
                    success=False,
                    error=f"Task timed out after {self.timeout}s",
                    duration=duration
                )

            except Exception as e:
                duration = asyncio.get_event_loop().time() - start_time
                return BatchResult(
                    task_id=task_id,
                    success=False,
                    error=str(e),
                    duration=duration
                )

    async def process_batch(
        self,
        tasks: List[Dict[str, Any]],
        func: Callable,
    ) -> List[BatchResult]:
        """Process a batch of tasks.

        Args:
            tasks: List of task dicts with 'id' and task parameters
            func: Async function to call for each task

        Returns:
            List of BatchResult objects

        Example:
            >>> async def process_message(message: str) -> str:
            ...     return f"Processed: {message}"
            >>>
            >>> processor = BatchProcessor(max_concurrent=5)
            >>> tasks = [
            ...     {"id": "1", "message": "Hello"},
            ...     {"id": "2", "message": "World"},
            ... ]
            >>> results = await processor.process_batch(tasks, process_message)
        """
        # Create coroutines for all tasks
        coroutines = []
        for task in tasks:
            task_id = task.pop("id", str(len(coroutines)))
            coro = self._process_single(task_id, func, **task)
            coroutines.append(coro)

        # Execute all tasks concurrently
        results = await asyncio.gather(*coroutines, return_exceptions=False)

        # Retry failed tasks if enabled
        if self.retry_failed:
            results = await self._retry_failed(results, tasks, func)

        return results

    async def _retry_failed(
        self,
        results: List[BatchResult],
        tasks: List[Dict[str, Any]],
        func: Callable,
    ) -> List[BatchResult]:
        """Retry failed tasks."""
        failed_indices = [i for i, r in enumerate(results) if not r.success]

        for retry_num in range(self.max_retries):
            if not failed_indices:
                break

            # Retry failed tasks
            retry_tasks = [tasks[i] for i in failed_indices]
            retry_results = await asyncio.gather(
                *[self._process_single(
                    f"{tasks[i].get('id', i)}_retry{retry_num}",
                    func,
                    **tasks[i]
                ) for i in failed_indices],
                return_exceptions=False
            )

            # Update results
            new_failed = []
            for idx, result in zip(failed_indices, retry_results):
                if result.success:
                    results[idx] = result
                else:
                    new_failed.append(idx)

            failed_indices = new_failed

        return results

    async def process_stream(
        self,
        task_stream: asyncio.Queue,
        func: Callable,
        result_callback: Optional[Callable[[BatchResult], None]] = None,
    ) -> None:
        """Process tasks from a stream/queue.

        Args:
            task_stream: Queue of tasks to process
            func: Async function to call for each task
            result_callback: Optional callback for each result
        """
        async def worker():
            while True:
                try:
                    task = await task_stream.get()
                    if task is None:  # Sentinel value to stop
                        break

                    task_id = task.pop("id", "unknown")
                    result = await self._process_single(task_id, func, **task)

                    if result_callback:
                        await result_callback(result)

                    task_stream.task_done()

                except Exception as e:
                    print(f"Worker error: {e}")

        # Start workers
        workers = [asyncio.create_task(worker()) for _ in range(self.max_concurrent)]

        # Wait for all tasks to complete
        await task_stream.join()

        # Stop workers
        for _ in range(self.max_concurrent):
            await task_stream.put(None)

        await asyncio.gather(*workers)

    def get_stats(self, results: List[BatchResult]) -> Dict[str, Any]:
        """Get statistics from batch results.

        Args:
            results: List of batch results

        Returns:
            Statistics dictionary
        """
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful

        durations = [r.duration for r in results]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0

        return {
            "total_tasks": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "avg_duration": avg_duration,
            "max_duration": max_duration,
            "min_duration": min_duration,
            "total_duration": sum(durations),
        }
