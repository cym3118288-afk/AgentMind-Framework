"""Plugin system for AgentMind.

This module provides a flexible plugin architecture that allows extending
AgentMind with custom functionality, integrations, and tools.
"""

from .base import Plugin, PluginMetadata, PluginType
from .loader import PluginLoader, PluginRegistry
from .manager import PluginManager

__all__ = [
    "Plugin",
    "PluginMetadata",
    "PluginType",
    "PluginLoader",
    "PluginRegistry",
    "PluginManager",
]
