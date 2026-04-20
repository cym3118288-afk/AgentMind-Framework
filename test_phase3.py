"""Quick test script for Phase 3 features."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_retry():
    """Test retry mechanism."""
    print("Testing retry mechanism...")
    from agentmind.utils.retry import RetryConfig, retry_with_backoff

    attempt_count = 0

    async def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError(f"Attempt {attempt_count} failed")
        return "Success!"

    config = RetryConfig(max_retries=3, initial_delay=0.1)
    result = await retry_with_backoff(failing_function, config, exceptions=(ValueError,))

    assert result == "Success!"
    assert attempt_count == 3
    print("✓ Retry mechanism works!")


async def test_observability():
    """Test observability system."""
    print("\nTesting observability...")
    from agentmind.utils.observability import Tracer

    tracer = Tracer(session_id="test-session", metadata={"test": True})
    tracer.start()

    # Simulate some work
    await asyncio.sleep(0.1)

    tracer.end()

    summary = tracer.get_summary()
    assert summary["session_id"] == "test-session"
    assert "duration_ms" in summary
    print("✓ Observability system works!")


def test_api_imports():
    """Test API server imports."""
    print("\nTesting API server imports...")
    try:
        import api_server

        assert hasattr(api_server, "app")
        assert hasattr(api_server, "collaborate")
        print("✓ API server imports successfully!")
    except ImportError as e:
        print(f"✗ API server import failed: {e}")
        print("  (This is expected if fastapi/uvicorn not installed)")


def test_cli_imports():
    """Test CLI imports."""
    print("\nTesting CLI imports...")
    try:
        import cli

        assert hasattr(cli, "cli")
        assert hasattr(cli, "run")
        print("✓ CLI imports successfully!")
    except ImportError as e:
        print(f"✗ CLI import failed: {e}")
        print("  (This is expected if click not installed)")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Phase 3 Feature Tests")
    print("=" * 60)

    # Test core features
    await test_retry()
    await test_observability()

    # Test optional features (may fail if dependencies not installed)
    test_api_imports()
    test_cli_imports()

    print("\n" + "=" * 60)
    print("All core tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
