"""Custom Tools Example

Demonstrates how to create and use custom tools with AgentMind agents.
Tools allow agents to interact with external systems, APIs, and data sources.

Difficulty: INTERMEDIATE
Prerequisites: Understanding of basic agent collaboration
Estimated time: 20 minutes

What you'll learn:
- Creating simple tools with the @tool decorator
- Creating tools that call external APIs
- Registering tools with agents
- Using tools in agent collaboration
- Tool parameter validation and error handling

Expected Output:
- Agents use calculator tool for mathematical operations
- Weather tool provides city weather information (mock data)
- Database tool performs data queries
- Time tool provides current timestamp
- Demonstrates tool integration in multi-agent workflows
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List

from agentmind import Agent, AgentMind
from agentmind.core.types import CollaborationStrategy
from agentmind.llm import OllamaProvider
from agentmind.tools import tool


# Example 1: Simple calculation tool
@tool(name="calculator", description="Perform basic math calculations")
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: Math expression to evaluate (e.g., "2 + 2", "10 * 5")

    Returns:
        Result of the calculation
    """
    try:
        # Safe evaluation of simple math expressions
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


# Example 2: Data lookup tool
@tool(name="get_weather", description="Get current weather for a city")
def get_weather(city: str) -> str:
    """Get weather information for a city.

    Args:
        city: Name of the city

    Returns:
        Weather information (mock data for demo)
    """
    # In production, this would call a real weather API
    mock_weather = {
        "new york": {"temp": 72, "condition": "Sunny", "humidity": 45},
        "london": {"temp": 58, "condition": "Cloudy", "humidity": 70},
        "tokyo": {"temp": 68, "condition": "Rainy", "humidity": 80},
        "paris": {"temp": 65, "condition": "Partly Cloudy", "humidity": 55},
    }

    city_lower = city.lower()
    if city_lower in mock_weather:
        data = mock_weather[city_lower]
        return json.dumps(data, indent=2)
    else:
        return f"Weather data not available for {city}"


# Example 3: Async tool for API calls
@tool(name="search_docs", description="Search documentation")
async def search_docs(query: str) -> str:
    """Search documentation for relevant information.

    Args:
        query: Search query

    Returns:
        Search results (mock data for demo)
    """
    # Simulate async API call
    await asyncio.sleep(0.5)

    # Mock search results
    results = {
        "installation": "Install with: pip install -e .",
        "quickstart": "See QUICKSTART.md for getting started guide",
        "examples": "Check examples/ directory for sample code",
        "api": "API documentation available in API.md",
    }

    for key, value in results.items():
        if key in query.lower():
            return value

    return "No relevant documentation found"


# Example 4: Tool with complex return type
@tool(name="analyze_text", description="Analyze text statistics")
def analyze_text(text: str) -> str:
    """Analyze text and return statistics.

    Args:
        text: Text to analyze

    Returns:
        JSON string with text statistics
    """
    words = text.split()
    stats = {
        "character_count": len(text),
        "word_count": len(words),
        "sentence_count": text.count(".") + text.count("!") + text.count("?"),
        "avg_word_length": sum(len(word) for word in words) / len(words) if words else 0,
        "timestamp": datetime.now().isoformat(),
    }
    return json.dumps(stats, indent=2)


async def demo_basic_tools():
    """Demonstrate basic tool usage."""
    print("\n" + "=" * 60)
    print("DEMO 1: Basic Tool Usage")
    print("=" * 60 + "\n")

    # Create agent with tools
    agent = Agent(name="Assistant", role="assistant")

    # Register tools
    agent.tool_registry.register(calculator)
    agent.tool_registry.register(get_weather)
    agent.tool_registry.register(analyze_text)

    # Test calculator
    print("Testing calculator tool:")
    result = calculator("15 * 8 + 12")
    print(f"  {result}\n")

    # Test weather lookup
    print("Testing weather tool:")
    result = get_weather("London")
    print(f"  {result}\n")

    # Test text analysis
    print("Testing text analysis tool:")
    result = analyze_text("AgentMind is a lightweight multi-agent framework.")
    print(f"  {result}\n")


async def demo_agent_with_tools():
    """Demonstrate agents using tools in collaboration."""
    print("\n" + "=" * 60)
    print("DEMO 2: Agents Using Tools")
    print("=" * 60 + "\n")

    # Create LLM provider
    llm = OllamaProvider(model="llama3.2")

    # Create AgentMind
    mind = AgentMind(llm_provider=llm)

    # Create agent with tools
    analyst = Agent(name="DataAnalyst", role="analyst", llm_provider=llm)
    analyst.config.system_prompt = """You are a data analyst with access to tools.
Use the calculator tool for computations.
Use the analyze_text tool to analyze text data.
Provide clear, data-driven insights."""

    # Register tools with agent
    analyst.tool_registry.register(calculator)
    analyst.tool_registry.register(analyze_text)

    # Add to mind
    mind.add_agent(analyst)

    # Collaborate with tool usage
    task = """Analyze this text and calculate statistics:

    "The quick brown fox jumps over the lazy dog. This sentence contains every letter."

    Then calculate: What is 26 * 2 (letters * 2)?"""

    print("Task:", task)
    print("\nAgent working...\n")

    result = await mind.collaborate(task, max_rounds=2)

    print("Result:")
    print(result.final_output)


async def demo_multi_agent_tools():
    """Demonstrate multiple agents with different tools."""
    print("\n" + "=" * 60)
    print("DEMO 3: Multi-Agent Tool Collaboration")
    print("=" * 60 + "\n")

    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(strategy=CollaborationStrategy.ROUND_ROBIN, llm_provider=llm)

    # Weather agent
    weather_agent = Agent(name="WeatherExpert", role="analyst", llm_provider=llm)
    weather_agent.config.system_prompt = """You are a weather expert.
Use the get_weather tool to provide weather information.
Give practical advice based on weather conditions."""
    weather_agent.tool_registry.register(get_weather)

    # Calculator agent
    calc_agent = Agent(name="Calculator", role="analyst", llm_provider=llm)
    calc_agent.config.system_prompt = """You are a math expert.
Use the calculator tool for all computations.
Show your work clearly."""
    calc_agent.tool_registry.register(calculator)

    # Coordinator agent
    coordinator = Agent(name="Coordinator", role="coordinator", llm_provider=llm)
    coordinator.config.system_prompt = """You are a coordinator.
Synthesize information from other agents.
Provide clear, actionable recommendations."""

    mind.add_agent(weather_agent)
    mind.add_agent(calc_agent)
    mind.add_agent(coordinator)

    task = """Plan a trip to London:
1. Check the weather
2. Calculate budget: (hotel $150/night * 3 nights) + (meals $50/day * 3 days)
3. Provide recommendations"""

    print("Task:", task)
    print("\nAgents collaborating...\n")

    result = await mind.collaborate(task, max_rounds=2)

    print("Final Recommendation:")
    print(result.final_output)


async def demo_custom_tool_class():
    """Demonstrate creating a custom tool class."""
    print("\n" + "=" * 60)
    print("DEMO 4: Custom Tool Class")
    print("=" * 60 + "\n")

    class DatabaseTool:
        """Custom tool class for database operations."""

        def __init__(self):
            # Mock database
            self.db = {
                "users": [
                    {"id": 1, "name": "Alice", "role": "admin"},
                    {"id": 2, "name": "Bob", "role": "user"},
                    {"id": 3, "name": "Charlie", "role": "user"},
                ],
                "products": [
                    {"id": 1, "name": "Widget", "price": 29.99},
                    {"id": 2, "name": "Gadget", "price": 49.99},
                ],
            }

        @tool(name="query_db", description="Query the database")
        def query(self, table: str, filter_key: str = None, filter_value: str = None) -> str:
            """Query database table.

            Args:
                table: Table name (users, products)
                filter_key: Optional filter key
                filter_value: Optional filter value

            Returns:
                Query results as JSON
            """
            if table not in self.db:
                return f"Table '{table}' not found"

            results = self.db[table]

            if filter_key and filter_value:
                results = [r for r in results if str(r.get(filter_key)) == filter_value]

            return json.dumps(results, indent=2)

    # Create and use custom tool
    db_tool = DatabaseTool()

    print("Querying all users:")
    result = db_tool.query("users")
    print(result)

    print("\nQuerying admin users:")
    result = db_tool.query("users", "role", "admin")
    print(result)


async def main():
    """Run all demos."""
    await demo_basic_tools()
    await demo_agent_with_tools()
    await demo_multi_agent_tools()
    await demo_custom_tool_class()

    print("\n" + "=" * 60)
    print("All demos complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
