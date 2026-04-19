"""Plugin manager for AgentMind."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from .base import Plugin, PluginType
from .loader import PluginLoader, PluginRegistry
from .lifecycle import PluginLifecycleManager, PluginState
from .dependencies import DependencyResolver, PluginDependency
from .security import PermissionManager, SandboxExecutor, ResourceLimits
from .config import ConfigManager
from .audit import PluginAuditLogger, AuditEventType

logger = logging.getLogger(__name__)


class PluginManager:
    """Manage plugin lifecycle and execution with production-grade features."""

    def __init__(
        self,
        registry: Optional[PluginRegistry] = None,
        config_dir: Optional[Path] = None,
        enable_security: bool = True,
        enable_audit: bool = True,
    ):
        """Initialize plugin manager.

        Args:
            registry: Plugin registry to use
            config_dir: Configuration directory
            enable_security: Enable security features
            enable_audit: Enable audit logging
        """
        self.registry = registry or PluginRegistry()
        self.loader = PluginLoader(self.registry)
        self._active_plugins: Dict[str, Plugin] = {}

        # Production features
        self.lifecycle_manager = PluginLifecycleManager()
        self.dependency_resolver = DependencyResolver()
        self.config_manager = ConfigManager(config_dir)
        self.permission_manager = PermissionManager() if enable_security else None
        self.sandbox_executor = (
            SandboxExecutor(self.permission_manager) if enable_security else None
        )
        self.audit_logger = PluginAuditLogger() if enable_audit else None

    async def load_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None,
        check_dependencies: bool = True,
    ) -> bool:
        """Load and initialize a plugin with full lifecycle management.

        Args:
            plugin_name: Name of plugin to load
            config: Plugin configuration
            check_dependencies: Whether to check dependencies

        Returns:
            True if loaded successfully
        """
        if plugin_name in self._active_plugins:
            logger.warning(f"Plugin {plugin_name} already loaded")
            return True

        # Check dependencies
        if check_dependencies:
            metadata = self.registry.get_metadata(plugin_name)
            if metadata and metadata.dependencies:
                available = {
                    name: self.registry.get_metadata(name).version
                    for name in self.registry._plugins.keys()
                }
                satisfied, missing = self.dependency_resolver.check_dependencies(
                    plugin_name, available
                )
                if not satisfied:
                    logger.error(f"Unsatisfied dependencies for {plugin_name}: {missing}")
                    if self.audit_logger:
                        self.audit_logger.log_event(
                            AuditEventType.PLUGIN_ERROR,
                            plugin_name,
                            details={"error": "unsatisfied_dependencies", "missing": missing},
                            severity="error",
                            success=False,
                        )
                    return False

        # Load or merge config
        if config is None:
            config = self.config_manager.load_config(plugin_name) or {}
        else:
            # Merge with file config
            file_config = self.config_manager.load_config(plugin_name) or {}
            config = {**file_config, **config}

        # Create instance
        plugin = self.registry.create_instance(plugin_name, config)
        if plugin is None:
            return False

        # Validate config
        if config and not plugin.validate_config(config):
            logger.error(f"Invalid configuration for plugin {plugin_name}")
            if self.audit_logger:
                self.audit_logger.log_event(
                    AuditEventType.PLUGIN_ERROR,
                    plugin_name,
                    details={"error": "invalid_config"},
                    severity="error",
                    success=False,
                )
            return False

        # Initialize with lifecycle management
        try:
            success = await self.lifecycle_manager.initialize(plugin_name, plugin)
            if not success:
                return False

            # Activate plugin
            success = await self.lifecycle_manager.activate(plugin_name, plugin)
            if not success:
                await self.lifecycle_manager.cleanup(plugin_name, plugin)
                return False

            self._active_plugins[plugin_name] = plugin

            # Audit log
            if self.audit_logger:
                metadata = plugin.get_metadata()
                self.audit_logger.log_event(
                    AuditEventType.PLUGIN_LOADED,
                    plugin_name,
                    details={"version": metadata.version},
                    severity="info",
                    success=True,
                )

            logger.info(f"Loaded plugin: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize plugin {plugin_name}: {e}")
            if self.audit_logger:
                self.audit_logger.log_event(
                    AuditEventType.PLUGIN_ERROR,
                    plugin_name,
                    details={"error": str(e)},
                    severity="error",
                    success=False,
                )
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload and shutdown a plugin with lifecycle management.

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            True if unloaded successfully
        """
        if plugin_name not in self._active_plugins:
            logger.warning(f"Plugin {plugin_name} not loaded")
            return False

        plugin = self._active_plugins[plugin_name]

        try:
            # Deactivate
            await self.lifecycle_manager.deactivate(plugin_name, plugin)

            # Cleanup
            await self.lifecycle_manager.cleanup(plugin_name, plugin)

            del self._active_plugins[plugin_name]

            # Audit log
            if self.audit_logger:
                self.audit_logger.log_event(
                    AuditEventType.PLUGIN_UNLOADED, plugin_name, severity="info", success=True
                )

            logger.info(f"Unloaded plugin: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to shutdown plugin {plugin_name}: {e}")
            if self.audit_logger:
                self.audit_logger.log_event(
                    AuditEventType.PLUGIN_ERROR,
                    plugin_name,
                    details={"error": str(e), "phase": "unload"},
                    severity="error",
                    success=False,
                )
            return False

    async def reload_plugin(
        self, plugin_name: str, config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Reload a plugin with hot-reload support.

        Args:
            plugin_name: Name of plugin to reload
            config: New plugin configuration

        Returns:
            True if reloaded successfully
        """
        plugin = self.get_plugin(plugin_name)
        if plugin:
            # Try hot-reload first
            if config:
                success = await self.config_manager.hot_reload(plugin_name, plugin)
                if success:
                    if self.audit_logger:
                        self.audit_logger.log_event(
                            AuditEventType.CONFIG_CHANGED,
                            plugin_name,
                            details={"hot_reload": True},
                            severity="info",
                            success=True,
                        )
                    return True

        # Fall back to full reload
        await self.unload_plugin(plugin_name)
        return await self.load_plugin(plugin_name, config)

    async def execute_plugin(
        self, plugin_name: str, sandboxed: bool = True, timeout: Optional[float] = None, **kwargs
    ) -> Any:
        """Execute a plugin with optional sandboxing.

        Args:
            plugin_name: Plugin name
            sandboxed: Whether to execute in sandbox
            timeout: Execution timeout
            **kwargs: Plugin execution parameters

        Returns:
            Execution result
        """
        plugin = self.get_plugin(plugin_name)
        if plugin is None:
            raise ValueError(f"Plugin not loaded: {plugin_name}")

        # Check permissions
        if self.permission_manager:
            # Basic permission check - extend as needed
            pass

        try:
            if sandboxed and self.sandbox_executor:
                # Execute in sandbox
                limits = ResourceLimits(max_execution_time=timeout or 30.0)
                result = await self.sandbox_executor.execute_sandboxed(
                    plugin_name,
                    plugin.execute if hasattr(plugin, "execute") else plugin.initialize,
                    limits,
                    **kwargs,
                )
            else:
                # Execute directly
                if hasattr(plugin, "execute"):
                    if timeout:
                        result = await asyncio.wait_for(plugin.execute(**kwargs), timeout=timeout)
                    else:
                        result = await plugin.execute(**kwargs)
                else:
                    raise ValueError(f"Plugin {plugin_name} does not support execution")

            # Audit log
            if self.audit_logger:
                self.audit_logger.log_event(
                    AuditEventType.PLUGIN_EXECUTED,
                    plugin_name,
                    details={"sandboxed": sandboxed},
                    severity="info",
                    success=True,
                )

            return result

        except Exception as e:
            logger.error(f"Plugin execution failed for {plugin_name}: {e}")
            if self.audit_logger:
                self.audit_logger.log_event(
                    AuditEventType.PLUGIN_ERROR,
                    plugin_name,
                    details={"error": str(e), "phase": "execution"},
                    severity="error",
                    success=False,
                )
            raise

    async def check_plugin_health(self, plugin_name: str) -> Dict[str, Any]:
        """Check plugin health status.

        Args:
            plugin_name: Plugin name

        Returns:
            Health status dictionary
        """
        plugin = self.get_plugin(plugin_name)
        if plugin is None:
            return {"healthy": False, "error": "Plugin not loaded"}

        status = await self.lifecycle_manager.check_health(plugin_name, plugin)

        if not status.healthy and self.audit_logger:
            self.audit_logger.log_event(
                AuditEventType.HEALTH_CHECK_FAILED,
                plugin_name,
                details=status.details,
                severity="warning",
                success=False,
            )

        return status.model_dump()

    def get_plugin_state(self, plugin_name: str) -> Optional[str]:
        """Get plugin lifecycle state.

        Args:
            plugin_name: Plugin name

        Returns:
            State string or None
        """
        state = self.lifecycle_manager.get_state(plugin_name)
        return state.value if state else None

    def register_lifecycle_hook(self, plugin_name: str, hook_name: str, callback: Any) -> None:
        """Register a lifecycle hook for a plugin.

        Args:
            plugin_name: Plugin name
            hook_name: Hook name
            callback: Callback function
        """
        hooks = self.lifecycle_manager.get_hooks(plugin_name)
        if hooks:
            hooks.register(hook_name, callback)

    def set_plugin_permissions(self, plugin_name: str, permissions: Dict[str, Any]) -> None:
        """Set permissions for a plugin.

        Args:
            plugin_name: Plugin name
            permissions: Permissions dictionary
        """
        if self.permission_manager:
            from .security import PluginPermissions

            perm_obj = PluginPermissions(plugin_name=plugin_name, **permissions)
            self.permission_manager.register_permissions(perm_obj)

    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get active plugin instance.

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin instance or None
        """
        return self._active_plugins.get(plugin_name)

    def list_active_plugins(self) -> List[str]:
        """List all active plugins.

        Returns:
            List of active plugin names
        """
        return list(self._active_plugins.keys())

    def list_available_plugins(self, plugin_type: Optional[PluginType] = None) -> List[str]:
        """List all available plugins.

        Args:
            plugin_type: Filter by plugin type

        Returns:
            List of available plugin names
        """
        metadata_list = self.registry.list_plugins(plugin_type)
        return [metadata.name for metadata in metadata_list]

    async def load_all_plugins(
        self, configs: Optional[Dict[str, Dict[str, Any]]] = None, resolve_dependencies: bool = True
    ) -> int:
        """Load all available plugins with dependency resolution.

        Args:
            configs: Dictionary mapping plugin names to configurations
            resolve_dependencies: Whether to resolve load order

        Returns:
            Number of plugins loaded successfully
        """
        configs = configs or {}
        available = self.list_available_plugins()

        if resolve_dependencies:
            # Build dependency graph
            for plugin_name in available:
                metadata = self.registry.get_metadata(plugin_name)
                if metadata:
                    deps = [
                        PluginDependency(name=dep, version_spec="*")
                        for dep in metadata.dependencies
                    ]
                    self.dependency_resolver.add_plugin(metadata.name, metadata.version, deps)

            # Get load order
            available_versions = {
                name: self.registry.get_metadata(name).version for name in available
            }
            load_order, errors = self.dependency_resolver.resolve_load_order(
                available, available_versions
            )

            if errors:
                logger.error(f"Dependency resolution errors: {errors}")
                return 0

            plugins_to_load = load_order
        else:
            plugins_to_load = available

        loaded_count = 0
        for plugin_name in plugins_to_load:
            config = configs.get(plugin_name)
            if await self.load_plugin(plugin_name, config, check_dependencies=False):
                loaded_count += 1

        return loaded_count

    async def unload_all_plugins(self) -> int:
        """Unload all active plugins.

        Returns:
            Number of plugins unloaded
        """
        plugin_names = list(self._active_plugins.keys())
        unloaded_count = 0

        for plugin_name in plugin_names:
            if await self.unload_plugin(plugin_name):
                unloaded_count += 1

        return unloaded_count

    def discover_and_load(
        self,
        search_paths: Optional[List[Path]] = None,
        auto_load: bool = False,
        configs: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> int:
        """Discover plugins and optionally load them.

        Args:
            search_paths: Paths to search for plugins
            auto_load: Whether to automatically load discovered plugins
            configs: Plugin configurations

        Returns:
            Number of plugins discovered
        """
        # Load built-in plugins
        builtin_count = self.loader.load_builtin_plugins()

        # Discover external plugins
        external_count = self.loader.discover_plugins(search_paths)

        total_discovered = builtin_count + external_count
        logger.info(f"Discovered {total_discovered} plugins")

        # Auto-load if requested
        if auto_load:
            asyncio.create_task(self.load_all_plugins(configs))

        return total_discovered

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """Get all active plugins of a specific type.

        Args:
            plugin_type: Plugin type to filter by

        Returns:
            List of plugin instances
        """
        result = []
        for plugin_name, plugin in self._active_plugins.items():
            metadata = self.registry.get_metadata(plugin_name)
            if metadata and metadata.plugin_type == plugin_type:
                result.append(plugin)
        return result

    async def execute_tool_plugin(self, plugin_name: str, **kwargs) -> Any:
        """Execute a tool plugin.

        Args:
            plugin_name: Name of tool plugin
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        plugin = self.get_plugin(plugin_name)
        if plugin is None:
            raise ValueError(f"Plugin not loaded: {plugin_name}")

        metadata = self.registry.get_metadata(plugin_name)
        if metadata and metadata.plugin_type != PluginType.TOOL:
            raise ValueError(f"Plugin {plugin_name} is not a tool plugin")

        from .base import ToolPlugin

        if not isinstance(plugin, ToolPlugin):
            raise ValueError(f"Plugin {plugin_name} is not a ToolPlugin")

        return await plugin.execute(**kwargs)

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions from all active tool plugins.

        Returns:
            List of tool definitions
        """
        from .base import ToolPlugin

        definitions = []

        for plugin in self._active_plugins.values():
            if isinstance(plugin, ToolPlugin):
                definitions.append(plugin.get_tool_definition())

        return definitions

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.unload_all_plugins()

    def get_statistics(self) -> Dict[str, Any]:
        """Get plugin manager statistics.

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_plugins": len(self.registry._plugins),
            "active_plugins": len(self._active_plugins),
            "plugin_states": self.lifecycle_manager.get_all_states(),
        }

        if self.audit_logger:
            stats["audit"] = self.audit_logger.get_statistics()

        return stats

    def export_plugin_info(self, output_file: Path) -> bool:
        """Export plugin information to file.

        Args:
            output_file: Output file path

        Returns:
            True if successful
        """
        try:
            import json

            info = {
                "plugins": [
                    {
                        "name": metadata.name,
                        "version": metadata.version,
                        "type": metadata.plugin_type.value,
                        "description": metadata.description,
                        "author": metadata.author,
                        "dependencies": metadata.dependencies,
                        "active": metadata.name in self._active_plugins,
                        "state": self.get_plugin_state(metadata.name),
                    }
                    for metadata in self.registry.list_plugins()
                ],
                "statistics": self.get_statistics(),
            }

            with open(output_file, "w") as f:
                json.dump(info, f, indent=2, default=str)

            logger.info(f"Exported plugin info to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error exporting plugin info: {e}")
            return False
