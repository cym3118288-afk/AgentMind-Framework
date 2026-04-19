"""Plugin manager for AgentMind."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from .base import Plugin, PluginType
from .loader import PluginLoader, PluginRegistry

logger = logging.getLogger(__name__)


class PluginManager:
    """Manage plugin lifecycle and execution."""

    def __init__(self, registry: Optional[PluginRegistry] = None):
        """Initialize plugin manager.

        Args:
            registry: Plugin registry to use
        """
        self.registry = registry or PluginRegistry()
        self.loader = PluginLoader(self.registry)
        self._active_plugins: Dict[str, Plugin] = {}

    async def load_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Load and initialize a plugin.

        Args:
            plugin_name: Name of plugin to load
            config: Plugin configuration

        Returns:
            True if loaded successfully
        """
        if plugin_name in self._active_plugins:
            logger.warning(f"Plugin {plugin_name} already loaded")
            return True

        # Create instance
        plugin = self.registry.create_instance(plugin_name, config)
        if plugin is None:
            return False

        # Validate config
        if config and not plugin.validate_config(config):
            logger.error(f"Invalid configuration for plugin {plugin_name}")
            return False

        # Initialize
        try:
            await plugin.initialize()
            plugin._initialized = True
            self._active_plugins[plugin_name] = plugin
            logger.info(f"Loaded plugin: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize plugin {plugin_name}: {e}")
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload and shutdown a plugin.

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
            await plugin.shutdown()
            plugin._initialized = False
            del self._active_plugins[plugin_name]
            logger.info(f"Unloaded plugin: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to shutdown plugin {plugin_name}: {e}")
            return False

    async def reload_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Reload a plugin.

        Args:
            plugin_name: Name of plugin to reload
            config: New plugin configuration

        Returns:
            True if reloaded successfully
        """
        await self.unload_plugin(plugin_name)
        return await self.load_plugin(plugin_name, config)

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

    def list_available_plugins(
        self,
        plugin_type: Optional[PluginType] = None
    ) -> List[str]:
        """List all available plugins.

        Args:
            plugin_type: Filter by plugin type

        Returns:
            List of available plugin names
        """
        metadata_list = self.registry.list_plugins(plugin_type)
        return [metadata.name for metadata in metadata_list]

    async def load_all_plugins(
        self,
        configs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> int:
        """Load all available plugins.

        Args:
            configs: Dictionary mapping plugin names to configurations

        Returns:
            Number of plugins loaded successfully
        """
        configs = configs or {}
        available = self.list_available_plugins()
        loaded_count = 0

        for plugin_name in available:
            config = configs.get(plugin_name)
            if await self.load_plugin(plugin_name, config):
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
        configs: Optional[Dict[str, Dict[str, Any]]] = None
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

    async def execute_tool_plugin(
        self,
        plugin_name: str,
        **kwargs
    ) -> Any:
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
