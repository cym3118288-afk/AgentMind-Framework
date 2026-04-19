"""Retry utilities for LLM providers with exponential backoff.

This module provides retry logic for handling transient failures in LLM API calls.
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to delays
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ) -> None:
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


def calculate_backoff_delay(
    attempt: int,
    config: RetryConfig
) -> float:
    """Calculate delay for exponential backoff.

    Args:
        attempt: Current retry attempt number (0-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds
    """
    delay = min(
        config.initial_delay * (config.exponential_base ** attempt),
        config.max_delay
    )

    if config.jitter:
        import random
        # Add jitter: random value between 0 and delay
        delay = delay * (0.5 + random.random() * 0.5)

    return delay


def should_retry(
    exception: Exception,
    retryable_exceptions: Tuple[Type[Exception], ...]
) -> bool:
    """Determine if an exception should trigger a retry.

    Args:
        exception: The exception that occurred
        retryable_exceptions: Tuple of exception types that are retryable

    Returns:
        True if should retry, False otherwise
    """
    return isinstance(exception, retryable_exceptions)


def retry_async(
    config: Optional[RetryConfig] = None,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None
) -> Callable:
    """Decorator for adding retry logic to async functions.

    Args:
        config: Retry configuration (uses defaults if None)
        retryable_exceptions: Exceptions that should trigger retry

    Returns:
        Decorated function with retry logic

    Example:
        >>> @retry_async(config=RetryConfig(max_retries=3))
        >>> async def fetch_data():
        ...     # API call that might fail
        ...     pass
    """
    if config is None:
        config = RetryConfig()

    if retryable_exceptions is None:
        # Default retryable exceptions for HTTP/network errors
        try:
            import httpx
            retryable_exceptions = (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.NetworkError,
                ConnectionError,
            )
        except ImportError:
            retryable_exceptions = (ConnectionError,)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # Don't retry on last attempt
                    if attempt >= config.max_retries:
                        break

                    # Check if exception is retryable
                    if not should_retry(e, retryable_exceptions):
                        raise

                    # Calculate delay and wait
                    delay = calculate_backoff_delay(attempt, config)
                    logger.warning(
                        f"Attempt {attempt + 1}/{config.max_retries + 1} failed: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)

            # All retries exhausted
            logger.error(
                f"All {config.max_retries + 1} attempts failed. Last error: {str(last_exception)}"
            )
            raise last_exception

        return wrapper
    return decorator


async def retry_with_backoff(
    func: Callable,
    config: Optional[RetryConfig] = None,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    *args: Any,
    **kwargs: Any
) -> Any:
    """Execute an async function with retry logic.

    This is a functional alternative to the decorator.

    Args:
        func: Async function to execute
        config: Retry configuration
        retryable_exceptions: Exceptions that should trigger retry
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result from func

    Example:
        >>> result = await retry_with_backoff(
        ...     api_call,
        ...     config=RetryConfig(max_retries=3),
        ...     param1="value"
        ... )
    """
    if config is None:
        config = RetryConfig()

    if retryable_exceptions is None:
        try:
            import httpx
            retryable_exceptions = (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.NetworkError,
                ConnectionError,
            )
        except ImportError:
            retryable_exceptions = (ConnectionError,)

    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)

        except Exception as e:
            last_exception = e

            if attempt >= config.max_retries:
                break

            if not should_retry(e, retryable_exceptions):
                raise

            delay = calculate_backoff_delay(attempt, config)
            logger.warning(
                f"Attempt {attempt + 1}/{config.max_retries + 1} failed: {str(e)}. "
                f"Retrying in {delay:.2f}s..."
            )
            await asyncio.sleep(delay)

    logger.error(
        f"All {config.max_retries + 1} attempts failed. Last error: {str(last_exception)}"
    )
    raise last_exception
