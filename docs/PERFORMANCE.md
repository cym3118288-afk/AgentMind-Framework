# Performance Optimization Guide

This guide covers performance optimization techniques, best practices, and benchmarking for AgentMind.

## Table of Contents

1. [Response Caching](#response-caching)
2. [Batch Processing](#batch-processing)
3. [Memory Optimization](#memory-optimization)
4. [Streaming Performance](#streaming-performance)
5. [Connection Pooling](#connection-pooling)
6. [Monitoring & Profiling](#monitoring--profiling)
7. [Best Practices](#best-practices)
8. [Benchmarking](#benchmarking)

## Response Caching

AgentMind provides a flexible caching layer to reduce redundant LLM calls and improve response times.

### In-Memory Cache

```python
from agentmind.performance.cache import InMemoryCache, CacheManager

# Create cache manager with in-memory backend
cache = CacheManager(
    backend=InMemoryCache(max_size=1000),
    default_ttl=3600,  # 1 hour
    enabled=True
)

# Use with LLM provider
messages = [{"role": "user", "content": "Hello"}]

# Check cache first
cached_response = await cache.get_response(messages)
if cached_response:
    print("Cache hit!")
else:
    # Generate and cache
    response = await llm.generate(messages)
    await cache.set_response(messages, response)
```

### Redis Cache (Distributed)

For distributed systems, use Redis for shared caching:

```python
from agentmind.performance.cache import RedisCache, CacheManager

# Create Redis-backed cache
redis_backend = RedisCache(
    host="localhost",
    port=6379,
    db=0,
    prefix="agentmind:"
)

cache = CacheManager(backend=redis_backend, default_ttl=3600)
```

### Cache Statistics

Monitor cache performance:

```python
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Total requests: {stats['total_requests']}")
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")
```

### Cache Invalidation

Invalidate cached responses when needed:

```python
# Invalidate specific response
await cache.invalidate(messages)

# Clear all cache
await cache.clear()
```

## Batch Processing

Process multiple agent tasks efficiently with concurrency control.

### Basic Batch Processing

```python
from agentmind.performance.batch import BatchProcessor

async def process_message(content: str) -> str:
    agent = Agent(name="processor", role="assistant", llm_provider=llm)
    message = Message(role="user", content=content, sender="user")
    response = await agent.process_message(message)
    return response.content

# Create batch processor
processor = BatchProcessor(
    max_concurrent=10,  # Process 10 tasks at once
    timeout=30.0,       # 30 second timeout per task
    retry_failed=True,  # Retry failed tasks
    max_retries=3
)

# Prepare tasks
tasks = [
    {"id": "1", "content": "Analyze this data"},
    {"id": "2", "content": "Summarize this text"},
    {"id": "3", "content": "Generate a report"},
]

# Process batch
results = await processor.process_batch(tasks, process_message)

# Check results
for result in results:
    if result.success:
        print(f"Task {result.task_id}: {result.result}")
    else:
        print(f"Task {result.task_id} failed: {result.error}")
```

### Stream Processing

Process tasks from a queue:

```python
import asyncio

# Create task queue
task_queue = asyncio.Queue()

# Add tasks to queue
for i in range(100):
    await task_queue.put({"id": str(i), "content": f"Task {i}"})

# Process stream
async def handle_result(result):
    print(f"Completed: {result.task_id}")

await processor.process_stream(task_queue, process_message, handle_result)
```

### Batch Statistics

```python
stats = processor.get_stats(results)
print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Average duration: {stats['avg_duration']:.3f}s")
print(f"Total duration: {stats['total_duration']:.3f}s")
```

## Memory Optimization

Optimize memory usage for long-running conversations.

### Sliding Window

Keep only recent messages:

```python
from agentmind.performance.memory_optimizer import MemoryOptimizer

optimizer = MemoryOptimizer(
    max_messages=100,      # Maximum messages before optimization
    sliding_window=50,     # Keep last 50 messages
    compression_threshold=75
)

# Optimize agent memory
agent.memory = await optimizer.optimize(
    agent.memory,
    strategy="sliding_window"
)
```

### Conversation Compression

Compress old messages using summarization:

```python
from agentmind.performance.memory_optimizer import ConversationCompressor

compressor = ConversationCompressor(
    llm_provider=llm,
    compression_ratio=0.5
)

# Compress messages
compressed, stats = await compressor.compress_messages(
    agent.memory,
    preserve_recent=10  # Keep last 10 messages uncompressed
)

print(f"Compression ratio: {stats.compression_ratio:.2%}")
print(f"Tokens saved: {stats.tokens_saved}")

agent.memory = compressed
```

### Hybrid Strategy

Combine sliding window and compression:

```python
agent.memory = await optimizer.optimize(
    agent.memory,
    strategy="hybrid"  # Uses both sliding window and compression
)
```

### Memory Statistics

```python
stats = optimizer.get_stats()
print(f"Messages processed: {stats['total_messages_processed']}")
print(f"Messages removed: {stats['total_messages_removed']}")
print(f"Removal rate: {stats['removal_rate']:.2%}")
```

## Streaming Performance

Optimize streaming responses with buffering and backpressure.

### Stream Buffering

```python
from agentmind.performance.streaming import StreamBuffer

buffer = StreamBuffer(
    buffer_size=100,      # Buffer up to 100 items
    flush_interval=0.1    # Flush every 0.1 seconds
)

# Add items to buffer
await buffer.add("token1")
await buffer.add("token2")

# Get buffered items
items = await buffer.get_buffered()
```

### Backpressure Management

```python
from agentmind.performance.streaming import BackpressureManager

manager = BackpressureManager(
    max_queue_size=1000,
    high_watermark=0.8,  # Apply backpressure at 80% full
    low_watermark=0.5    # Release at 50% full
)

# Producer
await manager.put(item)

# Consumer
item = await manager.get()

# Check status
if manager.is_backpressure_active():
    print("Backpressure active - slowing down")
```

### Optimized Stream Processing

```python
from agentmind.performance.streaming import OptimizedStreamProcessor

processor = OptimizedStreamProcessor(
    chunk_size=10,        # Buffer 10 tokens
    buffer_timeout=0.05   # Max 50ms wait
)

async for chunk in processor.process_stream(llm_stream):
    print(chunk, end='', flush=True)
```

## Connection Pooling

Reuse LLM provider connections for better performance.

```python
from agentmind.performance.memory_optimizer import ConnectionPool

pool = ConnectionPool(max_connections=10)

async def create_llm_connection():
    return OllamaProvider(model="llama3.2")

# Acquire connection
llm = await pool.acquire(create_llm_connection)

# Use connection
response = await llm.generate(messages)

# Release back to pool
await pool.release(llm)

# Check pool stats
stats = pool.get_stats()
print(f"Available: {stats['available']}")
print(f"In use: {stats['in_use']}")
```

## Monitoring & Profiling

### Prometheus Metrics

Export metrics for monitoring:

```python
from agentmind.performance.monitoring import PrometheusMetrics

metrics = PrometheusMetrics()

# Track LLM requests
with metrics.track_llm_request("ollama", "llama3.2"):
    response = await llm.generate(messages)

# Track agent processing
with metrics.track_agent_processing("agent1", "analyst"):
    await agent.process_message(message)

# Export metrics
metrics_data = metrics.export_metrics()
```

### OpenTelemetry Tracing

Distributed tracing for complex workflows:

```python
from agentmind.performance.monitoring import OpenTelemetryTracer

tracer = OpenTelemetryTracer(service_name="agentmind")

# Trace operations
with tracer.trace_operation("collaboration", task="analyze_data"):
    result = await mind.collaborate("Analyze this data")
```

### Structured Logging

Context-aware logging:

```python
from agentmind.performance.monitoring import StructuredLogger

logger = StructuredLogger(name="agentmind")

# Add context
logger.add_context(session_id="123", user_id="user1")

# Log with context
logger.info("Processing message", agent="agent1", message_id="msg1")
```

### Performance Profiling

Profile hot paths:

```python
from agentmind.performance.monitoring import PerformanceProfiler

profiler = PerformanceProfiler()

# Profile operations
with profiler.profile("llm_call"):
    await llm.generate(messages)

with profiler.profile("agent_processing"):
    await agent.process_message(message)

# Get statistics
stats = profiler.get_stats()
profiler.print_report()
```

## Best Practices

### 1. Enable Caching for Repeated Queries

```python
# Good: Cache enabled for repeated queries
cache = CacheManager(enabled=True, default_ttl=3600)

# Bad: No caching for repeated queries
cache = CacheManager(enabled=False)
```

### 2. Use Batch Processing for Multiple Tasks

```python
# Good: Process tasks in batches
processor = BatchProcessor(max_concurrent=10)
results = await processor.process_batch(tasks, process_func)

# Bad: Process tasks sequentially
for task in tasks:
    await process_func(**task)
```

### 3. Optimize Memory for Long Conversations

```python
# Good: Regular memory optimization
if len(agent.memory) > 100:
    agent.memory = await optimizer.optimize(agent.memory)

# Bad: Unbounded memory growth
# No optimization - memory grows indefinitely
```

### 4. Use Connection Pooling

```python
# Good: Reuse connections
pool = ConnectionPool(max_connections=10)
llm = await pool.acquire(create_connection)
# ... use llm ...
await pool.release(llm)

# Bad: Create new connection each time
llm = OllamaProvider(model="llama3.2")  # New connection every time
```

### 5. Monitor Performance

```python
# Good: Track metrics
metrics = PrometheusMetrics()
with metrics.track_llm_request("ollama", "llama3.2"):
    response = await llm.generate(messages)

# Bad: No monitoring
response = await llm.generate(messages)  # No visibility
```

## Benchmarking

### Run Benchmarks

```python
from agentmind.dev_tools import BenchmarkRunner

runner = BenchmarkRunner()

# Benchmark agent
results = await runner.benchmark_agent(
    agent=agent,
    messages=[Message(role="user", content="Test", sender="user")],
    iterations=10
)

print(f"Average duration: {results['avg_duration']:.3f}s")

# Benchmark collaboration
results = await runner.benchmark_collaboration(
    mind=mind,
    task="Analyze this data",
    iterations=5,
    max_rounds=3
)

runner.print_results()
```

### Compare Performance

```python
# Benchmark with caching
cache = CacheManager(enabled=True)
results_cached = await runner.benchmark_agent(agent, messages, 10)

# Benchmark without caching
cache = CacheManager(enabled=False)
results_uncached = await runner.benchmark_agent(agent, messages, 10)

speedup = results_uncached['avg_duration'] / results_cached['avg_duration']
print(f"Caching speedup: {speedup:.2f}x")
```

### Memory Leak Detection

```python
from agentmind.dev_tools import MemoryLeakDetector

detector = MemoryLeakDetector()

# Take snapshots during execution
detector.take_snapshot("start", [agent])

# ... run workload ...

detector.take_snapshot("after_100_messages", [agent])

# ... run more ...

detector.take_snapshot("after_200_messages", [agent])

# Analyze for leaks
detector.print_analysis()
```

## Performance Targets

Recommended performance targets for production systems:

- **Cache Hit Rate**: > 30% for typical workloads
- **Response Time**: < 2s for cached responses, < 10s for LLM calls
- **Memory Growth**: < 10MB per 1000 messages with optimization
- **Batch Throughput**: > 100 tasks/minute with 10 concurrent workers
- **Success Rate**: > 95% for batch processing

## Troubleshooting

### High Memory Usage

```python
# Check memory stats
stats = optimizer.get_stats()
if stats['removal_rate'] < 0.5:
    # Increase optimization frequency
    optimizer = MemoryOptimizer(max_messages=50, sliding_window=25)
```

### Low Cache Hit Rate

```python
# Check cache stats
stats = cache.get_stats()
if stats['hit_rate'] < 0.2:
    # Increase TTL or cache size
    cache = CacheManager(default_ttl=7200)
    cache.backend = InMemoryCache(max_size=5000)
```

### Slow Batch Processing

```python
# Increase concurrency
processor = BatchProcessor(max_concurrent=20)

# Or reduce timeout
processor = BatchProcessor(timeout=10.0)
```

## Next Steps

- [Testing Guide](TESTING.md) - Testing best practices
- [Debugging Guide](DEBUGGING.md) - Debugging techniques
- [API Documentation](API.md) - Complete API reference
