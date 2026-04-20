# Debugging Guide

Comprehensive guide to debugging AgentMind applications.

## Table of Contents

1. [Debug Mode](#debug-mode)
2. [Interactive Debugging](#interactive-debugging)
3. [Logging](#logging)
4. [Profiling](#profiling)
5. [Memory Debugging](#memory-debugging)
6. [Common Issues](#common-issues)
7. [Tools & Utilities](#tools--utilities)

## Debug Mode

### Enable Debug Mode

```python
from agentmind.dev_tools import DebugMode

# Create debug mode
debug = DebugMode(enabled=True)

# Log events
debug.log_event(
    event_type="message_sent",
    agent_name="agent1",
    data={"content": "Hello", "recipient": "agent2"}
)

# Time operations
debug.start_timer("llm_call")
response = await llm.generate(messages)
duration = debug.end_timer("llm_call")

debug.log_event(
    event_type="llm_response",
    agent_name="agent1",
    data={"response": response.content},
    duration=duration
)
```

### View Debug Events

```python
# Get all events
events = debug.get_events()

# Filter by type
message_events = debug.get_events(event_type="message_sent")

# Filter by agent
agent1_events = debug.get_events(agent_name="agent1")

# Print summary
debug.print_summary()
```

### Export Debug Data

```python
# Export to JSON
debug.export_events("debug_log.json")

# Clear events
debug.clear()
```

## Interactive Debugging

### Interactive Debugger

```python
from agentmind.dev_tools import InteractiveDebugger

# Create debugger
debugger = InteractiveDebugger(agent_mind)

# Add breakpoints
debugger.add_breakpoint(lambda msg: "error" in msg.content.lower())
debugger.add_breakpoint(lambda msg: msg.sender == "critical_agent")

# Step through collaboration
await debugger.step_through("Analyze this data", max_rounds=5)
```

### Breakpoint Examples

```python
# Break on specific content
debugger.add_breakpoint(lambda msg: "exception" in msg.content)

# Break on specific agent
debugger.add_breakpoint(lambda msg: msg.sender == "agent1")

# Break on message length
debugger.add_breakpoint(lambda msg: len(msg.content) > 1000)

# Complex condition
def complex_condition(msg):
    return (
        msg.role == "assistant" and
        "error" in msg.content.lower() and
        len(msg.content) > 100
    )

debugger.add_breakpoint(complex_condition)
```

### Inspect Agent State

```python
# During debugging, inspect state
for agent in mind.agents:
    print(f"\nAgent: {agent.name}")
    print(f"  Role: {agent.role}")
    print(f"  Active: {agent.is_active}")
    print(f"  Memory: {len(agent.memory)} messages")
    
    if agent.memory:
        print(f"  Last message: {agent.memory[-1].content[:100]}")
```

## Logging

### Structured Logging

```python
from agentmind.performance.monitoring import StructuredLogger

# Create logger
logger = StructuredLogger(name="agentmind")

# Add context
logger.add_context(
    session_id="session_123",
    user_id="user_456",
    environment="production"
)

# Log with context
logger.info("Processing message", agent="agent1", message_id="msg_789")
logger.warning("High memory usage", memory_mb=512)
logger.error("LLM timeout", provider="ollama", timeout=30)

# Clear context
logger.clear_context()
```

### Configure Logging Level

```python
import logging

# Set logging level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configure specific loggers
logging.getLogger("agentmind.core").setLevel(logging.DEBUG)
logging.getLogger("agentmind.llm").setLevel(logging.INFO)
```

### Log to File

```python
import logging

# Configure file handler
handler = logging.FileHandler("agentmind.log")
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

# Add to logger
logger = logging.getLogger("agentmind")
logger.addHandler(handler)
```

## Profiling

### Performance Profiler

```python
from agentmind.performance.monitoring import PerformanceProfiler

profiler = PerformanceProfiler()

# Profile operations
with profiler.profile("agent_processing"):
    await agent.process_message(message)

with profiler.profile("llm_call"):
    response = await llm.generate(messages)

with profiler.profile("memory_optimization"):
    agent.memory = await optimizer.optimize(agent.memory)

# Increment counters
profiler.increment("messages_processed")
profiler.increment("cache_hits")

# Get statistics
stats = profiler.get_stats()
print(f"LLM calls: {stats['llm_call']['count']}")
print(f"Average duration: {stats['llm_call']['avg']:.3f}s")

# Print report
profiler.print_report()
```

### Python cProfile

```python
import cProfile
import pstats

# Profile code
profiler = cProfile.Profile()
profiler.enable()

# Your code here
await mind.collaborate("Task", max_rounds=5)

profiler.disable()

# Print stats
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### Line Profiler

```python
# Install: pip install line_profiler

from line_profiler import LineProfiler

lp = LineProfiler()

# Add functions to profile
lp.add_function(agent.process_message)
lp.add_function(llm.generate)

# Run profiling
lp.enable()
await agent.process_message(message)
lp.disable()

# Print results
lp.print_stats()
```

## Memory Debugging

### Memory Leak Detection

```python
from agentmind.dev_tools import MemoryLeakDetector

detector = MemoryLeakDetector()

# Take snapshots
detector.take_snapshot("start", [agent1, agent2])

# Run workload
for i in range(100):
    await agent1.process_message(message)

detector.take_snapshot("after_100", [agent1, agent2])

# Run more
for i in range(100):
    await agent1.process_message(message)

detector.take_snapshot("after_200", [agent1, agent2])

# Analyze
detector.print_analysis()
```

### Memory Profiling with tracemalloc

```python
import tracemalloc

# Start tracing
tracemalloc.start()

# Take snapshot before
snapshot1 = tracemalloc.take_snapshot()

# Run code
await mind.collaborate("Task", max_rounds=10)

# Take snapshot after
snapshot2 = tracemalloc.take_snapshot()

# Compare
top_stats = snapshot2.compare_to(snapshot1, 'lineno')

print("Top 10 memory allocations:")
for stat in top_stats[:10]:
    print(stat)

# Stop tracing
tracemalloc.stop()
```

### Monitor Memory Usage

```python
import psutil
import os

def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

# Monitor during execution
print(f"Initial memory: {get_memory_usage():.2f} MB")

await mind.collaborate("Task", max_rounds=10)

print(f"After collaboration: {get_memory_usage():.2f} MB")

# Optimize memory
agent.memory = await optimizer.optimize(agent.memory)

print(f"After optimization: {get_memory_usage():.2f} MB")
```

## Common Issues

### Issue: Agent Not Responding

**Symptoms**: Agent returns None or empty responses

**Debug Steps**:

```python
# Check if agent is active
print(f"Agent active: {agent.is_active}")

# Check LLM provider
print(f"LLM provider: {agent.llm_provider}")

# Test LLM directly
if agent.llm_provider:
    response = await agent.llm_provider.generate([
        {"role": "user", "content": "Test"}
    ])
    print(f"LLM response: {response.content}")

# Check memory
print(f"Memory size: {len(agent.memory)}")
print(f"Last messages: {agent.memory[-3:]}")
```

### Issue: High Memory Usage

**Symptoms**: Memory grows continuously

**Debug Steps**:

```python
# Check memory size
print(f"Memory messages: {len(agent.memory)}")

# Calculate memory usage
import sys
memory_bytes = sum(sys.getsizeof(m.content) for m in agent.memory)
print(f"Memory size: {memory_bytes / 1024 / 1024:.2f} MB")

# Enable memory optimization
from agentmind.performance.memory_optimizer import MemoryOptimizer

optimizer = MemoryOptimizer(max_messages=50, sliding_window=25)
agent.memory = await optimizer.optimize(agent.memory)

print(f"After optimization: {len(agent.memory)} messages")
```

### Issue: Slow Performance

**Symptoms**: Operations take too long

**Debug Steps**:

```python
import time

# Profile operations
start = time.time()
response = await llm.generate(messages)
llm_duration = time.time() - start
print(f"LLM call: {llm_duration:.3f}s")

start = time.time()
await agent.process_message(message)
agent_duration = time.time() - start
print(f"Agent processing: {agent_duration:.3f}s")

# Check cache hit rate
if hasattr(llm, 'cache'):
    stats = llm.cache.get_stats()
    print(f"Cache hit rate: {stats['hit_rate']:.2%}")

# Enable caching if not already
from agentmind.performance.cache import CacheManager
cache = CacheManager(enabled=True)
```

### Issue: LLM Timeouts

**Symptoms**: Frequent timeout errors

**Debug Steps**:

```python
# Increase timeout
llm = OllamaProvider(model="llama3.2", timeout=60)

# Add retry logic
from agentmind.utils.retry import retry_with_backoff, RetryConfig

config = RetryConfig(
    max_retries=3,
    initial_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0
)

response = await retry_with_backoff(
    llm.generate,
    config,
    messages=messages
)

# Check LLM service
import aiohttp

async with aiohttp.ClientSession() as session:
    async with session.get("http://localhost:11434/api/tags") as resp:
        print(f"Ollama status: {resp.status}")
```

### Issue: Cache Not Working

**Symptoms**: Low cache hit rate

**Debug Steps**:

```python
# Check if cache is enabled
print(f"Cache enabled: {cache.enabled}")

# Check cache stats
stats = cache.get_stats()
print(f"Hits: {stats['hits']}")
print(f"Misses: {stats['misses']}")
print(f"Hit rate: {stats['hit_rate']:.2%}")

# Test cache directly
messages = [{"role": "user", "content": "Test"}]

# Set
await cache.set_response(messages, "Response")

# Get
result = await cache.get_response(messages)
print(f"Cached result: {result}")

# Check key generation
key1 = cache._generate_key(messages)
key2 = cache._generate_key(messages)
print(f"Keys match: {key1 == key2}")
```

## Tools & Utilities

### Development Environment Setup

```python
from agentmind.dev_tools import setup_development_environment

# Setup all dev tools
tools = setup_development_environment()

debug_mode = tools["debug_mode"]
benchmark_runner = tools["benchmark_runner"]
memory_detector = tools["memory_detector"]
```

### Benchmark Runner

```python
from agentmind.dev_tools import BenchmarkRunner

runner = BenchmarkRunner()

# Benchmark agent
results = await runner.benchmark_agent(
    agent=agent,
    messages=[Message(role="user", content="Test", sender="user")],
    iterations=10
)

print(f"Average: {results['avg_duration']:.3f}s")
print(f"Min: {results['min_duration']:.3f}s")
print(f"Max: {results['max_duration']:.3f}s")

# Benchmark collaboration
results = await runner.benchmark_collaboration(
    mind=mind,
    task="Analyze data",
    iterations=5,
    max_rounds=3
)

# Print all results
runner.print_results()

# Export results
runner.export_results("benchmarks.json")
```

### Debug Wrapper

Create a debug wrapper for agents:

```python
class DebugAgent:
    """Wrapper that adds debugging to an agent."""
    
    def __init__(self, agent, debug_mode):
        self.agent = agent
        self.debug = debug_mode
    
    async def process_message(self, message):
        """Process message with debugging."""
        self.debug.start_timer(f"{self.agent.name}_process")
        
        self.debug.log_event(
            event_type="message_received",
            agent_name=self.agent.name,
            data={"content": message.content, "sender": message.sender}
        )
        
        try:
            response = await self.agent.process_message(message)
            
            duration = self.debug.end_timer(f"{self.agent.name}_process")
            
            self.debug.log_event(
                event_type="message_sent",
                agent_name=self.agent.name,
                data={"content": response.content if response else None},
                duration=duration
            )
            
            return response
            
        except Exception as e:
            self.debug.log_event(
                event_type="error",
                agent_name=self.agent.name,
                data={"error": str(e), "type": type(e).__name__}
            )
            raise

# Use debug wrapper
debug = DebugMode(enabled=True)
debug_agent = DebugAgent(agent, debug)

await debug_agent.process_message(message)
debug.print_summary()
```

### Trace Decorator

```python
import functools
import time

def trace(func):
    """Decorator to trace function calls."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        print(f"→ Calling {func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start
            print(f"← {func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            print(f"✗ {func.__name__} failed after {duration:.3f}s: {e}")
            raise
    
    return wrapper

# Use decorator
@trace
async def process_with_trace(agent, message):
    return await agent.process_message(message)
```

## Debugging Checklist

When debugging issues, check:

- [ ] Agent is active (`agent.is_active`)
- [ ] LLM provider is configured (`agent.llm_provider`)
- [ ] LLM service is running (for Ollama/local models)
- [ ] API keys are set (for cloud providers)
- [ ] Memory size is reasonable (`len(agent.memory)`)
- [ ] Cache is enabled and working
- [ ] No timeout errors in logs
- [ ] Network connectivity (for remote LLMs)
- [ ] Sufficient system resources (CPU, memory)
- [ ] Correct message format
- [ ] Tool registry is configured (if using tools)

## Next Steps

- [Testing Guide](TESTING.md) - Testing best practices
- [Performance Guide](PERFORMANCE.md) - Optimization techniques
- [API Documentation](API.md) - Complete API reference
