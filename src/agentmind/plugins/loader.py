"""Plugin loader and registry."""

import importlib
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
import logging

from .base import Plugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing available plugins."""

    def __init__(self):
        """Initialize plugin registry."""
        self._plugins: Dict[str, Type[Plugin]] = {}
        self._metadata: Dict[str, PluginMetadata] = {}
        self._instances: Dict[str, Plugin] = {}

    def register(self, plugin_class: Type[Plugin]) -> None:
        """Register a plugin class.

        Args:
            plugin_class: Plugin class to register
        """
        # Create temporary instance to get metadata
        temp_instance = plugin_class()
        metadata = temp_instance.get_metadata()

        if metadata.name in self._plugins:
            logger.warning(f"Plugin {metadata.name} already registered, overwriting")

        self._plugins[metadata.name] = plugin_class
        self._metadata[metadata.name] = metadata
        logger.info(f"Registered plugin: {metadata.name} v{metadata.version}")

    def unregister(self, plugin_name: str) -> None:
        """Unregister a plugin.

        Args:
            plugin_name: Name of plugin to unregister
        """
        if plugin_name in self._plugins:
            del self._plugins[plugin_name]
            del self._metadata[plugin_name]
            if plugin_name in self._instances:
                del self._instances[plugin_name]
            logger.info(f"Unregistered plugin: {plugin_name}")

    def get_plugin_class(self, plugin_name: str) -> Optional[Type[Plugin]]:
        """Get plugin class by name.

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin class or None
        """
        return self._plugins.get(plugin_name)

    def get_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """Get plugin metadata.

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin metadata or None
        """
        return self._metadata.get(plugin_name)

    def list_plugins(
        self,
        plugin_type: Optional[PluginType] = None
    ) -> List[PluginMetadata]:
        """List all registered plugins.

        Args:
            plugin_type: Filter by plugin type

        Returns:
            List of plugin metadata
        """
        if plugin_type is None:
            return list(self._metadata.values())

        return [
            metadata for metadata in self._metadata.values()
            if metadata.plugin_type == plugin_type
        ]

    def create_instance(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[Plugin]:
        """Create plugin instance.

        Args:
            plugin_name: Plugin name
            config: Plugin configuration

        Returns:
            Plugin instance or None
        """
        plugin_class = self.get_plugin_class(plugin_name)
        if plugin_class is None:
            logger.error(f"Plugin not found: {plugin_name}")
            return None

        try:
            instance = plugin_class(config=config)
            self._instances[plugin_name] = instance
            return instance
        except Exception as e:
            logger.error(f"Failed to create plugin instance: {e}")
            return None

    def get_instance(self, plugin_name: str) -> Optional[Plugin]:
        """Get existing plugin instance.

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin instance or None
        """
        return self._instances.get(plugin_name)


class PluginLoader:
    """Load plugins from various sources."""

    def __init__(self, registry: Optional[PluginRegistry] = None):
        """Initialize plugin loader.

        Args:
            registry: Plugin registry to use
        """
        self.registry = registry or PluginRegistry()

    def load_from_module(self, module_name: str) -> int:
        """Load plugins from a Python module.

        Args:
            module_name: Module name to load

        Returns:
            Number of plugins loaded
        """
        try:
            module = importlib.import_module(module_name)
            return self._scan_module(module)
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {e}")
            return 0

    def load_from_file(self, file_path: Path) -> int:
        """Load plugins from a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            Number of plugins loaded
        """
        try:
            spec = importlib.util.spec_from_file_location("plugin_module", file_path)
            if spec is None or spec.loader is None:
                logger.error(f"Failed to load spec from {file_path}")
                return 0

            module = importlib.util.module_from_spec(spec)
            sys.modules["plugin_module"] = module
            spec.loader.exec_module(module)

            return self._scan_module(module)
        except Exception as e:
            logger.error(f"Failed to load plugin from {file_path}: {e}")
            return 0

    def load_from_directory(self, directory: Path) -> int:
        """Load all plugins from a directory.

        Args:
            directory: Directory containing plugin files

        Returns:
            Number of plugins loaded
        """
        if not directory.is_dir():
            logger.error(f"Directory not found: {directory}")
            return 0

        total_loaded = 0
        for file_path in directory.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            total_loaded += self.load_from_file(file_path)

        return total_loaded

    def _scan_module(self, module) -> int:
        """Scan module for plugin classes.

        Args:
            module: Module to scan

        Returns:
            Number of plugins found
        """
        count = 0
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, Plugin)
                and obj is not Plugin
                and not inspect.isabstract(obj)
            ):
                self.registry.register(obj)
                count += 1

        return count

    def discover_plugins(self, search_paths: Optional[List[Path]] = None) -> int:
        """Discover and load plugins from search paths.

        Args:
            search_paths: List of paths to search for plugins

        Returns:
            Total number of plugins loaded
        """
        if search_paths is None:
            # Default search paths
            search_paths = [
                Path.cwd() / "plugins",
                Path.home() / ".agentmind" / "plugins",
            ]

        total_loaded = 0
        for path in search_paths:
            if path.exists():
                logger.info(f"Searching for plugins in: {path}")
                total_loaded += self.load_from_directory(path)

        return total_loaded

    def load_builtin_plugins(self) -> int:
        """Load built-in plugins.

        Returns:
            Number of plugins loaded
        """
        try:
            # Try to load built-in plugins from agentmind.plugins.builtin
            return self.load_from_module("agentmind.plugins.builtin")
        except ImportError:
            logger.info("No built-in plugins found")
            return 0


def auto_discover_plugins(
    search_paths: Optional[List[Path]] = None
) -> PluginRegistry:
    """Auto-discover and load plugins.

    Args:
        search_paths: Optional list of paths to search

    Returns:
        Plugin registry with loaded plugins
    """
    loader = PluginLoader()

    # Load built-in plugins
    builtin_count = loader.load_builtin_plugins()
    logger.info(f"Loaded {builtin_count} built-in plugins")

    # Discover external plugins
    external_count = loader.discover_plugins(search_paths)
    logger.info(f"Loaded {external_count} external plugins")

    return loader.registry
