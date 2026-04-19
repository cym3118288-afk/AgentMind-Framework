"""Plugin lifecycle management with hooks and health monitoring."""

import asyncio
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PluginState(str, Enum):
    """Plugin lifecycle states."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    INACTIVE = "inactive"
    ERROR = "error"
    SUSPENDED = "suspended"


class HealthStatus(BaseModel):
    """Plugin health status."""

    healthy: bool = Field(..., description="Whether plugin is healthy")
    state: PluginState = Field(..., description="Current plugin state")
    last_check: datetime = Field(default_factory=datetime.now, description="Last health check time")
    error_count: int = Field(default=0, description="Number of errors since last reset")
    uptime_seconds: float = Field(default=0.0, description="Uptime in seconds")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional health details")


class LifecycleHooks:
    """Lifecycle hooks for plugins."""

    def __init__(self):
        """Initialize lifecycle hooks."""
        self._hooks: Dict[str, List[Callable]] = {
            "pre_initialize": [],
            "post_initialize": [],
            "pre_activate": [],
            "post_activate": [],
            "pre_deactivate": [],
            "post_deactivate": [],
            "pre_cleanup": [],
            "post_cleanup": [],
            "on_error": [],
            "on_health_check": [],
        }

    def register(self, hook_name: str, callback: Callable) -> None:
        """Register a lifecycle hook.

        Args:
            hook_name: Name of the hook
            callback: Callback function
        """
        if hook_name not in self._hooks:
            raise ValueError(f"Unknown hook: {hook_name}")

        self._hooks[hook_name].append(callback)
        logger.debug(f"Registered hook: {hook_name}")

    async def execute(self, hook_name: str, plugin: Any, **kwargs) -> None:
        """Execute all callbacks for a hook.

        Args:
            hook_name: Name of the hook
            plugin: Plugin instance
            **kwargs: Additional arguments for callbacks
        """
        if hook_name not in self._hooks:
            logger.warning(f"Unknown hook: {hook_name}")
            return

        for callback in self._hooks[hook_name]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(plugin, **kwargs)
                else:
                    callback(plugin, **kwargs)
            except Exception as e:
                logger.error(f"Error executing hook {hook_name}: {e}")


class PluginLifecycleManager:
    """Manage plugin lifecycle with state tracking and health monitoring."""

    def __init__(self):
        """Initialize lifecycle manager."""
        self._states: Dict[str, PluginState] = {}
        self._health_status: Dict[str, HealthStatus] = {}
        self._start_times: Dict[str, datetime] = {}
        self._hooks: Dict[str, LifecycleHooks] = {}
        self._error_counts: Dict[str, int] = {}

    def register_plugin(self, plugin_name: str) -> None:
        """Register a plugin for lifecycle management.

        Args:
            plugin_name: Name of the plugin
        """
        self._states[plugin_name] = PluginState.UNINITIALIZED
        self._health_status[plugin_name] = HealthStatus(
            healthy=False, state=PluginState.UNINITIALIZED
        )
        self._hooks[plugin_name] = LifecycleHooks()
        self._error_counts[plugin_name] = 0
        logger.info(f"Registered plugin for lifecycle management: {plugin_name}")

    def get_hooks(self, plugin_name: str) -> Optional[LifecycleHooks]:
        """Get lifecycle hooks for a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            LifecycleHooks instance or None
        """
        return self._hooks.get(plugin_name)

    async def initialize(self, plugin_name: str, plugin: Any) -> bool:
        """Initialize a plugin with lifecycle hooks.

        Args:
            plugin_name: Name of the plugin
            plugin: Plugin instance

        Returns:
            True if successful
        """
        if plugin_name not in self._states:
            self.register_plugin(plugin_name)

        try:
            self._states[plugin_name] = PluginState.INITIALIZING

            # Execute pre-initialize hooks
            hooks = self._hooks.get(plugin_name)
            if hooks:
                await hooks.execute("pre_initialize", plugin)

            # Initialize plugin
            await plugin.initialize()

            # Execute post-initialize hooks
            if hooks:
                await hooks.execute("post_initialize", plugin)

            self._states[plugin_name] = PluginState.INACTIVE
            self._start_times[plugin_name] = datetime.now()

            logger.info(f"Plugin initialized: {plugin_name}")
            return True

        except Exception as e:
            self._states[plugin_name] = PluginState.ERROR
            self._error_counts[plugin_name] = self._error_counts.get(plugin_name, 0) + 1
            logger.error(f"Failed to initialize plugin {plugin_name}: {e}")

            # Execute error hooks
            hooks = self._hooks.get(plugin_name)
            if hooks:
                await hooks.execute("on_error", plugin, error=e, phase="initialize")

            return False

    async def activate(self, plugin_name: str, plugin: Any) -> bool:
        """Activate a plugin.

        Args:
            plugin_name: Name of the plugin
            plugin: Plugin instance

        Returns:
            True if successful
        """
        if self._states.get(plugin_name) not in [PluginState.INACTIVE, PluginState.SUSPENDED]:
            logger.warning(
                f"Cannot activate plugin {plugin_name} in state {self._states.get(plugin_name)}"
            )
            return False

        try:
            # Execute pre-activate hooks
            hooks = self._hooks.get(plugin_name)
            if hooks:
                await hooks.execute("pre_activate", plugin)

            self._states[plugin_name] = PluginState.ACTIVE

            # Execute post-activate hooks
            if hooks:
                await hooks.execute("post_activate", plugin)

            logger.info(f"Plugin activated: {plugin_name}")
            return True

        except Exception as e:
            self._states[plugin_name] = PluginState.ERROR
            self._error_counts[plugin_name] = self._error_counts.get(plugin_name, 0) + 1
            logger.error(f"Failed to activate plugin {plugin_name}: {e}")
            return False

    async def deactivate(self, plugin_name: str, plugin: Any) -> bool:
        """Deactivate a plugin.

        Args:
            plugin_name: Name of the plugin
            plugin: Plugin instance

        Returns:
            True if successful
        """
        if self._states.get(plugin_name) != PluginState.ACTIVE:
            logger.warning(
                f"Cannot deactivate plugin {plugin_name} in state {self._states.get(plugin_name)}"
            )
            return False

        try:
            self._states[plugin_name] = PluginState.DEACTIVATING

            # Execute pre-deactivate hooks
            hooks = self._hooks.get(plugin_name)
            if hooks:
                await hooks.execute("pre_deactivate", plugin)

            self._states[plugin_name] = PluginState.INACTIVE

            # Execute post-deactivate hooks
            if hooks:
                await hooks.execute("post_deactivate", plugin)

            logger.info(f"Plugin deactivated: {plugin_name}")
            return True

        except Exception as e:
            self._states[plugin_name] = PluginState.ERROR
            logger.error(f"Failed to deactivate plugin {plugin_name}: {e}")
            return False

    async def cleanup(self, plugin_name: str, plugin: Any) -> bool:
        """Cleanup and shutdown a plugin.

        Args:
            plugin_name: Name of the plugin
            plugin: Plugin instance

        Returns:
            True if successful
        """
        try:
            # Execute pre-cleanup hooks
            hooks = self._hooks.get(plugin_name)
            if hooks:
                await hooks.execute("pre_cleanup", plugin)

            # Shutdown plugin
            await plugin.shutdown()

            # Execute post-cleanup hooks
            if hooks:
                await hooks.execute("post_cleanup", plugin)

            self._states[plugin_name] = PluginState.UNINITIALIZED

            logger.info(f"Plugin cleaned up: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup plugin {plugin_name}: {e}")
            return False

    async def check_health(self, plugin_name: str, plugin: Any) -> HealthStatus:
        """Check plugin health.

        Args:
            plugin_name: Name of the plugin
            plugin: Plugin instance

        Returns:
            HealthStatus
        """
        try:
            # Execute health check hooks
            hooks = self._hooks.get(plugin_name)
            if hooks:
                await hooks.execute("on_health_check", plugin)

            # Check plugin health
            healthy = plugin.health_check() if hasattr(plugin, "health_check") else True

            # Calculate uptime
            uptime = 0.0
            if plugin_name in self._start_times:
                uptime = (datetime.now() - self._start_times[plugin_name]).total_seconds()

            status = HealthStatus(
                healthy=healthy,
                state=self._states.get(plugin_name, PluginState.UNINITIALIZED),
                last_check=datetime.now(),
                error_count=self._error_counts.get(plugin_name, 0),
                uptime_seconds=uptime,
                details={},
            )

            self._health_status[plugin_name] = status
            return status

        except Exception as e:
            logger.error(f"Health check failed for plugin {plugin_name}: {e}")
            return HealthStatus(
                healthy=False,
                state=PluginState.ERROR,
                error_count=self._error_counts.get(plugin_name, 0) + 1,
                details={"error": str(e)},
            )

    def get_state(self, plugin_name: str) -> Optional[PluginState]:
        """Get current plugin state.

        Args:
            plugin_name: Name of the plugin

        Returns:
            PluginState or None
        """
        return self._states.get(plugin_name)

    def get_health_status(self, plugin_name: str) -> Optional[HealthStatus]:
        """Get cached health status.

        Args:
            plugin_name: Name of the plugin

        Returns:
            HealthStatus or None
        """
        return self._health_status.get(plugin_name)

    def reset_error_count(self, plugin_name: str) -> None:
        """Reset error count for a plugin.

        Args:
            plugin_name: Name of the plugin
        """
        self._error_counts[plugin_name] = 0
        logger.info(f"Reset error count for plugin: {plugin_name}")

    def get_all_states(self) -> Dict[str, PluginState]:
        """Get all plugin states.

        Returns:
            Dict mapping plugin names to states
        """
        return self._states.copy()

    def get_all_health_status(self) -> Dict[str, HealthStatus]:
        """Get all plugin health statuses.

        Returns:
            Dict mapping plugin names to health statuses
        """
        return self._health_status.copy()
