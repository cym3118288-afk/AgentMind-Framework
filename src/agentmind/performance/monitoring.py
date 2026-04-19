"""Monitoring and observability enhancements for AgentMind.

Provides Prometheus metrics, OpenTelemetry integration, and structured logging.
"""

import time
from typing import Any, Dict, Optional
from contextlib import contextmanager

try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


class PrometheusMetrics:
    """Prometheus metrics for AgentMind."""

    def __init__(self, registry: Optional[Any] = None):
        """Initialize Prometheus metrics.

        Args:
            registry: Optional Prometheus registry
        """
        if not PROMETHEUS_AVAILABLE:
            raise ImportError("prometheus_client required. Install with: pip install prometheus-client")

        self.registry = registry or CollectorRegistry()

        # Agent metrics
        self.agent_messages_total = Counter(
            'agentmind_agent_messages_total',
            'Total messages processed by agents',
            ['agent_name', 'role'],
            registry=self.registry
        )

        self.agent_processing_duration = Histogram(
            'agentmind_agent_processing_duration_seconds',
            'Time spent processing messages',
            ['agent_name', 'role'],
            registry=self.registry
        )

        # LLM metrics
        self.llm_requests_total = Counter(
            'agentmind_llm_requests_total',
            'Total LLM requests',
            ['provider', 'model'],
            registry=self.registry
        )

        self.llm_tokens_total = Counter(
            'agentmind_llm_tokens_total',
            'Total tokens used',
            ['provider', 'model', 'type'],
            registry=self.registry
        )

        self.llm_request_duration = Histogram(
            'agentmind_llm_request_duration_seconds',
            'LLM request duration',
            ['provider', 'model'],
            registry=self.registry
        )

        self.llm_errors_total = Counter(
            'agentmind_llm_errors_total',
            'Total LLM errors',
            ['provider', 'model', 'error_type'],
            registry=self.registry
        )

        # Cache metrics
        self.cache_hits_total = Counter(
            'agentmind_cache_hits_total',
            'Total cache hits',
            registry=self.registry
        )

        self.cache_misses_total = Counter(
            'agentmind_cache_misses_total',
            'Total cache misses',
            registry=self.registry
        )

        self.cache_size = Gauge(
            'agentmind_cache_size',
            'Current cache size',
            registry=self.registry
        )

        # Collaboration metrics
        self.collaboration_rounds = Histogram(
            'agentmind_collaboration_rounds',
            'Number of collaboration rounds',
            registry=self.registry
        )

        self.collaboration_duration = Histogram(
            'agentmind_collaboration_duration_seconds',
            'Total collaboration duration',
            registry=self.registry
        )

        # Memory metrics
        self.memory_messages_total = Gauge(
            'agentmind_memory_messages_total',
            'Total messages in memory',
            ['agent_name'],
            registry=self.registry
        )

    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format."""
        return generate_latest(self.registry)

    @contextmanager
    def track_llm_request(self, provider: str, model: str):
        """Context manager to track LLM request metrics."""
        start_time = time.time()
        try:
            yield
            duration = time.time() - start_time
            self.llm_requests_total.labels(provider=provider, model=model).inc()
            self.llm_request_duration.labels(provider=provider, model=model).observe(duration)
        except Exception as e:
            duration = time.time() - start_time
            self.llm_errors_total.labels(
                provider=provider,
                model=model,
                error_type=type(e).__name__
            ).inc()
            raise

    @contextmanager
    def track_agent_processing(self, agent_name: str, role: str):
        """Context manager to track agent processing metrics."""
        start_time = time.time()
        try:
            yield
            duration = time.time() - start_time
            self.agent_messages_total.labels(agent_name=agent_name, role=role).inc()
            self.agent_processing_duration.labels(agent_name=agent_name, role=role).observe(duration)
        except Exception:
            raise


class OpenTelemetryTracer:
    """OpenTelemetry integration for distributed tracing."""

    def __init__(
        self,
        service_name: str = "agentmind",
        exporter: Optional[Any] = None,
    ):
        """Initialize OpenTelemetry tracer.

        Args:
            service_name: Service name for traces
            exporter: Optional span exporter (defaults to console)
        """
        if not OTEL_AVAILABLE:
            raise ImportError("opentelemetry required. Install with: pip install opentelemetry-api opentelemetry-sdk")

        # Create resource
        resource = Resource.create({"service.name": service_name})

        # Set up tracer provider
        provider = TracerProvider(resource=resource)

        # Add span processor
        exporter = exporter or ConsoleSpanExporter()
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        # Set as global tracer provider
        trace.set_tracer_provider(provider)

        self.tracer = trace.get_tracer(__name__)

    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Start a new span.

        Args:
            name: Span name
            attributes: Optional span attributes

        Returns:
            Span context manager
        """
        span = self.tracer.start_span(name)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        return span

    @contextmanager
    def trace_operation(self, operation: str, **attributes):
        """Context manager for tracing operations."""
        with self.tracer.start_as_current_span(operation) as span:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
            yield span


class StructuredLogger:
    """Structured logging with context."""

    def __init__(self, name: str = "agentmind"):
        """Initialize structured logger.

        Args:
            name: Logger name
        """
        import logging
        import json

        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}

    def add_context(self, **kwargs) -> None:
        """Add context to all log messages."""
        self.context.update(kwargs)

    def clear_context(self) -> None:
        """Clear logging context."""
        self.context.clear()

    def _format_message(self, message: str, **kwargs) -> str:
        """Format message with context."""
        import json
        data = {
            "message": message,
            "context": self.context,
            **kwargs
        }
        return json.dumps(data)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(self._format_message(message, **kwargs))

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(self._format_message(message, **kwargs))

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(self._format_message(message, **kwargs))

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(self._format_message(message, **kwargs))


class PerformanceProfiler:
    """Performance profiling utilities."""

    def __init__(self):
        """Initialize performance profiler."""
        self.timings: Dict[str, list] = {}
        self.counters: Dict[str, int] = {}

    @contextmanager
    def profile(self, operation: str):
        """Profile an operation.

        Args:
            operation: Operation name

        Example:
            >>> profiler = PerformanceProfiler()
            >>> with profiler.profile("llm_call"):
            ...     await llm.generate(messages)
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            if operation not in self.timings:
                self.timings[operation] = []
            self.timings[operation].append(duration)

    def increment(self, counter: str, value: int = 1) -> None:
        """Increment a counter."""
        self.counters[counter] = self.counters.get(counter, 0) + value

    def get_stats(self) -> Dict[str, Any]:
        """Get profiling statistics."""
        stats = {}

        for operation, times in self.timings.items():
            stats[operation] = {
                "count": len(times),
                "total": sum(times),
                "avg": sum(times) / len(times) if times else 0,
                "min": min(times) if times else 0,
                "max": max(times) if times else 0,
            }

        stats["counters"] = self.counters.copy()
        return stats

    def reset(self) -> None:
        """Reset profiling data."""
        self.timings.clear()
        self.counters.clear()

    def print_report(self) -> None:
        """Print profiling report."""
        stats = self.get_stats()

        print("\n=== Performance Profile ===")
        print("\nTimings:")
        for operation, data in stats.items():
            if operation == "counters":
                continue
            print(f"\n{operation}:")
            print(f"  Count: {data['count']}")
            print(f"  Total: {data['total']:.3f}s")
            print(f"  Avg: {data['avg']:.3f}s")
            print(f"  Min: {data['min']:.3f}s")
            print(f"  Max: {data['max']:.3f}s")

        if stats.get("counters"):
            print("\nCounters:")
            for counter, value in stats["counters"].items():
                print(f"  {counter}: {value}")

        print("\n" + "=" * 30 + "\n")
