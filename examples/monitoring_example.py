"""Example: Monitoring and observability with Prometheus and OpenTelemetry.

This example demonstrates how to use monitoring and observability features
in AgentMind for production systems.
"""

import asyncio
from agentmind.core.agent import Agent
from agentmind.core.mind import AgentMind
from agentmind.core.types import Message
from agentmind.llm.ollama_provider import OllamaProvider

try:
    from agentmind.performance.monitoring import (
        PrometheusMetrics,
        OpenTelemetryTracer,
        StructuredLogger,
        PerformanceProfiler
    )
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    print("Warning: Monitoring packages not installed")


async def example_prometheus_metrics():
    """Demonstrate Prometheus metrics."""
    if not MONITORING_AVAILABLE:
        print("Skipping Prometheus example - packages not installed")
        return

    print("\n=== Prometheus Metrics Example ===\n")

    try:
        metrics = PrometheusMetrics()

        llm = OllamaProvider(model="llama3.2")
        agent = Agent(name="monitored_agent", role="assistant", llm_provider=llm)

        # Track operations
        for i in range(5):
            message = Message(role="user", content=f"Message {i}", sender="user")

            # Track agent processing
            with metrics.track_agent_processing(agent.name, agent.role):
                await agent.process_message(message)

            # Track LLM request
            with metrics.track_llm_request("ollama", "llama3.2"):
                await llm.generate([{"role": "user", "content": "Test"}])

        # Update cache metrics
        metrics.cache_hits_total.inc()
        metrics.cache_hits_total.inc()
        metrics.cache_misses_total.inc()

        # Export metrics
        metrics_data = metrics.export_metrics()
        print(f"Exported {len(metrics_data)} bytes of metrics")
        print("\nSample metrics:")
        print(metrics_data.decode()[:500])

    except Exception as e:
        print(f"Error in Prometheus example: {e}")


async def example_opentelemetry_tracing():
    """Demonstrate OpenTelemetry tracing."""
    if not MONITORING_AVAILABLE:
        print("Skipping OpenTelemetry example - packages not installed")
        return

    print("\n=== OpenTelemetry Tracing Example ===\n")

    try:
        tracer = OpenTelemetryTracer(service_name="agentmind-example")

        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        agent = Agent(name="traced_agent", role="assistant", llm_provider=llm)
        mind.add_agent(agent)

        # Trace collaboration
        with tracer.trace_operation(
            "collaboration",
            task="analyze_data",
            agent_count=1
        ):
            result = await mind.start_collaboration("Analyze this data", max_rounds=2)

        print("Tracing completed - check console output for spans")

    except Exception as e:
        print(f"Error in OpenTelemetry example: {e}")


async def example_structured_logging():
    """Demonstrate structured logging."""
    if not MONITORING_AVAILABLE:
        print("Skipping structured logging example - packages not installed")
        return

    print("\n=== Structured Logging Example ===\n")

    logger = StructuredLogger(name="agentmind")

    # Add context
    logger.add_context(
        session_id="session_123",
        user_id="user_456",
        environment="development"
    )

    # Log events
    logger.info("Starting agent collaboration", task="data_analysis")
    logger.info("Agent created", agent_name="analyst", role="analyst")
    logger.warning("High memory usage detected", memory_mb=512)
    logger.error("LLM timeout", provider="ollama", timeout_seconds=30)

    print("Structured logs written (check console output)")

    # Clear context
    logger.clear_context()


async def example_performance_profiling():
    """Demonstrate performance profiling."""
    print("\n=== Performance Profiling Example ===\n")

    profiler = PerformanceProfiler()

    llm = OllamaProvider(model="llama3.2")
    agent = Agent(name="profiled_agent", role="assistant", llm_provider=llm)

    # Profile different operations
    for i in range(3):
        with profiler.profile("message_processing"):
            message = Message(role="user", content=f"Message {i}", sender="user")
            await agent.process_message(message)

        with profiler.profile("llm_generation"):
            await llm.generate([{"role": "user", "content": "Test"}])

        profiler.increment("total_operations")
        profiler.increment("messages_sent")

    # Print profiling report
    profiler.print_report()


async def example_complete_monitoring():
    """Demonstrate complete monitoring setup."""
    print("\n=== Complete Monitoring Setup ===\n")

    # Setup monitoring components
    profiler = PerformanceProfiler()
    logger = StructuredLogger(name="agentmind")

    # Add context
    logger.add_context(session_id="demo_session", environment="production")

    # Create agents
    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(llm_provider=llm)

    analyst = Agent(name="analyst", role="analyst", llm_provider=llm)
    writer = Agent(name="writer", role="writer", llm_provider=llm)

    mind.add_agent(analyst)
    mind.add_agent(writer)

    # Log start
    logger.info("Starting collaboration", agents=["analyst", "writer"])

    # Profile collaboration
    with profiler.profile("full_collaboration"):
        result = await mind.start_collaboration(
            "Write a report on renewable energy",
            max_rounds=2
        )

    # Log completion
    logger.info("Collaboration completed", result_length=len(result))

    # Show profiling results
    profiler.print_report()

    print(f"\nResult preview: {result[:200]}...")


async def main():
    """Run all monitoring examples."""
    print("=" * 60)
    print("AgentMind Monitoring & Observability Examples")
    print("=" * 60)

    try:
        await example_prometheus_metrics()
        await example_opentelemetry_tracing()
        await example_structured_logging()
        await example_performance_profiling()
        await example_complete_monitoring()

        print("\n" + "=" * 60)
        print("All monitoring examples completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
