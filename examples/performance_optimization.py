"""Example: Performance optimization with caching and batch processing.

This example demonstrates how to use AgentMind's performance features
to optimize multi - agent systems.
"""

import asyncio
from agentmind.core.agent import Agent
from agentmind.core.mind import AgentMind
from agentmind.core.types import Message
from agentmind.llm.ollama_provider import OllamaProvider
from agentmind.performance.cache import CacheManager, InMemoryCache
from agentmind.performance.batch import BatchProcessor
from agentmind.performance.memory_optimizer import MemoryOptimizer
from agentmind.performance.monitoring import PerformanceProfiler


async def example_caching():
    """Demonstrate response caching."""
    print("\n=== Response Caching Example ===\n")

    # Create cache manager
    cache = CacheManager(backend=InMemoryCache(max_size=100), default_ttl=3600, enabled=True)

    # Create LLM provider
    llm = OllamaProvider(model="llama3.2")

    # Simulate repeated queries
    messages = [{"role": "user", "content": "What is Python?"}]

    # First call - cache miss
    print("First call (cache miss)...")
    cached = await cache.get_response(messages)
    if not cached:
        response = await llm.generate(messages)
        await cache.set_response(messages, response)
        print(f"Response: {response.content[:100]}...")

    # Second call - cache hit
    print("\nSecond call (cache hit)...")
    cached = await cache.get_response(messages)
    if cached:
        print(f"Cached response: {cached.content[:100]}...")

    # Show statistics
    stats = cache.get_stats()
    print("\nCache Statistics:")
    print(f"  Hit rate: {stats['hit_rate']:.2%}")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")


async def example_batch_processing():
    """Demonstrate batch processing."""
    print("\n=== Batch Processing Example ===\n")

    llm = OllamaProvider(model="llama3.2")

    async def process_task(task_id: str, content: str) -> str:
        """Process a single task."""
        agent = Agent(name=f"agent_{task_id}", role="assistant", llm_provider=llm)
        message = Message(role="user", content=content, sender="user")
        response = await agent.process_message(message)
        return response.content if response else "No response"

    # Create batch processor
    processor = BatchProcessor(max_concurrent=5, timeout=30.0, retry_failed=True, max_retries=2)

    # Prepare tasks
    tasks = [
        {"id": "1", "task_id": "1", "content": "Explain machine learning"},
        {"id": "2", "task_id": "2", "content": "What is deep learning?"},
        {"id": "3", "task_id": "3", "content": "Describe neural networks"},
        {"id": "4", "task_id": "4", "content": "What is NLP?"},
        {"id": "5", "task_id": "5", "content": "Explain transformers"},
    ]

    print(f"Processing {len(tasks)} tasks with max {processor.max_concurrent} concurrent...")

    # Process batch
    results = await processor.process_batch(tasks, process_task)

    # Show results
    print("\nResults:")
    for result in results:
        if result.success:
            print(f"  Task {result.task_id}: Success ({result.duration:.2f}s)")
        else:
            print(f"  Task {result.task_id}: Failed - {result.error}")

    # Show statistics
    stats = processor.get_stats(results)
    print("\nBatch Statistics:")
    print(f"  Success rate: {stats['success_rate']:.2%}")
    print(f"  Average duration: {stats['avg_duration']:.2f}s")
    print(f"  Total duration: {stats['total_duration']:.2f}s")


async def example_memory_optimization():
    """Demonstrate memory optimization."""
    print("\n=== Memory Optimization Example ===\n")

    llm = OllamaProvider(model="llama3.2")
    agent = Agent(name="memory_agent", role="assistant", llm_provider=llm)

    # Generate many messages
    print("Generating 100 messages...")
    for i in range(100):
        message = Message(role="user", content=f"Message {i}", sender="user")
        await agent.process_message(message)

    print(f"Memory size before optimization: {len(agent.memory)} messages")

    # Create optimizer
    optimizer = MemoryOptimizer(max_messages=50, sliding_window=25, compression_threshold=40)

    # Optimize memory
    agent.memory = await optimizer.optimize(agent.memory, strategy="sliding_window")

    print(f"Memory size after optimization: {len(agent.memory)} messages")

    # Show statistics
    stats = optimizer.get_stats()
    print("\nOptimization Statistics:")
    print(f"  Messages processed: {stats['total_messages_processed']}")
    print(f"  Messages removed: {stats['total_messages_removed']}")
    print(f"  Removal rate: {stats['removal_rate']:.2%}")


async def example_profiling():
    """Demonstrate performance profiling."""
    print("\n=== Performance Profiling Example ===\n")

    profiler = PerformanceProfiler()

    llm = OllamaProvider(model="llama3.2")
    agent = Agent(name="profiled_agent", role="assistant", llm_provider=llm)

    # Profile operations
    for i in range(5):
        message = Message(role="user", content=f"Test message {i}", sender="user")

        with profiler.profile("agent_processing"):
            await agent.process_message(message)

        profiler.increment("messages_processed")

    # Print profiling report
    profiler.print_report()


async def example_complete_optimization():
    """Demonstrate complete optimization workflow."""
    print("\n=== Complete Optimization Workflow ===\n")

    # Setup components
    cache = CacheManager(enabled=True)
    optimizer = MemoryOptimizer(max_messages=50)
    profiler = PerformanceProfiler()

    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(llm_provider=llm)

    # Create agents
    analyst = Agent(name="analyst", role="analyst", llm_provider=llm)
    writer = Agent(name="writer", role="writer", llm_provider=llm)

    mind.add_agent(analyst)
    mind.add_agent(writer)

    # Run collaboration with profiling
    print("Running optimized collaboration...")

    with profiler.profile("collaboration"):
        result = await mind.start_collaboration(
            "Analyze the benefits of AI in healthcare", max_rounds=3
        )

    # Optimize memory
    print("\nOptimizing agent memory...")
    analyst.memory = await optimizer.optimize(analyst.memory)
    writer.memory = await optimizer.optimize(writer.memory)

    # Show results
    print(f"\nResult: {result[:200]}...")

    # Show statistics
    print("\nPerformance Statistics:")
    profiler.print_report()

    print("\nMemory Statistics:")
    stats = optimizer.get_stats()
    print(f"  Removal rate: {stats['removal_rate']:.2%}")

    print("\nCache Statistics:")
    cache_stats = cache.get_stats()
    print(f"  Hit rate: {cache_stats['hit_rate']:.2%}")


async def main():
    """Run all examples."""
    print("=" * 60)
    print("AgentMind Performance Optimization Examples")
    print("=" * 60)

    try:
        # Run examples
        await example_caching()
        await example_batch_processing()
        await example_memory_optimization()
        await example_profiling()
        await example_complete_optimization()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
