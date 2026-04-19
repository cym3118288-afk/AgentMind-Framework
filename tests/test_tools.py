"""Tests for tool system."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from agentmind.tools import (
    Tool,
    ToolResult,
    ToolRegistry,
    tool,
    get_global_registry,
    Calculator,
    CodeExecutor,
    FileIO,
)


class TestToolResult:
    """Tests for ToolResult model."""

    def test_successful_result(self):
        """Test creating a successful result."""
        result = ToolResult(success=True, output="Hello", metadata={"key": "value"})
        assert result.success is True
        assert result.output == "Hello"
        assert result.error is None
        assert result.metadata["key"] == "value"

    def test_failed_result(self):
        """Test creating a failed result."""
        result = ToolResult(success=False, error="Something went wrong")
        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.output is None


class TestCalculator:
    """Tests for Calculator tool."""

    @pytest.mark.asyncio
    async def test_basic_arithmetic(self):
        """Test basic arithmetic operations."""
        calc = Calculator()

        result = await calc.execute(expression="2 + 3")
        assert result.success is True
        assert result.output == "5"

        result = await calc.execute(expression="10 - 4")
        assert result.success is True
        assert result.output == "6"

        result = await calc.execute(expression="5 * 6")
        assert result.success is True
        assert result.output == "30"

        result = await calc.execute(expression="20 / 4")
        assert result.success is True
        assert result.output == "5.0"

    @pytest.mark.asyncio
    async def test_power_operation(self):
        """Test power operation."""
        calc = Calculator()

        result = await calc.execute(expression="2 ** 10")
        assert result.success is True
        assert result.output == "1024"

    @pytest.mark.asyncio
    async def test_complex_expression(self):
        """Test complex expression."""
        calc = Calculator()

        result = await calc.execute(expression="(10 + 5) * 2 - 8")
        assert result.success is True
        assert result.output == "22"

    @pytest.mark.asyncio
    async def test_invalid_expression(self):
        """Test handling invalid expression."""
        calc = Calculator()

        result = await calc.execute(expression="invalid")
        assert result.success is False
        assert "error" in result.error.lower()

    @pytest.mark.asyncio
    async def test_unsafe_expression(self):
        """Test that unsafe operations are rejected."""
        calc = Calculator()

        # Should not allow function calls
        result = await calc.execute(expression="__import__('os').system('ls')")
        assert result.success is False


class TestCodeExecutor:
    """Tests for CodeExecutor tool."""

    @pytest.mark.asyncio
    async def test_simple_execution(self):
        """Test executing simple code."""
        executor = CodeExecutor(timeout=5)

        result = await executor.execute(code="print('Hello, World!')")
        assert result.success is True
        assert "Hello, World!" in result.output

    @pytest.mark.asyncio
    async def test_calculation(self):
        """Test executing calculation."""
        executor = CodeExecutor(timeout=5)

        result = await executor.execute(code="print(2 ** 10)")
        assert result.success is True
        assert "1024" in result.output

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test handling code errors."""
        executor = CodeExecutor(timeout=5)

        result = await executor.execute(code="print(undefined_variable)")
        assert result.success is False
        assert "NameError" in result.error or "not defined" in result.error

    @pytest.mark.asyncio
    async def test_timeout(self):
        """Test execution timeout."""
        executor = CodeExecutor(timeout=1)

        # This should timeout
        result = await executor.execute(
            code="import time; time.sleep(5); print('done')",
            timeout=1
        )
        assert result.success is False
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_multiline_code(self):
        """Test executing multiline code."""
        executor = CodeExecutor(timeout=5)

        code = """
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
print(f"Sum: {total}")
"""
        result = await executor.execute(code=code)
        assert result.success is True
        assert "Sum: 15" in result.output


class TestFileIO:
    """Tests for FileIO tool."""

    @pytest.mark.asyncio
    async def test_write_and_read(self):
        """Test writing and reading files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)

            # Write file
            write_result = await file_io.execute(
                operation="write",
                path="test.txt",
                content="Hello, World!"
            )
            assert write_result.success is True

            # Read file
            read_result = await file_io.execute(
                operation="read",
                path="test.txt"
            )
            assert read_result.success is True
            assert read_result.output == "Hello, World!"

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self):
        """Test reading nonexistent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)

            result = await file_io.execute(
                operation="read",
                path="nonexistent.txt"
            )
            assert result.success is False
            assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_path_traversal_protection(self):
        """Test protection against path traversal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)

            # Try to access parent directory
            result = await file_io.execute(
                operation="read",
                path="../../../etc/passwd"
            )
            assert result.success is False
            assert "denied" in result.error.lower()

    @pytest.mark.asyncio
    async def test_write_without_content(self):
        """Test write operation without content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)

            result = await file_io.execute(
                operation="write",
                path="test.txt"
            )
            assert result.success is False
            assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Test invalid operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)

            result = await file_io.execute(
                operation="delete",
                path="test.txt"
            )
            assert result.success is False
            assert "unknown operation" in result.error.lower()


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_and_get(self):
        """Test registering and retrieving tools."""
        registry = ToolRegistry()
        calc = Calculator()

        registry.register(calc)
        retrieved = registry.get("calculator")

        assert retrieved is not None
        assert retrieved.name == "calculator"

    def test_list_tools(self):
        """Test listing registered tools."""
        registry = ToolRegistry()
        calc = Calculator()
        executor = CodeExecutor()

        registry.register(calc)
        registry.register(executor)

        tools = registry.list_tools()
        assert "calculator" in tools
        assert "code_executor" in tools

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test executing tool through registry."""
        registry = ToolRegistry()
        calc = Calculator()
        registry.register(calc)

        result = await registry.execute("calculator", expression="5 + 3")
        assert result.success is True
        assert result.output == "8"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing nonexistent tool."""
        registry = ToolRegistry()

        result = await registry.execute("nonexistent", param="value")
        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_parallel(self):
        """Test executing multiple tools in parallel."""
        registry = ToolRegistry()
        calc = Calculator()
        registry.register(calc)

        tool_calls = [
            {"name": "calculator", "parameters": {"expression": "2 + 2"}},
            {"name": "calculator", "parameters": {"expression": "3 * 3"}},
            {"name": "calculator", "parameters": {"expression": "10 - 5"}},
        ]

        results = await registry.execute_parallel(tool_calls)
        assert len(results) == 3
        assert all(r.success for r in results)
        assert results[0].output == "4"
        assert results[1].output == "9"
        assert results[2].output == "5"

    def test_get_definitions(self):
        """Test getting tool definitions."""
        registry = ToolRegistry()
        calc = Calculator()
        registry.register(calc)

        definitions = registry.get_definitions()
        assert len(definitions) == 1
        assert definitions[0].name == "calculator"
        assert "expression" in str(definitions[0].parameters)


class TestToolDecorator:
    """Tests for @tool decorator."""

    @pytest.mark.asyncio
    async def test_simple_tool(self):
        """Test creating a simple tool with decorator."""

        @tool(name="greeter", description="Greet someone")
        async def greet(name: str) -> ToolResult:
            return ToolResult(success=True, output=f"Hello, {name}!")

        assert greet.name == "greeter"
        assert greet.description == "Greet someone"

        result = await greet.execute(name="Alice")
        assert result.success is True
        assert result.output == "Hello, Alice!"

    @pytest.mark.asyncio
    async def test_tool_auto_wrap(self):
        """Test that decorator auto-wraps return values."""

        @tool(name="adder")
        async def add(a: int, b: int):
            return a + b

        result = await add.execute(a=5, b=3)
        assert result.success is True
        assert result.output == 8

    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """Test that decorator handles errors."""

        @tool(name="divider")
        async def divide(a: int, b: int):
            return a / b

        result = await divide.execute(a=10, b=0)
        assert result.success is False
        assert "division" in result.error.lower()

    def test_tool_definition(self):
        """Test getting tool definition."""

        @tool(name="multiplier", description="Multiply two numbers")
        async def multiply(x: int, y: int):
            return x * y

        definition = multiply.get_definition()
        assert definition.name == "multiplier"
        assert definition.description == "Multiply two numbers"
        assert "x" in definition.parameters["properties"]
        assert "y" in definition.parameters["properties"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
