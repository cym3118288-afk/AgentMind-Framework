"""
Tutorial 05: Plugin Development

This tutorial covers the AgentMind plugin system:
- Creating custom plugins
- Plugin discovery and loading
- LLM provider plugins
- Memory backend plugins
- Tool registry plugins
- Observer plugins

Estimated time: 30 minutes
Difficulty: Advanced
"""

import asyncio
from typing import Any, Dict, List, Optional
# from agentmind import Agent  # noqa: F401
from agentmind.llm import LLMProvider, LLMResponse, LLMMessage
from agentmind.tools import Tool, ToolRegistry


# Example 1: Custom LLM Provider Plugin
class CustomLLMProvider(LLMProvider):
    """Example custom LLM provider plugin"""

    def __init__(self, model: str = "custom - model", **kwargs):
        self.model = model
        self.config = kwargs

    async def generate(
        self, messages: List[LLMMessage], temperature: float = 0.7, max_tokens: int = 1000, **kwargs
    ) -> LLMResponse:
        """Generate a response (mock implementation)"""
        # In a real plugin, this would call your custom LLM API
        last_message = messages[-1].content if messages else ""

        # Mock response
        response_text = f"[Custom LLM Response to: {last_message[:50]}...]"

        return LLMResponse(
            content=response_text,
            model=self.model,
            usage={
                "prompt_tokens": len(last_message.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(last_message.split()) + len(response_text.split()),
            },
            metadata={"provider": "custom", "config": self.config},
        )

    async def generate_stream(self, messages: List[LLMMessage], **kwargs):
        """Stream generation (mock implementation)"""
        response = await self.generate(messages, **kwargs)
        # Simulate streaming by yielding chunks
        words = response.content.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.1)


# Example 2: Custom Memory Backend Plugin
class CustomMemoryBackend:
    """Example custom memory backend plugin"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.storage: Dict[str, List[Dict[str, Any]]] = {}

    async def store(self, agent_id: str, message: Dict[str, Any]) -> None:
        """Store a message in memory"""
        if agent_id not in self.storage:
            self.storage[agent_id] = []

        self.storage[agent_id].append(message)

        # Enforce max size
        if len(self.storage[agent_id]) > self.max_size:
            self.storage[agent_id] = self.storage[agent_id][-self.max_size :]

    async def retrieve(self, agent_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve messages from memory"""
        messages = self.storage.get(agent_id, [])
        if limit:
            return messages[-limit:]
        return messages

    async def clear(self, agent_id: str) -> None:
        """Clear memory for an agent"""
        if agent_id in self.storage:
            self.storage[agent_id] = []

    async def search(self, agent_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memory (simple keyword search)"""
        messages = self.storage.get(agent_id, [])
        results = [msg for msg in messages if query.lower() in str(msg.get("content", "")).lower()]
        return results[:limit]


# Example 3: Custom Tool Plugin
class WebScraperTool(Tool):
    """Example web scraper tool plugin"""

    def __init__(self):
        super().__init__(
            name="web_scraper",
            description="Scrape content from web pages",
            parameters={
                "url": {"type": "string", "description": "URL to scrape"},
                "selector": {
                    "type": "string",
                    "description": "CSS selector for content",
                    "default": "body",
                },
            },
        )

    async def execute(self, url: str, selector: str = "body") -> str:
        """Execute web scraping (mock implementation)"""
        # In a real plugin, this would use requests / beautifulsoup / playwright
        return f"[Scraped content from {url} using selector '{selector}']"


# Example 4: Custom Observer Plugin
class MetricsObserver:
    """Example metrics observer plugin"""

    def __init__(self):
        self.metrics = {
            "messages_processed": 0,
            "agents_active": 0,
            "collaborations_started": 0,
            "errors": 0,
        }

    async def on_message_processed(self, agent_name: str, message: Any) -> None:
        """Called when an agent processes a message"""
        self.metrics["messages_processed"] += 1
        print(f"[Metrics] Message processed by {agent_name}")

    async def on_agent_activated(self, agent_name: str) -> None:
        """Called when an agent is activated"""
        self.metrics["agents_active"] += 1
        print(f"[Metrics] Agent activated: {agent_name}")

    async def on_collaboration_started(self, task: str) -> None:
        """Called when collaboration starts"""
        self.metrics["collaborations_started"] += 1
        print(f"[Metrics] Collaboration started: {task[:50]}...")

    async def on_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Called when an error occurs"""
        self.metrics["errors"] += 1
        print(f"[Metrics] Error: {str(error)}")

    def get_metrics(self) -> Dict[str, int]:
        """Get current metrics"""
        return self.metrics.copy()


# Example 5: Plugin Registry
class PluginRegistry:
    """Registry for managing plugins"""

    def __init__(self):
        self.llm_providers: Dict[str, type] = {}
        self.memory_backends: Dict[str, type] = {}
        self.tools: Dict[str, type] = {}
        self.observers: Dict[str, type] = {}

    def register_llm_provider(self, name: str, provider_class: type) -> None:
        """Register an LLM provider plugin"""
        self.llm_providers[name] = provider_class
        print(f"Registered LLM provider: {name}")

    def register_memory_backend(self, name: str, backend_class: type) -> None:
        """Register a memory backend plugin"""
        self.memory_backends[name] = backend_class
        print(f"Registered memory backend: {name}")

    def register_tool(self, name: str, tool_class: type) -> None:
        """Register a tool plugin"""
        self.tools[name] = tool_class
        print(f"Registered tool: {name}")

    def register_observer(self, name: str, observer_class: type) -> None:
        """Register an observer plugin"""
        self.observers[name] = observer_class
        print(f"Registered observer: {name}")

    def get_llm_provider(self, name: str, **kwargs) -> Optional[LLMProvider]:
        """Get an LLM provider instance"""
        if name in self.llm_providers:
            return self.llm_providers[name](**kwargs)
        return None

    def get_memory_backend(self, name: str, **kwargs) -> Optional[Any]:
        """Get a memory backend instance"""
        if name in self.memory_backends:
            return self.memory_backends[name](**kwargs)
        return None

    def list_plugins(self) -> Dict[str, List[str]]:
        """List all registered plugins"""
        return {
            "llm_providers": list(self.llm_providers.keys()),
            "memory_backends": list(self.memory_backends.keys()),
            "tools": list(self.tools.keys()),
            "observers": list(self.observers.keys()),
        }


async def example_1_custom_llm_provider():
    """Example 1: Using a custom LLM provider"""
    print("\n=== Example 1: Custom LLM Provider ===\n")

    # Create custom provider
    custom_llm = CustomLLMProvider(model="my - custom - model", api_key="test")

    # Create agent with custom provider
    # _agent = Agent(name="assistant", role="assistant", llm_provider=custom_llm)

    print(f"Agent using custom LLM provider: {custom_llm.model}")
    print(f"Provider config: {custom_llm.config}\n")


async def example_2_custom_memory_backend():
    """Example 2: Using a custom memory backend"""
    print("\n=== Example 2: Custom Memory Backend ===\n")

    # Create custom memory backend
    memory = CustomMemoryBackend(max_size=50)

    # Store some messages
    await memory.store("agent1", {"content": "Hello", "role": "user"})
    await memory.store("agent1", {"content": "Hi there!", "role": "assistant"})
    await memory.store("agent1", {"content": "How are you?", "role": "user"})

    # Retrieve messages
    messages = await memory.retrieve("agent1")
    print(f"Stored {len(messages)} messages")

    # Search memory
    results = await memory.search("agent1", "hello")
    print(f"Search results: {len(results)} matches\n")


async def example_3_custom_tool_plugin():
    """Example 3: Using a custom tool plugin"""
    print("\n=== Example 3: Custom Tool Plugin ===\n")

    # Create tool registry
    registry = ToolRegistry()

    # Register custom tool
    scraper = WebScraperTool()
    registry.register_tool(scraper)

    # Test the tool
    result = await scraper.execute(url="https://example.com", selector=".content")
    print(f"Tool result: {result}\n")


async def example_4_observer_plugin():
    """Example 4: Using an observer plugin"""
    print("\n=== Example 4: Observer Plugin ===\n")

    # Create observer
    observer = MetricsObserver()

    # Simulate events
    await observer.on_collaboration_started("Research quantum computing")
    await observer.on_agent_activated("researcher")
    await observer.on_message_processed("researcher", {"content": "test"})

    # Get metrics
    metrics = observer.get_metrics()
    print(f"\nMetrics: {metrics}\n")


async def example_5_plugin_registry():
    """Example 5: Using the plugin registry"""
    print("\n=== Example 5: Plugin Registry ===\n")

    # Create registry
    registry = PluginRegistry()

    # Register plugins
    registry.register_llm_provider("custom", CustomLLMProvider)
    registry.register_memory_backend("custom", CustomMemoryBackend)
    registry.register_tool("web_scraper", WebScraperTool)
    registry.register_observer("metrics", MetricsObserver)

    # List all plugins
    print("\nRegistered plugins:")
    plugins = registry.list_plugins()
    for category, names in plugins.items():
        print(f"  {category}: {', '.join(names)}")

    # Get plugin instance
    llm = registry.get_llm_provider("custom", model="test - model")
    print(f"\nCreated LLM provider: {llm.model}\n")


async def example_6_plugin_composition():
    """Example 6: Composing multiple plugins"""
    print("\n=== Example 6: Plugin Composition ===\n")

    # Create components
    llm = CustomLLMProvider(model="composed - model")
    memory = CustomMemoryBackend(max_size=100)
    MetricsObserver()

    print("Created plugin composition:")
    print(f"  - LLM Provider: {llm.model}")
    print(f"  - Memory Backend: max_size={memory.max_size}")
    print("  - Observer: MetricsObserver")
    print("\nPlugins can work together in an agent system\n")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("AgentMind Tutorial 05: Plugin Development")
    print("=" * 60)

    await example_1_custom_llm_provider()
    await example_2_custom_memory_backend()
    await example_3_custom_tool_plugin()
    await example_4_observer_plugin()
    await example_5_plugin_registry()
    await example_6_plugin_composition()

    print("\n" + "=" * 60)
    print("Tutorial Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. Plugins extend AgentMind with custom functionality")
    print("2. LLM provider plugins enable custom model backends")
    print("3. Memory backend plugins customize storage")
    print("4. Tool plugins add new agent capabilities")
    print("5. Observer plugins enable monitoring and metrics")
    print("6. Plugin registry manages plugin lifecycle")
    print("\nNext: Tutorial 06 - Production Deployment")


if __name__ == "__main__":
    asyncio.run(main())
