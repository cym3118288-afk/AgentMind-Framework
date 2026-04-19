# Developer Tools & Utilities

Essential tools and utilities for building with AgentMind.

## Table of Contents

- [Debugging Tools](#debugging-tools)
- [Performance Profiling](#performance-profiling)
- [Cost Tracking](#cost-tracking)
- [Testing Utilities](#testing-utilities)
- [Development Helpers](#development-helpers)
- [CLI Tools](#cli-tools)

## Debugging Tools

### 1. Verbose Logging

Enable detailed logging to understand agent behavior:

```python
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# AgentMind will now log detailed information
from agentmind import Agent, AgentMind
```

### 2. Message History Inspector

Inspect conversation history:

```python
async def inspect_conversation():
    mind = AgentMind(llm_provider=llm)
    mind.add_agent(agent)
    
    result = await mind.collaborate("Task", max_rounds=3)
    
    # Inspect messages
    for i, msg in enumerate(mind.memory.get_messages()):
        print(f"\n--- Message {i+1} ---")
        print(f"Role: {msg.role}")
        print(f"Agent: {msg.agent}")
        print(f"Content: {msg.content[:100]}...")
```

### 3. Agent Response Debugger

Debug individual agent responses:

```python
from agentmind.core.types import Message

async def debug_agent_response(agent: Agent, prompt: str):
    """Debug a single agent's response"""
    messages = [Message(role="user", content=prompt)]
    
    print(f"Testing agent: {agent.name}")
    print(f"Prompt: {prompt}\n")
    
    response = await agent.generate(prompt, messages)
    
    print(f"Response: {response}")
    print(f"Response length: {len(response)} chars")
    
    return response

# Use it
await debug_agent_response(my_agent, "Test prompt")
```

### 4. Tool Execution Tracer

Trace tool executions:

```python
from agentmind.tools import Tool
import time

class TracedTool(Tool):
    """Wrapper that traces tool execution"""
    
    def __init__(self, tool: Tool):
        self.tool = tool
        super().__init__(
            name=tool.name,
            description=tool.description,
            parameters=tool.parameters
        )
    
    async def execute(self, **kwargs) -> str:
        start = time.time()
        print(f"[TOOL] Executing {self.name} with {kwargs}")
        
        try:
            result = await self.tool.execute(**kwargs)
            duration = time.time() - start
            print(f"[TOOL] {self.name} completed in {duration:.2f}s")
            return result
        except Exception as e:
            print(f"[TOOL] {self.name} failed: {e}")
            raise

# Wrap your tools
traced_tool = TracedTool(my_tool)
agent = Agent(name="Worker", tools=[traced_tool])
```

## Performance Profiling

### 1. Execution Timer

Time agent operations:

```python
import time
from contextlib import asynccontextmanager

@asynccontextmanager
async def timer(name: str):
    """Context manager for timing operations"""
    start = time.time()
    print(f"[TIMER] Starting {name}")
    try:
        yield
    finally:
        duration = time.time() - start
        print(f"[TIMER] {name} took {duration:.2f}s")

# Use it
async def profile_collaboration():
    async with timer("Full collaboration"):
        result = await mind.collaborate("Task", max_rounds=3)
    
    async with timer("Single agent"):
        response = await agent.generate("Prompt", [])
```

### 2. Token Counter

Track token usage:

```python
class TokenCounter:
    """Track token usage across operations"""
    
    def __init__(self):
        self.total_tokens = 0
        self.operations = []
    
    def count(self, text: str, operation: str):
        # Rough estimate: ~4 chars per token
        tokens = len(text) // 4
        self.total_tokens += tokens
        self.operations.append({
            "operation": operation,
            "tokens": tokens,
            "text_length": len(text)
        })
    
    def report(self):
        print(f"\n=== Token Usage Report ===")
        print(f"Total tokens: {self.total_tokens}")
        print(f"Operations: {len(self.operations)}")
        print(f"\nBreakdown:")
        for op in self.operations:
            print(f"  {op['operation']}: {op['tokens']} tokens")

# Use it
counter = TokenCounter()

async def tracked_generate(agent, prompt, messages):
    counter.count(prompt, f"{agent.name}_input")
    response = await agent.generate(prompt, messages)
    counter.count(response, f"{agent.name}_output")
    return response

# After operations
counter.report()
```

### 3. Memory Profiler

Monitor memory usage:

```python
import psutil
import os

class MemoryProfiler:
    """Profile memory usage"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_memory = self.get_memory()
    
    def get_memory(self):
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def report(self):
        current = self.get_memory()
        delta = current - self.start_memory
        print(f"\n=== Memory Usage ===")
        print(f"Start: {self.start_memory:.2f} MB")
        print(f"Current: {current:.2f} MB")
        print(f"Delta: {delta:.2f} MB")

# Use it
profiler = MemoryProfiler()

# Your code here

profiler.report()
```

## Cost Tracking

### 1. Built-in Cost Tracker

Use AgentMind's cost tracker:

```python
from agentmind.utils.observability import CostTracker

tracker = CostTracker()
tracker.start()

# Your operations
await mind.collaborate("Task", max_rounds=3)

tracker.end()

print(f"Total cost: ${tracker.total_cost:.4f}")
print(f"Total tokens: {tracker.total_tokens}")
print(f"Average cost per request: ${tracker.average_cost:.4f}")
```

### 2. Custom Cost Calculator

Calculate costs for different providers:

```python
class CostCalculator:
    """Calculate costs for different LLM providers"""
    
    PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},  # per 1K tokens
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "ollama": {"input": 0.0, "output": 0.0},  # Free!
    }
    
    def calculate(self, model: str, input_tokens: int, output_tokens: int):
        if model not in self.PRICING:
            return 0.0
        
        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost
    
    def compare(self, input_tokens: int, output_tokens: int):
        """Compare costs across providers"""
        print("\n=== Cost Comparison ===")
        for model, pricing in self.PRICING.items():
            cost = self.calculate(model, input_tokens, output_tokens)
            print(f"{model:20s}: ${cost:.4f}")

# Use it
calc = CostCalculator()
calc.compare(input_tokens=1000, output_tokens=500)
```

## Testing Utilities

### 1. Mock LLM Provider

Test without real LLM calls:

```python
from agentmind.llm import BaseLLMProvider

class MockLLMProvider(BaseLLMProvider):
    """Mock LLM for testing"""
    
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.call_count = 0
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response

# Use in tests
mock_llm = MockLLMProvider([
    "Response 1",
    "Response 2",
    "Response 3"
])

agent = Agent(name="Test", role="test", system_prompt="...", llm_provider=mock_llm)
```

### 2. Agent Test Harness

Test agent behavior:

```python
import pytest

class AgentTestHarness:
    """Test harness for agents"""
    
    def __init__(self, agent: Agent):
        self.agent = agent
        self.test_cases = []
    
    def add_test(self, prompt: str, expected_keywords: list[str]):
        """Add a test case"""
        self.test_cases.append({
            "prompt": prompt,
            "keywords": expected_keywords
        })
    
    async def run_tests(self):
        """Run all test cases"""
        results = []
        
        for test in self.test_cases:
            response = await self.agent.generate(test["prompt"], [])
            
            passed = all(
                keyword.lower() in response.lower()
                for keyword in test["keywords"]
            )
            
            results.append({
                "prompt": test["prompt"],
                "passed": passed,
                "response": response
            })
        
        return results

# Use it
harness = AgentTestHarness(my_agent)
harness.add_test("What is Python?", ["programming", "language"])
harness.add_test("Explain AI", ["artificial", "intelligence"])

results = await harness.run_tests()
for result in results:
    status = "✓" if result["passed"] else "✗"
    print(f"{status} {result['prompt']}")
```

## Development Helpers

### 1. Agent Builder

Quickly create agents with common patterns:

```python
class AgentBuilder:
    """Builder pattern for creating agents"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
        self.name = None
        self.role = None
        self.prompt = None
        self.tools = []
    
    def with_name(self, name: str):
        self.name = name
        return self
    
    def with_role(self, role: str):
        self.role = role
        return self
    
    def with_prompt(self, prompt: str):
        self.prompt = prompt
        return self
    
    def with_tools(self, *tools):
        self.tools.extend(tools)
        return self
    
    def build(self) -> Agent:
        return Agent(
            name=self.name,
            role=self.role,
            system_prompt=self.prompt,
            tools=self.tools,
            llm_provider=self.llm
        )

# Use it
agent = (AgentBuilder(llm)
    .with_name("Researcher")
    .with_role("researcher")
    .with_prompt("You are a researcher.")
    .with_tools(search_tool, calculator_tool)
    .build())
```

### 2. Prompt Template Manager

Manage reusable prompts:

```python
class PromptTemplates:
    """Reusable prompt templates"""
    
    RESEARCHER = """You are a thorough researcher.
    Find accurate, relevant information on: {topic}
    Focus on: {focus_areas}
    """
    
    WRITER = """You are a creative writer.
    Write {content_type} about: {topic}
    Tone: {tone}
    Length: {length}
    """
    
    ANALYST = """You are a data analyst.
    Analyze: {data_description}
    Focus on: {analysis_type}
    Provide: {deliverables}
    """
    
    @staticmethod
    def format(template: str, **kwargs) -> str:
        return template.format(**kwargs)

# Use it
prompt = PromptTemplates.format(
    PromptTemplates.RESEARCHER,
    topic="AI trends",
    focus_areas="recent developments, key players"
)
```

### 3. Configuration Manager

Manage agent configurations:

```python
import json
from pathlib import Path

class ConfigManager:
    """Manage agent configurations"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
    
    def save_agent_config(self, agent: Agent, filename: str):
        """Save agent configuration"""
        config = {
            "name": agent.name,
            "role": agent.role,
            "system_prompt": agent.system_prompt,
            "tools": [tool.name for tool in agent.tools]
        }
        
        path = self.config_dir / f"{filename}.json"
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_agent_config(self, filename: str) -> dict:
        """Load agent configuration"""
        path = self.config_dir / f"{filename}.json"
        with open(path, 'r') as f:
            return json.load(f)

# Use it
manager = ConfigManager()
manager.save_agent_config(my_agent, "researcher_config")
config = manager.load_agent_config("researcher_config")
```

## CLI Tools

### 1. Quick Test Command

Test agents from command line:

```bash
# Create a test script: test_agent.py
python -c "
from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
import asyncio

async def test():
    llm = OllamaProvider(model='llama3.2')
    mind = AgentMind(llm_provider=llm)
    agent = Agent(name='Test', role='test', system_prompt='You are helpful.')
    mind.add_agent(agent)
    result = await mind.collaborate('Hello!', max_rounds=1)
    print(result)

asyncio.run(test())
"
```

### 2. Benchmark Runner

Run performance benchmarks:

```python
# benchmark.py
import asyncio
import time
from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider

async def benchmark():
    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(llm_provider=llm)
    
    agent = Agent(
        name="Benchmark",
        role="test",
        system_prompt="You are a test agent."
    )
    mind.add_agent(agent)
    
    # Run multiple iterations
    iterations = 5
    times = []
    
    for i in range(iterations):
        start = time.time()
        await mind.collaborate(f"Test {i}", max_rounds=1)
        duration = time.time() - start
        times.append(duration)
        print(f"Iteration {i+1}: {duration:.2f}s")
    
    avg = sum(times) / len(times)
    print(f"\nAverage: {avg:.2f}s")
    print(f"Min: {min(times):.2f}s")
    print(f"Max: {max(times):.2f}s")

if __name__ == "__main__":
    asyncio.run(benchmark())
```

Run with: `python benchmark.py`

## Best Practices

1. **Use logging for debugging**: Enable verbose logging during development
2. **Profile before optimizing**: Measure performance before making changes
3. **Track costs**: Monitor API costs, especially in production
4. **Test thoroughly**: Use mock providers and test harnesses
5. **Version configurations**: Save and version agent configurations
6. **Monitor in production**: Use observability tools in production

## Additional Resources

- [Debugging Guide](docs/DEBUGGING.md)
- [Testing Guide](docs/TESTING.md)
- [Performance Guide](PERFORMANCE.md)
- [API Documentation](API.md)

---

Happy developing with AgentMind!
