"""
Tutorial 03: Creating Custom Tools

This tutorial covers creating and using custom tools:
- Tool decorator and registration
- Parameter validation
- Error handling
- Tool discovery and usage

Estimated time: 20 minutes
Difficulty: Intermediate
"""

import asyncio
from typing import Dict, Any
from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool, ToolRegistry


# Example 1: Simple tool with decorator
class CalculatorTool(Tool):
    """A simple calculator tool"""

    def __init__(self):
        super().__init__(
            name="calculator",
            description="Performs basic arithmetic operations",
            parameters={
                "operation": {
                    "type": "string",
                    "description": "Operation to perform: add, subtract, multiply, divide",
                    "enum": ["add", "subtract", "multiply", "divide"],
                },
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
        )

    async def execute(self, operation: str, a: float, b: float) -> str:
        """Execute the calculation"""
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return "Error: Division by zero"
                result = a / b
            else:
                return f"Error: Unknown operation {operation}"

            return f"Result: {result}"
        except Exception as e:
            return f"Error: {str(e)}"


# Example 2: Tool with external API simulation
class WeatherTool(Tool):
    """Simulates a weather API tool"""

    def __init__(self):
        super().__init__(
            name="get_weather",
            description="Get current weather for a location",
            parameters={
                "location": {"type": "string", "description": "City name or location"},
                "units": {
                    "type": "string",
                    "description": "Temperature units: celsius or fahrenheit",
                    "enum": ["celsius", "fahrenheit"],
                    "default": "celsius",
                },
            },
        )

    async def execute(self, location: str, units: str = "celsius") -> str:
        """Simulate weather API call"""
        # In real implementation, this would call an actual weather API
        weather_data = {
            "new york": {"temp_c": 22, "temp_": 72, "condition": "Sunny"},
            "london": {"temp_c": 15, "temp_": 59, "condition": "Cloudy"},
            "tokyo": {"temp_c": 25, "temp_": 77, "condition": "Clear"},
        }

        location_lower = location.lower()
        if location_lower not in weather_data:
            return f"Weather data not available for {location}"

        data = weather_data[location_lower]
        temp = data["temp_c"] if units == "celsius" else data["temp_"]
        unit_symbol = "°C" if units == "celsius" else "°F"

        return f"Weather in {location}: {data['condition']}, {temp}{unit_symbol}"


# Example 3: Tool with validation
class DatabaseTool(Tool):
    """Simulates database operations"""

    def __init__(self):
        super().__init__(
            name="query_database",
            description="Query a database table",
            parameters={
                "table": {"type": "string", "description": "Table name to query"},
                "filters": {"type": "object", "description": "Filter conditions", "default": {}},
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 10,
                },
            },
        )
        # Simulated database
        self.db = {
            "users": [
                {"id": 1, "name": "Alice", "role": "admin"},
                {"id": 2, "name": "Bob", "role": "user"},
                {"id": 3, "name": "Charlie", "role": "user"},
            ],
            "products": [
                {"id": 1, "name": "Laptop", "price": 999},
                {"id": 2, "name": "Mouse", "price": 29},
                {"id": 3, "name": "Keyboard", "price": 79},
            ],
        }

    async def execute(self, table: str, filters: Dict[str, Any] = None, limit: int = 10) -> str:
        """Execute database query"""
        if table not in self.db:
            return f"Error: Table '{table}' not found"

        results = self.db[table]

        # Apply filters
        if filters:
            filtered = []
            for item in results:
                match = all(item.get(k) == v for k, v in filters.items())
                if match:
                    filtered.append(item)
            results = filtered

        # Apply limit
        results = results[:limit]

        return f"Found {len(results)} results: {results}"


async def example_1_basic_tool():
    """Example 1: Using a basic tool"""
    print("\n=== Example 1: Basic Tool Usage ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create tool registry and add tool
    registry = ToolRegistry()
    calculator = CalculatorTool()
    registry.register_tool(calculator)

    # Create agent with tools
    _agent = Agent(name="math_assistant", role="assistant", llm_provider=llm, tool_registry=registry)

    # Test the tool directly
    result = await calculator.execute(operation="add", a=15, b=27)
    print(f"Direct tool call: 15 + 27 = {result}\n")

    print(f"Agent has access to {len(registry.list_tools())} tool(s)")


async def example_2_multiple_tools():
    """Example 2: Agent with multiple tools"""
    print("\n=== Example 2: Multiple Tools ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create registry with multiple tools
    registry = ToolRegistry()
    registry.register_tool(CalculatorTool())
    registry.register_tool(WeatherTool())
    registry.register_tool(DatabaseTool())

    # Create agent
    _agent = Agent(name="assistant", role="assistant", llm_provider=llm, tool_registry=registry)

    print(f"Agent has access to {len(registry.list_tools())} tools:")
    for tool_name in registry.list_tools():
        tool = registry.get_tool(tool_name)
        print(f"  - {tool_name}: {tool.description}")


async def example_3_tool_in_collaboration():
    """Example 3: Tools in multi - agent collaboration"""
    print("\n=== Example 3: Tools in Collaboration ===\n")

    llm = OllamaProvider(model="llama3.2:3b")

    # Create shared tool registry
    registry = ToolRegistry()
    registry.register_tool(CalculatorTool())
    registry.register_tool(WeatherTool())

    # Create agents with tools
    analyst = Agent(name="analyst", role="analyst", llm_provider=llm, tool_registry=registry)

    planner = Agent(name="planner", role="planner", llm_provider=llm, tool_registry=registry)

    # Create orchestrator
    mind = AgentMind(strategy="round_robin")
    mind.add_agent(analyst)
    mind.add_agent(planner)

    print("Agents can use tools during collaboration")
    print(f"Available tools: {', '.join(registry.list_tools())}\n")


async def example_4_error_handling():
    """Example 4: Tool error handling"""
    print("\n=== Example 4: Error Handling ===\n")

    calculator = CalculatorTool()

    # Test error cases
    print("Testing error handling:")

    # Division by zero
    result1 = await calculator.execute(operation="divide", a=10, b=0)
    print(f"10 / 0 = {result1}")

    # Invalid operation
    result2 = await calculator.execute(operation="power", a=2, b=3)
    print(f"Invalid operation = {result2}\n")


async def example_5_custom_tool_pattern():
    """Example 5: Advanced tool pattern"""
    print("\n=== Example 5: Advanced Tool Pattern ===\n")

    class FileSystemTool(Tool):
        """Tool with state and configuration"""

        def __init__(self, base_path: str = "/tmp"):
            self.base_path = base_path
            super().__init__(
                name="file_system",
                description="Simulated file system operations",
                parameters={
                    "operation": {"type": "string", "enum": ["list", "read", "write"]},
                    "path": {"type": "string", "description": "File path"},
                    "content": {
                        "type": "string",
                        "description": "Content for write operation",
                        "default": "",
                    },
                },
            )
            self.files = {}  # Simulated file system

        async def execute(self, operation: str, path: str, content: str = "") -> str:
            """Execute file system operation"""
            full_path = f"{self.base_path}/{path}"

            if operation == "list":
                return f"Files: {list(self.files.keys())}"
            elif operation == "read":
                return self.files.get(full_path, "File not found")
            elif operation == "write":
                self.files[full_path] = content
                return f"Written to {full_path}"
            else:
                return f"Unknown operation: {operation}"

    # Create and test the tool
    fs_tool = FileSystemTool(base_path="/workspace")

    await fs_tool.execute(operation="write", path="test.txt", content="Hello World")
    result = await fs_tool.execute(operation="read", path="test.txt")
    print(f"File content: {result}")

    files = await fs_tool.execute(operation="list", path="")
    print(f"{files}\n")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("AgentMind Tutorial 03: Creating Custom Tools")
    print("=" * 60)

    await example_1_basic_tool()
    await example_2_multiple_tools()
    await example_3_tool_in_collaboration()
    await example_4_error_handling()
    await example_5_custom_tool_pattern()

    print("\n" + "=" * 60)
    print("Tutorial Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. Tools extend agent capabilities with custom functions")
    print("2. Tools have names, descriptions, and parameter schemas")
    print("3. ToolRegistry manages tool registration and discovery")
    print("4. Tools can maintain state and handle errors")
    print("5. Multiple agents can share the same tool registry")
    print("\nNext: Tutorial 04 - Multi - Agent Orchestration")


if __name__ == "__main__":
    asyncio.run(main())
