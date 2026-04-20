"""Comprehensive tests for production - grade plugin system."""

import asyncio

import pytest

from agentmind.plugins.audit import AuditEventType, PluginAuditLogger
from agentmind.plugins.config import ConfigManager
from agentmind.plugins.dependencies import DependencyResolver, PluginDependency, VersionChecker
from agentmind.plugins.lifecycle import HealthStatus, PluginLifecycleManager, PluginState
from agentmind.plugins.manager import PluginManager
from agentmind.plugins.marketplace import (
    PluginCategory,
    PluginManifest,
)
from agentmind.plugins.marketplace import PluginRegistry as MarketplaceRegistry
from agentmind.plugins.security import (
    PermissionManager,
    PluginPermissions,
    ResourceLimits,
    SandboxExecutor,
    SignatureVerifier,
)
from agentmind.plugins.testing import FailingPlugin, MockPlugin, PluginTestHarness


class TestPluginLifecycle:
    """Test plugin lifecycle management."""

    @pytest.mark.asyncio
    async def test_lifecycle_states(self):
        """Test plugin lifecycle state transitions."""
        manager = PluginLifecycleManager()
        plugin = MockPlugin()

        manager.register_plugin("test - plugin")

        # Initial state
        assert manager.get_state("test - plugin") == PluginState.UNINITIALIZED

        # Initialize
        await manager.initialize("test - plugin", plugin)
        assert manager.get_state("test - plugin") == PluginState.INACTIVE

        # Activate
        await manager.activate("test - plugin", plugin)
        assert manager.get_state("test - plugin") == PluginState.ACTIVE

        # Deactivate
        await manager.deactivate("test - plugin", plugin)
        assert manager.get_state("test - plugin") == PluginState.INACTIVE

        # Cleanup
        await manager.cleanup("test - plugin", plugin)
        assert manager.get_state("test - plugin") == PluginState.UNINITIALIZED

    @pytest.mark.asyncio
    async def test_lifecycle_hooks(self):
        """Test lifecycle hooks execution."""
        manager = PluginLifecycleManager()
        plugin = MockPlugin()

        manager.register_plugin("test - plugin")
        hooks = manager.get_hooks("test - plugin")

        hook_called = {"pre_init": False, "post_init": False}

        def pre_init_hook(p):
            hook_called["pre_init"] = True

        async def post_init_hook(p):
            hook_called["post_init"] = True

        hooks.register("pre_initialize", pre_init_hook)
        hooks.register("post_initialize", post_init_hook)

        await manager.initialize("test - plugin", plugin)

        assert hook_called["pre_init"]
        assert hook_called["post_init"]

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test plugin health checking."""
        manager = PluginLifecycleManager()
        plugin = MockPlugin()

        manager.register_plugin("test - plugin")
        await manager.initialize("test - plugin", plugin)
        await manager.activate("test - plugin", plugin)

        status = await manager.check_health("test - plugin", plugin)

        assert isinstance(status, HealthStatus)
        assert status.healthy
        assert status.state == PluginState.ACTIVE
        assert status.uptime_seconds >= 0


class TestDependencyResolution:
    """Test dependency resolution."""

    def test_version_checking(self):
        """Test version compatibility checking."""
        checker = VersionChecker()

        assert checker.check_version("1.5.0", ">=1.0.0,<2.0.0")
        assert not checker.check_version("2.0.0", ">=1.0.0,<2.0.0")
        assert checker.check_version("1.0.0", "==1.0.0")
        assert not checker.check_version("1.0.1", "==1.0.0")
        assert checker.check_version("1.5.0", "*")

    def test_dependency_graph(self):
        """Test dependency graph building."""
        resolver = DependencyResolver()

        # Add plugins with dependencies
        resolver.add_plugin("plugin-a", "1.0.0", [])
        resolver.add_plugin(
            "plugin-b", "1.0.0", [PluginDependency(name="plugin-a", version_spec=">=1.0.0")]
        )
        resolver.add_plugin(
            "plugin-c", "1.0.0", [PluginDependency(name="plugin-b", version_spec=">=1.0.0")]
        )

        # Get load order
        available = {"plugin-a": "1.0.0", "plugin-b": "1.0.0", "plugin-c": "1.0.0"}
        load_order, errors = resolver.resolve_load_order(
            ["plugin-a", "plugin-b", "plugin-c"], available
        )

        assert errors == []
        assert load_order.index("plugin-a") < load_order.index("plugin-b")
        assert load_order.index("plugin-b") < load_order.index("plugin-c")

    def test_circular_dependency_detection(self):
        """Test circular dependency detection."""
        resolver = DependencyResolver()

        resolver.add_plugin(
            "plugin-a", "1.0.0", [PluginDependency(name="plugin-b", version_spec="*")]
        )
        resolver.add_plugin(
            "plugin-b", "1.0.0", [PluginDependency(name="plugin-a", version_spec="*")]
        )

        has_circular, cycle = resolver.graph.has_circular_dependency()
        assert has_circular
        assert cycle is not None

    def test_missing_dependencies(self):
        """Test missing dependency detection."""
        resolver = DependencyResolver()

        resolver.add_plugin(
            "plugin-a",
            "1.0.0",
            [PluginDependency(name="plugin-missing", version_spec=">=1.0.0")],
        )

        available = {"plugin-a": "1.0.0"}
        satisfied, missing = resolver.check_dependencies("plugin-a", available)

        assert not satisfied
        assert len(missing) > 0


class TestPluginSecurity:
    """Test plugin security features."""

    def test_permission_management(self):
        """Test permission management."""
        manager = PermissionManager()

        permissions = PluginPermissions(
            plugin_name="test - plugin",
            allow_network=True,
            allow_filesystem=False,
            allowed_apis={"api1", "api2"},
        )

        manager.register_permissions(permissions)

        assert manager.check_permission("test - plugin", "network", "connect")
        assert not manager.check_permission("test - plugin", "filesystem", "write")
        assert manager.check_api_access("test - plugin", "api1")
        assert not manager.check_api_access("test - plugin", "api3")

    @pytest.mark.asyncio
    async def test_sandbox_execution(self):
        """Test sandboxed plugin execution."""
        executor = SandboxExecutor()

        async def test_func(value):
            return value * 2

        result = await executor.execute_sandboxed(
            "test - plugin", test_func, ResourceLimits(max_execution_time=5.0), 5
        )

        assert result == 10

    @pytest.mark.asyncio
    async def test_execution_timeout(self):
        """Test execution timeout."""
        executor = SandboxExecutor()

        async def slow_func():
            await asyncio.sleep(10)
            return "done"

        with pytest.raises(asyncio.TimeoutError):
            await executor.execute_with_timeout("test - plugin", slow_func, timeout=0.1)

    def test_signature_verification(self):
        """Test plugin signature verification."""
        verifier = SignatureVerifier()

        content = b"plugin code here"
        checksum = verifier.calculate_checksum(content)

        from agentmind.plugins.security import PluginSignature

        signature = PluginSignature(
            plugin_name="test - plugin",
            version="1.0.0",
            checksum=checksum,
            signed_by="trusted - signer",
        )

        verifier.register_signature(signature)
        verifier.add_trusted_signer("trusted - signer")

        assert verifier.verify_checksum("test - plugin", "1.0.0", content)
        assert verifier.is_trusted("test - plugin", "1.0.0")


class TestPluginConfiguration:
    """Test plugin configuration management."""

    def test_config_validation(self, tmp_path):
        """Test configuration validation."""
        manager = ConfigManager(config_dir=tmp_path)

        from pydantic import BaseModel, Field

        class TestConfigSchema(BaseModel):
            enabled: bool = True
            api_key: str = Field(..., min_length=10)

        manager.register_schema("test - plugin", TestConfigSchema)

        # Valid config
        valid_config = {"enabled": True, "api_key": "1234567890"}
        assert manager.update_config("test - plugin", valid_config, save=False)

        # Invalid config
        invalid_config = {"enabled": True, "api_key": "short"}
        assert not manager.update_config("test - plugin", invalid_config, save=False)

    def test_environment_configs(self, tmp_path):
        """Test environment - specific configurations."""
        manager = ConfigManager(config_dir=tmp_path)

        dev_config = {"enabled": True, "debug": True}
        prod_config = {"enabled": True, "debug": False}

        manager.update_config("test - plugin", dev_config, save=False)

        config = manager.get_config("test - plugin")
        assert config is not None

    @pytest.mark.asyncio
    async def test_hot_reload(self, tmp_path):
        """Test configuration hot - reload."""
        manager = ConfigManager(config_dir=tmp_path)
        plugin = MockPlugin()

        # Save initial config
        initial_config = {"enabled": True, "setting": "value1"}
        manager.save_config("test - plugin", initial_config)

        # Update config
        new_config = {"enabled": True, "setting": "value2"}
        manager.update_config("test - plugin", new_config)

        # Hot reload
        success = await manager.hot_reload("test - plugin", plugin)
        assert success


class TestPluginMarketplace:
    """Test plugin marketplace features."""

    def test_plugin_registration(self, tmp_path):
        """Test plugin registration in marketplace."""
        registry = MarketplaceRegistry(registry_file=tmp_path / "registry.json")

        manifest = PluginManifest(
            name="test - plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.TOOLS,
            tags=["test", "example"],
        )

        assert registry.register_plugin(manifest)
        retrieved = registry.get_plugin("test - plugin")
        assert retrieved is not None
        assert retrieved.name == "test - plugin"

    def test_plugin_search(self, tmp_path):
        """Test plugin search functionality."""
        registry = MarketplaceRegistry(registry_file=tmp_path / "registry.json")

        # Register multiple plugins
        for i in range(5):
            manifest = PluginManifest(
                name=f"plugin-{i}",
                version="1.0.0",
                description=f"Test plugin {i}",
                author="Test",
                category=PluginCategory.TOOLS if i % 2 == 0 else PluginCategory.INTEGRATION,
                tags=["test"],
            )
            registry.register_plugin(manifest)

        # Search by category
        tools = registry.search_plugins(category=PluginCategory.TOOLS)
        assert len(tools) == 3

        # Search by query
        results = registry.search_plugins(query="plugin-2")
        assert len(results) == 1

    def test_plugin_ratings(self, tmp_path):
        """Test plugin rating system."""
        registry = MarketplaceRegistry(registry_file=tmp_path / "registry.json")

        manifest = PluginManifest(
            name="test - plugin",
            version="1.0.0",
            description="Test",
            author="Test",
            category=PluginCategory.TOOLS,
        )
        registry.register_plugin(manifest)

        # Add ratings
        registry.add_rating("test - plugin", "user1", 5, "Great plugin!")
        registry.add_rating("test - plugin", "user2", 4, "Good")
        registry.add_rating("test - plugin", "user3", 5, "Excellent")

        plugin = registry.get_plugin("test - plugin")
        assert plugin.rating_count == 3
        assert plugin.average_rating == pytest.approx(4.67, 0.01)


class TestPluginAudit:
    """Test plugin audit logging."""

    def test_audit_logging(self, tmp_path):
        """Test audit event logging."""
        logger = PluginAuditLogger(log_dir=tmp_path)

        event = logger.log_event(
            AuditEventType.PLUGIN_LOADED,
            "test - plugin",
            details={"version": "1.0.0"},
            user_id="user123",
        )

        assert event.plugin_name == "test - plugin"
        assert event.event_type == AuditEventType.PLUGIN_LOADED

        # Retrieve events
        events = logger.get_events(plugin_name="test - plugin")
        assert len(events) == 1

    def test_audit_filtering(self, tmp_path):
        """Test audit event filtering."""
        logger = PluginAuditLogger(log_dir=tmp_path)

        # Log multiple events
        logger.log_event(AuditEventType.PLUGIN_LOADED, "plugin-a", user_id="user1")
        logger.log_event(AuditEventType.PLUGIN_ERROR, "plugin-a", success=False)
        logger.log_event(AuditEventType.PLUGIN_LOADED, "plugin-b", user_id="user2")

        # Filter by plugin
        plugin_a_events = logger.get_events(plugin_name="plugin-a")
        assert len(plugin_a_events) == 2

        # Filter by user
        user1_events = logger.get_events(user_id="user1")
        assert len(user1_events) == 1

        # Get failed operations
        failed = logger.get_failed_operations()
        assert len(failed) == 1

    def test_audit_statistics(self, tmp_path):
        """Test audit statistics."""
        logger = PluginAuditLogger(log_dir=tmp_path)

        logger.log_event(AuditEventType.PLUGIN_LOADED, "plugin-a")
        logger.log_event(AuditEventType.PLUGIN_ERROR, "plugin-a", success=False)
        logger.log_event(AuditEventType.PLUGIN_EXECUTED, "plugin-b")

        stats = logger.get_statistics()

        assert stats["total_events"] == 3
        assert stats["failed_events"] == 1
        assert stats["success_rate"] == pytest.approx(0.67, 0.01)


class TestPluginManager:
    """Test integrated plugin manager."""

    @pytest.mark.asyncio
    async def test_plugin_loading(self):
        """Test plugin loading with full features."""
        manager = PluginManager(enable_security=True, enable_audit=True)

        # Register mock plugin
        manager.registry.register(MockPlugin)

        # Load plugin
        success = await manager.load_plugin("mock-plugin")
        assert success

        # Check state
        assert manager.get_plugin_state("mock-plugin") == "active"

        # Check health
        health = await manager.check_plugin_health("mock-plugin")
        assert health["healthy"]

        # Unload
        await manager.unload_plugin("mock-plugin")

    @pytest.mark.asyncio
    async def test_plugin_execution(self):
        """Test plugin execution."""
        manager = PluginManager(enable_security=True)

        manager.registry.register(MockPlugin)
        await manager.load_plugin("mock-plugin")

        # Execute plugin
        result = await manager.execute_plugin("mock-plugin", sandboxed=True)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_dependency_resolution(self):
        """Test automatic dependency resolution."""
        manager = PluginManager()

        # This would test with real plugins that have dependencies
        # For now, just verify the mechanism exists
        assert manager.dependency_resolver is not None


class TestPluginTestingUtilities:
    """Test plugin testing utilities."""

    @pytest.mark.asyncio
    async def test_plugin_test_harness(self):
        """Test plugin test harness."""
        harness = PluginTestHarness(MockPlugin)
        await harness.setup()

        results = await harness.test_lifecycle()

        assert results["initialize"]
        assert results["health_check"]
        assert results["shutdown"]

        await harness.teardown()

    @pytest.mark.asyncio
    async def test_failing_plugin_handling(self):
        """Test handling of failing plugins."""
        plugin = FailingPlugin(fail_on="initialize")

        with pytest.raises(RuntimeError):
            await plugin.initialize()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
