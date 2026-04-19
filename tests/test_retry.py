"""Tests for retry utilities."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentmind.llm.retry import (
    RetryConfig,
    calculate_backoff_delay,
    retry_async,
    retry_with_backoff,
    should_retry,
)


class TestRetryConfig:
    """Test RetryConfig class."""

    def test_default_config(self) -> None:
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_custom_config(self) -> None:
        """Test custom retry configuration."""
        config = RetryConfig(
            max_retries=5,
            initial_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False
        )
        assert config.max_retries == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 3.0
        assert config.jitter is False


class TestBackoffCalculation:
    """Test backoff delay calculation."""

    def test_exponential_backoff_no_jitter(self) -> None:
        """Test exponential backoff without jitter."""
        config = RetryConfig(initial_delay=1.0, exponential_base=2.0, jitter=False)

        assert calculate_backoff_delay(0, config) == 1.0
        assert calculate_backoff_delay(1, config) == 2.0
        assert calculate_backoff_delay(2, config) == 4.0
        assert calculate_backoff_delay(3, config) == 8.0

    def test_max_delay_cap(self) -> None:
        """Test that delay is capped at max_delay."""
        config = RetryConfig(initial_delay=1.0, max_delay=5.0, jitter=False)

        assert calculate_backoff_delay(10, config) == 5.0

    def test_jitter_adds_randomness(self) -> None:
        """Test that jitter adds randomness to delay."""
        config = RetryConfig(initial_delay=1.0, jitter=True)

        delays = [calculate_backoff_delay(1, config) for _ in range(10)]

        # With jitter, delays should vary
        assert len(set(delays)) > 1
        # All delays should be between 1.0 and 2.0 (base delay * [0.5, 1.0])
        assert all(1.0 <= d <= 2.0 for d in delays)


class TestShouldRetry:
    """Test retry decision logic."""

    def test_retryable_exception(self) -> None:
        """Test that retryable exceptions return True."""
        exception = ConnectionError("Connection failed")
        retryable = (ConnectionError, TimeoutError)

        assert should_retry(exception, retryable) is True

    def test_non_retryable_exception(self) -> None:
        """Test that non-retryable exceptions return False."""
        exception = ValueError("Invalid value")
        retryable = (ConnectionError, TimeoutError)

        assert should_retry(exception, retryable) is False

    def test_subclass_exception(self) -> None:
        """Test that exception subclasses are handled correctly."""
        class CustomConnectionError(ConnectionError):
            pass

        exception = CustomConnectionError("Custom error")
        retryable = (ConnectionError,)

        assert should_retry(exception, retryable) is True


class TestRetryDecorator:
    """Test retry_async decorator."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self) -> None:
        """Test function succeeds on first attempt."""
        call_count = 0

        @retry_async(config=RetryConfig(max_retries=3))
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_func()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_retries(self) -> None:
        """Test function succeeds after retries."""
        call_count = 0

        @retry_async(config=RetryConfig(max_retries=3, initial_delay=0.01, jitter=False))
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = await flaky_func()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self) -> None:
        """Test that exception is raised after all retries."""
        call_count = 0

        @retry_async(config=RetryConfig(max_retries=2, initial_delay=0.01, jitter=False))
        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent failure")

        with pytest.raises(ConnectionError):
            await failing_func()

        assert call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_non_retryable_exception_not_retried(self) -> None:
        """Test that non-retryable exceptions are not retried."""
        call_count = 0

        @retry_async(
            config=RetryConfig(max_retries=3),
            retryable_exceptions=(ConnectionError,)
        )
        async def func_with_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")

        with pytest.raises(ValueError):
            await func_with_value_error()

        assert call_count == 1  # No retries

    @pytest.mark.asyncio
    async def test_retry_with_args_and_kwargs(self) -> None:
        """Test retry works with function arguments."""
        call_count = 0

        @retry_async(config=RetryConfig(max_retries=2, initial_delay=0.01, jitter=False))
        async def func_with_params(x, y, z=10):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Retry me")
            return x + y + z

        result = await func_with_params(1, 2, z=3)
        assert result == 6
        assert call_count == 2


class TestRetryWithBackoff:
    """Test retry_with_backoff function."""

    @pytest.mark.asyncio
    async def test_functional_retry_success(self) -> None:
        """Test functional retry interface."""
        call_count = 0

        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Retry")
            return "success"

        result = await retry_with_backoff(
            test_func,
            config=RetryConfig(max_retries=3, initial_delay=0.01, jitter=False)
        )

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_functional_retry_with_params(self) -> None:
        """Test functional retry with parameters."""
        call_count = 0

        async def test_func(x, y):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Retry")
            return x * y

        result = await retry_with_backoff(
            test_func,
            config=RetryConfig(max_retries=3, initial_delay=0.01, jitter=False),
            x=5,
            y=3
        )

        assert result == 15
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_functional_retry_exhausted(self) -> None:
        """Test functional retry with all attempts exhausted."""
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError):
            await retry_with_backoff(
                failing_func,
                config=RetryConfig(max_retries=2, initial_delay=0.01, jitter=False)
            )

        assert call_count == 3


class TestRetryTiming:
    """Test retry timing and delays."""

    @pytest.mark.asyncio
    async def test_retry_delays_increase(self) -> None:
        """Test that retry delays increase exponentially."""
        call_times = []

        @retry_async(config=RetryConfig(max_retries=3, initial_delay=0.1, jitter=False))
        async def timed_func():
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 3:
                raise ConnectionError("Retry")
            return "success"

        await timed_func()

        # Check that delays increase
        assert len(call_times) == 3
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        # Second delay should be roughly 2x first delay (exponential base = 2)
        assert delay2 > delay1
        assert 0.15 < delay2 < 0.25  # ~0.2s with some tolerance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
