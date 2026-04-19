# Testing Guide

Comprehensive guide to testing AgentMind applications.

## Table of Contents

1. [Test Setup](#test-setup)
2. [Unit Testing](#unit-testing)
3. [Integration Testing](#integration-testing)
4. [Property-Based Testing](#property-based-testing)
5. [Performance Testing](#performance-testing)
6. [Mocking & Fixtures](#mocking--fixtures)
7. [Test Coverage](#test-coverage)
8. [Best Practices](#best-practices)

## Test Setup

### Installation

```bash
pip install pytest pytest-asyncio pytest-cov hypothesis
```

### Configuration

Create `pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --cov=src/agentmind
    --cov-report=term-missing
    --cov-report=html
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agent.py

# Run with coverage
pytest --cov=src/agentmind --cov-report=html

# Run specific test
pytest tests/test_agent.py::TestAgent::test_agent_creation

# Run with verbose output
pytest -v

# Run in parallel
pytest -n auto
```

## Unit Testing

### Testing Agents

```python
import pytest
from agentmind.core.agent import Agent
from agentmind.core.types import Message

class TestAgent:
    """Unit tests for Agent class."""

    def test_agent_creation(self):
        """Test agent can be created."""
        agent = Agent(name="test_agent", role="assistant")
        assert agent.name == "test_agent"
        assert agent.role == "assistant"
        assert agent.is_active is True

    def test_agent_name_validation(self):
        """Test agent name validation."""
        with pytest.raises(ValueError):
            Agent(name="", role="assistant")

    @pytest.mark.asyncio
    async def test_agent_process_message(self):
        """Test agent can process messages."""
        agent = Agent(name="test_agent", role="assistant")
        message = Message(role="user", content="Hello", sender="user")
        
        response = await agent.process_message(message)
        
        assert response is not None
        assert len(agent.memory) == 2  # Input + output

    @pytest.mark.asyncio
    async def test_inactive_agent(self):
        """Test inactive agent returns None."""
        agent = Agent(name="test_agent", role="assistant")
        agent.is_active = False
        
        message = Message(role="user", content="Hello", sender="user")
        response = await agent.process_message(message)
        
        assert response is None
```

### Testing LLM Providers

```python
import pytest
from unittest.mock import AsyncMock, Mock
from agentmind.llm.provider import LLMProvider, LLMResponse

class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    async def generate(self, messages, **kwargs):
        return LLMResponse(
            content="Mock response",
            model=self.model,
            usage={"prompt_tokens": 10, "completion_tokens": 20}
        )

    async def generate_stream(self, messages, **kwargs):
        for char in "Mock response":
            yield char

class TestLLMProvider:
    """Unit tests for LLM providers."""

    @pytest.mark.asyncio
    async def test_generate(self):
        """Test LLM generation."""
        llm = MockLLMProvider(model="test-model")
        messages = [{"role": "user", "content": "Hello"}]
        
        response = await llm.generate(messages)
        
        assert response.content == "Mock response"
        assert response.model == "test-model"
        assert response.usage["total_tokens"] == 30

    @pytest.mark.asyncio
    async def test_generate_stream(self):
        """Test streaming generation."""
        llm = MockLLMProvider(model="test-model")
        messages = [{"role": "user", "content": "Hello"}]
        
        chunks = []
        async for chunk in llm.generate_stream(messages):
            chunks.append(chunk)
        
        assert "".join(chunks) == "Mock response"
```

### Testing Cache

```python
import pytest
from agentmind.performance.cache import InMemoryCache, CacheManager

class TestCache:
    """Unit tests for caching."""

    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        """Test basic cache operations."""
        cache = InMemoryCache()
        
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache TTL expiration."""
        import asyncio
        cache = InMemoryCache()
        
        await cache.set("key1", "value1", ttl=1)
        assert await cache.get("key1") == "value1"
        
        await asyncio.sleep(1.1)
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_cache_manager_stats(self):
        """Test cache statistics."""
        manager = CacheManager()
        messages = [{"role": "user", "content": "Hello"}]
        
        # Miss
        await manager.get_response(messages)
        
        # Set
        await manager.set_response(messages, "Response")
        
        # Hit
        await manager.get_response(messages)
        
        stats = manager.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
```

## Integration Testing

### Testing Multi-Agent Collaboration

```python
import pytest
from agentmind.core.agent import Agent
from agentmind.core.mind import AgentMind
from agentmind.llm.provider import LLMProvider, LLMResponse

class TestCollaboration:
    """Integration tests for agent collaboration."""

    @pytest.mark.asyncio
    async def test_two_agent_collaboration(self):
        """Test collaboration between two agents."""
        # Setup
        llm = MockLLMProvider(model="test-model")
        mind = AgentMind(llm_provider=llm)
        
        agent1 = Agent(name="agent1", role="analyst", llm_provider=llm)
        agent2 = Agent(name="agent2", role="writer", llm_provider=llm)
        
        mind.add_agent(agent1)
        mind.add_agent(agent2)
        
        # Execute
        result = await mind.collaborate("Test task", max_rounds=2)
        
        # Verify
        assert result is not None
        assert len(agent1.memory) > 0
        assert len(agent2.memory) > 0

    @pytest.mark.asyncio
    async def test_collaboration_with_tools(self):
        """Test collaboration with tool usage."""
        from agentmind.tools import tool, ToolRegistry
        
        @tool
        def calculator(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b
        
        registry = ToolRegistry()
        registry.register(calculator)
        
        llm = MockLLMProvider(model="test-model")
        agent = Agent(
            name="calculator_agent",
            role="assistant",
            llm_provider=llm,
            tool_registry=registry
        )
        
        assert len(agent._available_tools) > 0
```

### Testing with Real LLM Providers

```python
import pytest
import os

@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key not available"
)
@pytest.mark.asyncio
async def test_with_real_llm():
    """Test with real LLM provider (requires API key)."""
    from agentmind.llm.litellm_provider import LiteLLMProvider
    
    llm = LiteLLMProvider(model="gpt-3.5-turbo")
    messages = [{"role": "user", "content": "Say hello"}]
    
    response = await llm.generate(messages)
    
    assert response.content
    assert len(response.content) > 0
```

## Property-Based Testing

### Using Hypothesis

```python
from hypothesis import given, strategies as st
import pytest

@given(
    name=st.text(min_size=1, max_size=50),
    role=st.text(min_size=1, max_size=50),
)
def test_agent_creation_properties(name, role):
    """Test agent creation with random inputs."""
    agent = Agent(name=name, role=role)
    assert agent.name == name
    assert agent.role == role

@given(st.lists(st.integers(), min_size=0, max_size=100))
@pytest.mark.asyncio
async def test_batch_processing_properties(values):
    """Test batch processing with random inputs."""
    from agentmind.performance.batch import BatchProcessor
    
    async def process(value: int) -> int:
        return value * 2
    
    processor = BatchProcessor(max_concurrent=5)
    tasks = [{"id": str(i), "value": v} for i, v in enumerate(values)]
    
    results = await processor.process_batch(tasks, process)
    
    assert len(results) == len(values)
    assert all(r.success for r in results)
```

### Stateful Testing

```python
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant

class CacheStateMachine(RuleBasedStateMachine):
    """Stateful testing for cache."""

    def __init__(self):
        super().__init__()
        self.cache = InMemoryCache(max_size=100)
        self.expected = {}

    @rule(key=st.text(min_size=1), value=st.text())
    async def set_value(self, key, value):
        """Set a value."""
        await self.cache.set(key, value)
        self.expected[key] = value

    @rule(key=st.text(min_size=1))
    async def get_value(self, key):
        """Get a value."""
        result = await self.cache.get(key)
        expected = self.expected.get(key)
        if expected is not None:
            assert result == expected

    @invariant()
    def cache_size_valid(self):
        """Cache size should be valid."""
        assert self.cache.size() <= 100
```

## Performance Testing

### Load Testing

```python
import pytest
import asyncio
from agentmind.performance.batch import BatchProcessor

@pytest.mark.asyncio
async def test_load_handling():
    """Test system under load."""
    async def process_task(task_id: int) -> int:
        await asyncio.sleep(0.01)  # Simulate work
        return task_id * 2
    
    processor = BatchProcessor(max_concurrent=50)
    
    # Create 1000 tasks
    tasks = [{"id": str(i), "task_id": i} for i in range(1000)]
    
    import time
    start = time.time()
    results = await processor.process_batch(tasks, process_task)
    duration = time.time() - start
    
    # Verify
    assert len(results) == 1000
    assert all(r.success for r in results)
    assert duration < 30  # Should complete in 30 seconds
    
    # Check throughput
    throughput = len(results) / duration
    assert throughput > 30  # At least 30 tasks/second
```

### Memory Testing

```python
import pytest
from agentmind.dev_tools import MemoryLeakDetector

@pytest.mark.asyncio
async def test_memory_growth():
    """Test memory doesn't grow unbounded."""
    from agentmind.performance.memory_optimizer import MemoryOptimizer
    
    detector = MemoryLeakDetector()
    optimizer = MemoryOptimizer(max_messages=50)
    
    agent = Agent(name="test", role="assistant", llm_provider=MockLLMProvider())
    
    detector.take_snapshot("start", [agent])
    
    # Process many messages
    for i in range(200):
        msg = Message(role="user", content=f"Message {i}", sender="user")
        await agent.process_message(msg)
        
        # Optimize periodically
        if i % 50 == 0:
            agent.memory = await optimizer.optimize(agent.memory)
    
    detector.take_snapshot("end", [agent])
    
    analysis = detector.analyze()
    
    # Memory should not grow excessively
    assert analysis["agents"]["test"]["memory_growth"] < 100
```

## Mocking & Fixtures

### Pytest Fixtures

```python
import pytest
from agentmind.core.agent import Agent
from agentmind.core.mind import AgentMind

@pytest.fixture
def mock_llm():
    """Fixture for mock LLM provider."""
    return MockLLMProvider(model="test-model")

@pytest.fixture
def test_agent(mock_llm):
    """Fixture for test agent."""
    return Agent(name="test_agent", role="assistant", llm_provider=mock_llm)

@pytest.fixture
def agent_mind(mock_llm):
    """Fixture for AgentMind."""
    return AgentMind(llm_provider=mock_llm)

@pytest.fixture
async def agent_with_memory(test_agent):
    """Fixture for agent with pre-populated memory."""
    for i in range(10):
        msg = Message(role="user", content=f"Message {i}", sender="user")
        await test_agent.process_message(msg)
    return test_agent

# Use fixtures in tests
def test_with_fixtures(test_agent):
    """Test using fixtures."""
    assert test_agent.name == "test_agent"

@pytest.mark.asyncio
async def test_with_memory_fixture(agent_with_memory):
    """Test with pre-populated memory."""
    assert len(agent_with_memory.memory) == 20  # 10 inputs + 10 outputs
```

### Mocking External Services

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mocked_llm():
    """Test with mocked LLM calls."""
    with patch('agentmind.llm.ollama_provider.OllamaProvider.generate') as mock_gen:
        mock_gen.return_value = LLMResponse(
            content="Mocked response",
            model="llama3.2",
            usage={}
        )
        
        from agentmind.llm.ollama_provider import OllamaProvider
        llm = OllamaProvider(model="llama3.2")
        
        response = await llm.generate([{"role": "user", "content": "Test"}])
        
        assert response.content == "Mocked response"
        assert mock_gen.called
```

## Test Coverage

### Measuring Coverage

```bash
# Run with coverage
pytest --cov=src/agentmind --cov-report=html

# View HTML report
open htmlcov/index.html

# Show missing lines
pytest --cov=src/agentmind --cov-report=term-missing
```

### Coverage Goals

- **Overall**: > 90%
- **Core modules**: > 95%
- **Critical paths**: 100%

### Excluding Code from Coverage

```python
def debug_only_function():  # pragma: no cover
    """This function is only for debugging."""
    pass
```

## Best Practices

### 1. Test Organization

```
tests/
├── unit/
│   ├── test_agent.py
│   ├── test_llm.py
│   └── test_cache.py
├── integration/
│   ├── test_collaboration.py
│   └── test_workflows.py
├── performance/
│   ├── test_load.py
│   └── test_memory.py
└── conftest.py  # Shared fixtures
```

### 2. Test Naming

```python
# Good: Descriptive test names
def test_agent_processes_message_successfully():
    pass

def test_agent_returns_none_when_inactive():
    pass

# Bad: Vague test names
def test_agent():
    pass

def test_1():
    pass
```

### 3. Arrange-Act-Assert Pattern

```python
def test_cache_hit():
    # Arrange
    cache = CacheManager()
    messages = [{"role": "user", "content": "Hello"}]
    await cache.set_response(messages, "Response")
    
    # Act
    result = await cache.get_response(messages)
    
    # Assert
    assert result == "Response"
```

### 4. Test Independence

```python
# Good: Each test is independent
def test_agent_creation():
    agent = Agent(name="test", role="assistant")
    assert agent.name == "test"

def test_agent_processing():
    agent = Agent(name="test", role="assistant")
    # ... test processing ...

# Bad: Tests depend on each other
agent = None  # Global state

def test_create_agent():
    global agent
    agent = Agent(name="test", role="assistant")

def test_use_agent():
    # Depends on test_create_agent running first
    assert agent.name == "test"
```

### 5. Use Parametrize for Multiple Cases

```python
@pytest.mark.parametrize("role,expected", [
    ("analyst", "analyst"),
    ("writer", "writer"),
    ("coordinator", "coordinator"),
])
def test_agent_roles(role, expected):
    """Test different agent roles."""
    agent = Agent(name="test", role=role)
    assert agent.role == expected
```

### 6. Test Error Cases

```python
def test_agent_invalid_name():
    """Test agent creation with invalid name."""
    with pytest.raises(ValueError, match="cannot be empty"):
        Agent(name="", role="assistant")

@pytest.mark.asyncio
async def test_llm_timeout():
    """Test LLM timeout handling."""
    with pytest.raises(asyncio.TimeoutError):
        await llm.generate(messages, timeout=0.001)
```

### 7. Clean Up Resources

```python
@pytest.fixture
async def redis_cache():
    """Fixture with cleanup."""
    cache = RedisCache(host="localhost")
    yield cache
    # Cleanup
    await cache.clear()
    await cache.close()
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    
    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-asyncio pytest-cov hypothesis
    
    - name: Run tests
      run: pytest --cov=src/agentmind --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Next Steps

- [Performance Guide](PERFORMANCE.md) - Optimization techniques
- [Debugging Guide](DEBUGGING.md) - Debugging tools
- [Contributing Guide](../CONTRIBUTING.md) - Contribution guidelines
