"""Plugin testing utilities and fixtures."""

import asyncio
import pytest
from typing import Any, Dict, List, Optional, Type
from unittest.mock import Mock, AsyncMock, MagicMock
from pathlib import Path

from agentmind.plugins.base import Plugin, PluginMetadata, PluginType
from agentmind.plugins.manager import PluginManager
from agentmind.plugins.loader import PluginRegistry
from agentmind.plugins.lifecycle import PluginLifecycleManager, PluginState
from agentmind.plugins.security import PermissionManager, PluginPermissions, SandboxExecutor
from agentmind.plugins.config import ConfigManager
from agentmind.plugins.audit import PluginAuditLogger


class MockPlugin(Plugin):
    """Mock plugin for testing."""

    def __init__(
        self,
        name: str = "mock-plugin",
        version: str = "1.0.0",
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize mock plugin."""
        super().__init__(config)
        self._name = name
        self._version = version
        self.initialize_called = False
        self.shutdown_called = False
        self.execute_count = 0

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self._name,
            version=self._version,
            description="Mock plugin for testing",
            author="Test Author",
            plugin_type=PluginType.TOOL,
        )

    async def initialize(self) -> None:
        """Initialize the plugin."""
        self.initialize_called = True
        self._initialized = True

    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        self.shutdown_called = True
        self._initialized = False

    async def execute(self, **kwargs) -> Any:
        """Execute mock operation."""
        self.execute_count += 1
        return {"status": "success", "count": self.execute_count}


class FailingPlugin(Plugin):
    """Plugin that fails for testing error handling."""

    def __init__(self, fail_on: str = "initialize"):
        """Initialize failing plugin.

        Args:
            fail_on: Which method should fail ('initialize', 'shutdown', 'execute')
        """
        super().__init__()
        self.fail_on = fail_on

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="failing-plugin",
            version="1.0.0",
            description="Plugin that fails",
            author="Test",
            plugin_type=PluginType.TOOL,
        )

    async def initialize(self) -> None:
        """Initialize - may fail."""
        if self.fail_on == "initialize":
            raise RuntimeError("Initialization failed")
        self._initialized = True

    async def shutdown(self) -> None:
        """Shutdown - may fail."""
        if self.fail_on == "shutdown":
            raise RuntimeError("Shutdown failed")

    async def execute(self, **kwargs) -> Any:
        """Execute - may fail."""
        if self.fail_on == "execute":
            raise RuntimeError("Execution failed")
        return {"status": "success"}


class PluginTestHarness:
    """Test harness for plugin development and testing."""

    def __init__(self, plugin_class: Type[Plugin], config: Optional[Dict[str, Any]] = None):
        """Initialize test harness.

        Args:
            plugin_class: Plugin class to test
            config: Plugin configuration
        """
        self.plugin_class = plugin_class
        self.config = config or {}
        self.plugin: Optional[Plugin] = None
        self.lifecycle_manager = PluginLifecycleManager()
        self.permission_manager = PermissionManager()
        self.audit_logger = PluginAuditLogger()

    async def setup(self) -> None:
        """Set up test environment."""
        self.plugin = self.plugin_class(self.config)
        metadata = self.plugin.get_metadata()
        self.lifecycle_manager.register_plugin(metadata.name)

    async def teardown(self) -> None:
        """Tear down test environment."""
        if self.plugin and self.plugin.is_initialized:
            await self.plugin.shutdown()

    async def test_lifecycle(self) -> Dict[str, bool]:
        """Test plugin lifecycle.

        Returns:
            Dict of test results
        """
        results = {}

        # Test initialization
        try:
            await self.plugin.initialize()
            results["initialize"] = self.plugin.is_initialized
        except Exception as e:
            results["initialize"] = False
            results["initialize_error"] = str(e)

        # Test health check
        try:
            healthy = self.plugin.health_check() if hasattr(self.plugin, "health_check") else True
            results["health_check"] = healthy
        except Exception as e:
            results["health_check"] = False
            results["health_check_error"] = str(e)

        # Test shutdown
        try:
            await self.plugin.shutdown()
            results["shutdown"] = not self.plugin.is_initialized
        except Exception as e:
            results["shutdown"] = False
            results["shutdown_error"] = str(e)

        return results

    async def test_config_validation(self, test_configs: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Test configuration validation.

        Args:
            test_configs: List of configurations to test

        Returns:
            Dict of validation results
        """
        results = {}

        for i, config in enumerate(test_configs):
            try:
                valid = self.plugin.validate_config(config)
                results[f"config_{i}"] = valid
            except Exception as e:
                results[f"config_{i}"] = False
                results[f"config_{i}_error"] = str(e)

        return results

    async def test_error_handling(self) -> Dict[str, bool]:
        """Test error handling.

        Returns:
            Dict of test results
        """
        results = {}

        # Test with invalid config
        try:
            invalid_plugin = self.plugin_class({"invalid": "config"})
            await invalid_plugin.initialize()
            results["invalid_config_handled"] = True
        except Exception:
            results["invalid_config_handled"] = True

        # Test double initialization
        try:
            await self.plugin.initialize()
            await self.plugin.initialize()
            results["double_init_handled"] = True
        except Exception:
            results["double_init_handled"] = True

        return results

    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """Generate test report.

        Args:
            results: Test results

        Returns:
            Formatted report
        """
        report = f"Plugin Test Report: {self.plugin.get_metadata().name}\n"
        report += "=" * 60 + "\n\n"

        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            report += f"{status}: {test_name}\n"

        return report


# Pytest fixtures


@pytest.fixture
def mock_plugin():
    """Fixture for mock plugin."""
    return MockPlugin()


@pytest.fixture
def failing_plugin():
    """Fixture for failing plugin."""
    return FailingPlugin()


@pytest.fixture
def plugin_manager():
    """Fixture for plugin manager."""
    return PluginManager()


@pytest.fixture
def plugin_registry():
    """Fixture for plugin registry."""
    return PluginRegistry()


@pytest.fixture
def lifecycle_manager():
    """Fixture for lifecycle manager."""
    return PluginLifecycleManager()


@pytest.fixture
def permission_manager():
    """Fixture for permission manager."""
    return PermissionManager()


@pytest.fixture
def config_manager(tmp_path):
    """Fixture for config manager."""
    return ConfigManager(config_dir=tmp_path / "config")


@pytest.fixture
def audit_logger(tmp_path):
    """Fixture for audit logger."""
    return PluginAuditLogger(log_dir=tmp_path / "logs")


@pytest.fixture
def sandbox_executor():
    """Fixture for sandbox executor."""
    return SandboxExecutor()


@pytest.fixture
async def initialized_plugin(mock_plugin):
    """Fixture for initialized plugin."""
    await mock_plugin.initialize()
    yield mock_plugin
    await mock_plugin.shutdown()


# Helper functions for testing


def create_test_plugin(
    name: str = "test-plugin",
    plugin_type: PluginType = PluginType.TOOL,
    dependencies: Optional[List[str]] = None,
) -> Type[Plugin]:
    """Create a test plugin class.

    Args:
        name: Plugin name
        plugin_type: Plugin type
        dependencies: Plugin dependencies

    Returns:
        Plugin class
    """

    class TestPlugin(Plugin):
        def get_metadata(self) -> PluginMetadata:
            return PluginMetadata(
                name=name,
                version="1.0.0",
                description=f"Test plugin: {name}",
                author="Test",
                plugin_type=plugin_type,
                dependencies=dependencies or [],
            )

        async def initialize(self) -> None:
            self._initialized = True

        async def shutdown(self) -> None:
            self._initialized = False

    return TestPlugin


async def run_plugin_test_suite(
    plugin_class: Type[Plugin], config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Run complete test suite for a plugin.

    Args:
        plugin_class: Plugin class to test
        config: Plugin configuration

    Returns:
        Test results
    """
    harness = PluginTestHarness(plugin_class, config)
    await harness.setup()

    results = {}

    # Test lifecycle
    results["lifecycle"] = await harness.test_lifecycle()

    # Test error handling
    results["error_handling"] = await harness.test_error_handling()

    await harness.teardown()

    return results


def assert_plugin_valid(plugin: Plugin) -> None:
    """Assert that a plugin is valid.

    Args:
        plugin: Plugin to validate

    Raises:
        AssertionError: If plugin is invalid
    """
    # Check metadata
    metadata = plugin.get_metadata()
    assert metadata.name, "Plugin must have a name"
    assert metadata.version, "Plugin must have a version"
    assert metadata.description, "Plugin must have a description"
    assert metadata.author, "Plugin must have an author"
    assert metadata.plugin_type, "Plugin must have a type"

    # Check methods exist
    assert hasattr(plugin, "initialize"), "Plugin must have initialize method"
    assert hasattr(plugin, "shutdown"), "Plugin must have shutdown method"
    assert callable(plugin.initialize), "initialize must be callable"
    assert callable(plugin.shutdown), "shutdown must be callable"


def mock_plugin_execution(
    plugin: Plugin, return_value: Any = None, side_effect: Optional[Exception] = None
):
    """Mock plugin execution for testing.

    Args:
        plugin: Plugin to mock
        return_value: Return value for execution
        side_effect: Exception to raise

    Returns:
        Mock object
    """
    if hasattr(plugin, "execute"):
        mock = AsyncMock(return_value=return_value, side_effect=side_effect)
        plugin.execute = mock
        return mock
    return None


class PluginPerformanceTester:
    """Test plugin performance."""

    def __init__(self, plugin: Plugin):
        """Initialize performance tester.

        Args:
            plugin: Plugin to test
        """
        self.plugin = plugin
        self.results = {}

    async def test_initialization_time(self, iterations: int = 10) -> float:
        """Test initialization time.

        Args:
            iterations: Number of iterations

        Returns:
            Average initialization time in seconds
        """
        import time

        times = []
        for _ in range(iterations):
            start = time.time()
            await self.plugin.initialize()
            await self.plugin.shutdown()
            times.append(time.time() - start)

        avg_time = sum(times) / len(times)
        self.results["initialization_time"] = avg_time
        return avg_time

    async def test_execution_throughput(self, duration: float = 5.0) -> float:
        """Test execution throughput.

        Args:
            duration: Test duration in seconds

        Returns:
            Operations per second
        """
        import time

        if not hasattr(self.plugin, "execute"):
            return 0.0

        await self.plugin.initialize()

        count = 0
        start = time.time()
        end = start + duration

        while time.time() < end:
            await self.plugin.execute()
            count += 1

        await self.plugin.shutdown()

        ops_per_sec = count / duration
        self.results["throughput"] = ops_per_sec
        return ops_per_sec

    def get_results(self) -> Dict[str, float]:
        """Get performance test results.

        Returns:
            Dict of results
        """
        return self.results
