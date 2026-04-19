"""Plugin isolation and security features."""

import asyncio
import hashlib
import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from functools import wraps

# Try to import resource module (Unix-like systems only)
try:
    import resource

    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

logger = logging.getLogger(__name__)


class PluginPermission(BaseModel):
    """Plugin permission specification."""

    resource: str = Field(..., description="Resource name (e.g., 'file', 'network', 'memory')")
    actions: List[str] = Field(..., description="Allowed actions (e.g., ['read', 'write'])")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Additional constraints")


class PluginPermissions(BaseModel):
    """Complete permission set for a plugin."""

    plugin_name: str = Field(..., description="Plugin name")
    permissions: List[PluginPermission] = Field(
        default_factory=list, description="List of permissions"
    )
    allow_network: bool = Field(default=False, description="Allow network access")
    allow_filesystem: bool = Field(default=False, description="Allow filesystem access")
    allow_subprocess: bool = Field(default=False, description="Allow subprocess execution")
    allowed_apis: Set[str] = Field(default_factory=set, description="Allowed API endpoints")
    max_memory_mb: Optional[int] = Field(None, description="Maximum memory in MB")
    max_cpu_percent: Optional[float] = Field(None, description="Maximum CPU usage percent")


class ResourceLimits(BaseModel):
    """Resource limits for plugin execution."""

    max_execution_time: float = Field(default=30.0, description="Max execution time in seconds")
    max_memory_mb: int = Field(default=512, description="Max memory in MB")
    max_cpu_time: float = Field(default=10.0, description="Max CPU time in seconds")
    max_file_descriptors: int = Field(default=100, description="Max open file descriptors")


class ExecutionContext(BaseModel):
    """Execution context for sandboxed plugin."""

    plugin_name: str
    start_time: datetime = Field(default_factory=datetime.now)
    timeout: float = Field(default=30.0)
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    permissions: Optional[PluginPermissions] = None


class PluginSignature(BaseModel):
    """Plugin signature for verification."""

    plugin_name: str
    version: str
    checksum: str = Field(..., description="SHA256 checksum of plugin code")
    signature: Optional[str] = Field(None, description="Digital signature")
    signed_by: Optional[str] = Field(None, description="Signer identity")
    signed_at: Optional[datetime] = Field(None, description="Signature timestamp")


class PermissionManager:
    """Manage plugin permissions."""

    def __init__(self):
        """Initialize permission manager."""
        self._permissions: Dict[str, PluginPermissions] = {}
        self._default_permissions = PluginPermissions(
            plugin_name="default",
            allow_network=False,
            allow_filesystem=False,
            allow_subprocess=False,
            max_memory_mb=512,
            max_cpu_percent=50.0,
        )

    def register_permissions(self, permissions: PluginPermissions) -> None:
        """Register permissions for a plugin.

        Args:
            permissions: Plugin permissions
        """
        self._permissions[permissions.plugin_name] = permissions
        logger.info(f"Registered permissions for plugin: {permissions.plugin_name}")

    def get_permissions(self, plugin_name: str) -> PluginPermissions:
        """Get permissions for a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin permissions (default if not registered)
        """
        return self._permissions.get(plugin_name, self._default_permissions)

    def check_permission(self, plugin_name: str, resource: str, action: str) -> bool:
        """Check if plugin has permission for an action.

        Args:
            plugin_name: Plugin name
            resource: Resource name
            action: Action to perform

        Returns:
            True if permitted
        """
        permissions = self.get_permissions(plugin_name)

        # Check specific permissions
        for perm in permissions.permissions:
            if perm.resource == resource and action in perm.actions:
                return True

        # Check general permissions
        if resource == "network" and permissions.allow_network:
            return True
        if resource == "filesystem" and permissions.allow_filesystem:
            return True
        if resource == "subprocess" and permissions.allow_subprocess:
            return True

        return False

    def check_api_access(self, plugin_name: str, api_name: str) -> bool:
        """Check if plugin can access an API.

        Args:
            plugin_name: Plugin name
            api_name: API name

        Returns:
            True if allowed
        """
        permissions = self.get_permissions(plugin_name)
        return api_name in permissions.allowed_apis or "*" in permissions.allowed_apis

    def set_default_permissions(self, permissions: PluginPermissions) -> None:
        """Set default permissions for plugins.

        Args:
            permissions: Default permissions
        """
        self._default_permissions = permissions
        logger.info("Updated default plugin permissions")


class SandboxExecutor:
    """Execute plugins in sandboxed environment."""

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        """Initialize sandbox executor.

        Args:
            permission_manager: Permission manager instance
        """
        self.permission_manager = permission_manager or PermissionManager()
        self._active_contexts: Dict[str, ExecutionContext] = {}

    async def execute_with_timeout(
        self, plugin_name: str, func: Any, timeout: float, *args, **kwargs
    ) -> Any:
        """Execute function with timeout.

        Args:
            plugin_name: Plugin name
            func: Function to execute
            timeout: Timeout in seconds
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            asyncio.TimeoutError: If execution times out
        """
        try:
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            return result
        except asyncio.TimeoutError:
            logger.error(f"Plugin {plugin_name} execution timed out after {timeout}s")
            raise

    async def execute_sandboxed(
        self,
        plugin_name: str,
        func: Any,
        resource_limits: Optional[ResourceLimits] = None,
        *args,
        **kwargs,
    ) -> Any:
        """Execute function in sandboxed environment.

        Args:
            plugin_name: Plugin name
            func: Function to execute
            resource_limits: Resource limits
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        limits = resource_limits or ResourceLimits()

        # Create execution context
        context = ExecutionContext(
            plugin_name=plugin_name,
            timeout=limits.max_execution_time,
            resource_limits=limits,
            permissions=self.permission_manager.get_permissions(plugin_name),
        )

        self._active_contexts[plugin_name] = context

        try:
            # Set resource limits (Unix-like systems only)
            if HAS_RESOURCE:
                try:
                    # Memory limit
                    if limits.max_memory_mb:
                        max_memory = limits.max_memory_mb * 1024 * 1024
                        resource.setrlimit(resource.RLIMIT_AS, (max_memory, max_memory))

                    # CPU time limit
                    if limits.max_cpu_time:
                        resource.setrlimit(
                            resource.RLIMIT_CPU,
                            (int(limits.max_cpu_time), int(limits.max_cpu_time)),
                        )

                    # File descriptor limit
                    if limits.max_file_descriptors:
                        resource.setrlimit(
                            resource.RLIMIT_NOFILE,
                            (limits.max_file_descriptors, limits.max_file_descriptors),
                        )

                except (AttributeError, ValueError) as e:
                    # Resource limits not available on this platform
                    logger.warning(f"Could not set resource limits: {e}")
            else:
                logger.debug("Resource limits not available on this platform (Windows)")

            # Execute with timeout
            result = await self.execute_with_timeout(
                plugin_name, func, limits.max_execution_time, *args, **kwargs
            )

            return result

        finally:
            # Clean up context
            if plugin_name in self._active_contexts:
                del self._active_contexts[plugin_name]

            # Reset resource limits
            if HAS_RESOURCE:
                try:
                    resource.setrlimit(
                        resource.RLIMIT_AS, (resource.RLIM_INFINITY, resource.RLIM_INFINITY)
                    )
                    resource.setrlimit(
                        resource.RLIMIT_CPU, (resource.RLIM_INFINITY, resource.RLIM_INFINITY)
                    )
                except (AttributeError, ValueError):
                    pass

    def get_active_contexts(self) -> Dict[str, ExecutionContext]:
        """Get all active execution contexts.

        Returns:
            Dict of active contexts
        """
        return self._active_contexts.copy()


class SignatureVerifier:
    """Verify plugin signatures and checksums."""

    def __init__(self):
        """Initialize signature verifier."""
        self._signatures: Dict[str, PluginSignature] = {}
        self._trusted_signers: Set[str] = set()

    def calculate_checksum(self, content: bytes) -> str:
        """Calculate SHA256 checksum.

        Args:
            content: Content to hash

        Returns:
            Hex digest of checksum
        """
        return hashlib.sha256(content).hexdigest()

    def register_signature(self, signature: PluginSignature) -> None:
        """Register a plugin signature.

        Args:
            signature: Plugin signature
        """
        key = f"{signature.plugin_name}:{signature.version}"
        self._signatures[key] = signature
        logger.info(f"Registered signature for {key}")

    def verify_checksum(self, plugin_name: str, version: str, content: bytes) -> bool:
        """Verify plugin checksum.

        Args:
            plugin_name: Plugin name
            version: Plugin version
            content: Plugin content

        Returns:
            True if checksum matches
        """
        key = f"{plugin_name}:{version}"
        signature = self._signatures.get(key)

        if not signature:
            logger.warning(f"No signature found for {key}")
            return False

        calculated = self.calculate_checksum(content)
        matches = calculated == signature.checksum

        if not matches:
            logger.error(
                f"Checksum mismatch for {key}: expected {signature.checksum}, got {calculated}"
            )

        return matches

    def add_trusted_signer(self, signer: str) -> None:
        """Add a trusted signer.

        Args:
            signer: Signer identity
        """
        self._trusted_signers.add(signer)
        logger.info(f"Added trusted signer: {signer}")

    def is_trusted(self, plugin_name: str, version: str) -> bool:
        """Check if plugin is from trusted signer.

        Args:
            plugin_name: Plugin name
            version: Plugin version

        Returns:
            True if trusted
        """
        key = f"{plugin_name}:{version}"
        signature = self._signatures.get(key)

        if not signature or not signature.signed_by:
            return False

        return signature.signed_by in self._trusted_signers


def require_permission(resource: str, action: str):
    """Decorator to require permission for plugin method.

    Args:
        resource: Resource name
        action: Action name
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get plugin name from instance
            plugin_name = getattr(
                self, "get_metadata", lambda: type("obj", (object,), {"name": "unknown"})()
            )().name

            # Check permission (would need access to permission manager)
            # This is a simplified version - in production, inject permission manager
            logger.debug(f"Checking permission for {plugin_name}: {resource}.{action}")

            return await func(self, *args, **kwargs)

        return wrapper

    return decorator
