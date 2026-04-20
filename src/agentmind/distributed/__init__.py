"""
Distributed execution module for AgentMind
Supports Celery and Ray backends for distributed agent execution
"""

from typing import Any

# Try to import backends
try:
    from .celery_backend import (
        DistributedMind as CeleryDistributedMind,
    )

    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

try:
    from .ray_backend import (
        RayDistributedMind,
    )

    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False


def create_distributed_mind(
    backend: str = "ray",
    **kwargs,
) -> Any:
    """
    Factory function to create distributed mind with specified backend

    Args:
        backend: Backend to use ('ray' or 'celery')
        **kwargs: Backend-specific configuration

    Returns:
        Distributed mind instance

    Examples:
        >>> # Ray backend
        >>> mind = create_distributed_mind('ray', num_cpus=4)
        >>>
        >>> # Celery backend
        >>> mind = create_distributed_mind(
        ...     'celery',
        ...     broker_url='redis://localhost:6379/0'
        ... )
    """
    if backend == "ray":
        if not RAY_AVAILABLE:
            raise ImportError("Ray not available. Install with: pip install ray")
        return RayDistributedMind(**kwargs)

    elif backend == "celery":
        if not CELERY_AVAILABLE:
            raise ImportError("Celery not available. Install with: pip install celery redis")
        return CeleryDistributedMind(**kwargs)

    else:
        raise ValueError(f"Unknown backend: {backend}. Choose 'ray' or 'celery'")


__all__ = [
    "create_distributed_mind",
    "CELERY_AVAILABLE",
    "RAY_AVAILABLE",
]

# Conditionally export backend-specific classes
if CELERY_AVAILABLE:
    __all__.extend(
        [
            "CeleryDistributedMind",
            "LoadBalancer",
            "create_celery_app",
            "start_worker",
        ]
    )

if RAY_AVAILABLE:
    __all__.extend(
        [
            "RayDistributedMind",
            "RayActorPool",
            "FaultTolerantExecutor",
        ]
    )
