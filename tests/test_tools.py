"""Tests for tool system."""

import asyncio
import tempfile
import time
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
        result = await executor.execute(code="import time; time.sleep(5); print('done')", timeout=1)
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
                operation="write", path="test.txt", content="Hello, World!"
            )
            assert write_result.success is True

            # Read file
            read_result = await file_io.execute(operation="read", path="test.txt")
            assert read_result.success is True
            assert read_result.output == "Hello, World!"

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self):
        """Test reading nonexistent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)

            result = await file_io.execute(operation="read", path="nonexistent.txt")
            assert result.success is False
            assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_path_traversal_protection(self):
        """Test protection against path traversal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)

            # Try to access parent directory
            result = await file_io.execute(operation="read", path="../../../etc/passwd")
            assert result.success is False
            assert "denied" in result.error.lower()

    @pytest.mark.asyncio
    async def test_write_without_content(self):
        """Test write operation without content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)

            result = await file_io.execute(operation="write", path="test.txt")
            assert result.success is False
            assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Test invalid operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)

            result = await file_io.execute(operation="delete", path="test.txt")
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


class TestCalculatorAdvanced:
    """Advanced tests for Calculator tool."""

    @pytest.mark.asyncio
    async def test_division_by_zero(self):
        """Test division by zero handling."""
        calc = Calculator()
        result = await calc.execute(expression="10 / 0")
        assert result.success is False
        assert "division" in result.error.lower()

    @pytest.mark.asyncio
    async def test_nested_expressions(self):
        """Test deeply nested expressions."""
        calc = Calculator()
        result = await calc.execute(expression="((2 + 3) * (4 + 5)) / 3")
        assert result.success is True
        assert float(result.output) == 15.0

    @pytest.mark.asyncio
    async def test_negative_numbers(self):
        """Test negative number handling."""
        calc = Calculator()
        result = await calc.execute(expression="-5 + 10")
        assert result.success is True
        assert result.output == "5"

    @pytest.mark.asyncio
    async def test_floating_point(self):
        """Test floating point calculations."""
        calc = Calculator()
        result = await calc.execute(expression="3.14 * 2")
        assert result.success is True
        assert float(result.output) == 6.28

    @pytest.mark.asyncio
    async def test_security_import_blocked(self):
        """Test that imports are blocked."""
        calc = Calculator()
        result = await calc.execute(expression="__import__('os')")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_security_eval_blocked(self):
        """Test that eval is blocked."""
        calc = Calculator()
        result = await calc.execute(expression="eval('1+1')")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_security_exec_blocked(self):
        """Test that exec is blocked."""
        calc = Calculator()
        result = await calc.execute(expression="exec('print(1)')")
        assert result.success is False


class TestCodeExecutorAdvanced:
    """Advanced tests for CodeExecutor tool."""

    @pytest.mark.asyncio
    async def test_return_value_capture(self):
        """Test capturing return values."""
        executor = CodeExecutor(timeout=5)
        code = """
result = 2 ** 10
print(result)
"""
        result = await executor.execute(code=code)
        assert result.success is True
        assert "1024" in result.output

    @pytest.mark.asyncio
    async def test_syntax_error(self):
        """Test handling syntax errors."""
        executor = CodeExecutor(timeout=5)
        result = await executor.execute(code="if True print('test')")
        assert result.success is False
        assert "SyntaxError" in result.error or "invalid syntax" in result.error

    @pytest.mark.asyncio
    async def test_import_error(self):
        """Test handling import errors."""
        executor = CodeExecutor(timeout=5)
        result = await executor.execute(code="import nonexistent_module")
        assert result.success is False
        assert "ModuleNotFoundError" in result.error or "No module" in result.error

    @pytest.mark.asyncio
    async def test_multiple_prints(self):
        """Test capturing multiple print statements."""
        executor = CodeExecutor(timeout=5)
        code = """
print('Line 1')
print('Line 2')
print('Line 3')
"""
        result = await executor.execute(code=code)
        assert result.success is True
        assert "Line 1" in result.output
        assert "Line 2" in result.output
        assert "Line 3" in result.output

    @pytest.mark.asyncio
    async def test_stderr_capture(self):
        """Test capturing stderr output."""
        executor = CodeExecutor(timeout=5)
        code = """
import sys
print('stdout message')
print('stderr message', file=sys.stderr)
"""
        result = await executor.execute(code=code)
        assert result.success is True
        assert "stdout message" in result.output

    @pytest.mark.asyncio
    async def test_custom_timeout(self):
        """Test custom timeout parameter."""
        executor = CodeExecutor(timeout=10)
        result = await executor.execute(
            code="import time; time.sleep(0.5); print('done')", timeout=2
        )
        assert result.success is True
        assert "done" in result.output


class TestFileIOAdvanced:
    """Advanced tests for FileIO tool."""

    @pytest.mark.asyncio
    async def test_write_creates_directories(self):
        """Test that write creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)
            result = await file_io.execute(
                operation="write", path="subdir/nested/file.txt", content="test content"
            )
            assert result.success is True
            assert Path(tmpdir, "subdir/nested/file.txt").exists()

    @pytest.mark.asyncio
    async def test_overwrite_existing_file(self):
        """Test overwriting existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)

            # Write initial content
            await file_io.execute(operation="write", path="test.txt", content="original")

            # Overwrite
            result = await file_io.execute(operation="write", path="test.txt", content="updated")
            assert result.success is True

            # Verify overwrite
            read_result = await file_io.execute(operation="read", path="test.txt")
            assert read_result.output == "updated"

    @pytest.mark.asyncio
    async def test_unicode_content(self):
        """Test handling unicode content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)

            unicode_content = "Hello 世界 🌍 Привет"
            write_result = await file_io.execute(
                operation="write", path="unicode.txt", content=unicode_content
            )
            assert write_result.success is True

            read_result = await file_io.execute(operation="read", path="unicode.txt")
            assert read_result.success is True
            assert read_result.output == unicode_content

    @pytest.mark.asyncio
    async def test_large_file(self):
        """Test handling large files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)

            # Create 1MB content
            large_content = "x" * (1024 * 1024)
            write_result = await file_io.execute(
                operation="write", path="large.txt", content=large_content
            )
            assert write_result.success is True

            read_result = await file_io.execute(operation="read", path="large.txt")
            assert read_result.success is True
            assert len(read_result.output) == len(large_content)

    @pytest.mark.asyncio
    async def test_empty_file(self):
        """Test handling empty files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)

            write_result = await file_io.execute(operation="write", path="empty.txt", content="")
            assert write_result.success is True

            read_result = await file_io.execute(operation="read", path="empty.txt")
            assert read_result.success is True
            assert read_result.output == ""

    @pytest.mark.asyncio
    async def test_path_traversal_variations(self):
        """Test various path traversal attempts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_io = FileIO(base_dir=tmpdir)

            dangerous_paths = [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32",
                "./../../sensitive.txt",
                "subdir/../../outside.txt",
            ]

            for path in dangerous_paths:
                result = await file_io.execute(operation="read", path=path)
                # Should either fail or stay within base_dir
                if result.success:
                    # If it succeeds, verify it's within base_dir
                    resolved = (Path(tmpdir) / path).resolve()
                    assert str(resolved).startswith(str(Path(tmpdir).resolve()))
                else:
                    # Should fail with either "denied" or "not found" error
                    assert "denied" in result.error.lower() or "not found" in result.error.lower()


class TestToolRegistryAdvanced:
    """Advanced tests for ToolRegistry."""

    @pytest.mark.asyncio
    async def test_parallel_execution_performance(self):
        """Test parallel execution is faster than sequential."""
        registry = ToolRegistry()
        executor = CodeExecutor(timeout=5)
        registry.register(executor)

        tool_calls = [
            {
                "name": "code_executor",
                "parameters": {"code": "import time; time.sleep(0.1); print('done')"},
            },
            {
                "name": "code_executor",
                "parameters": {"code": "import time; time.sleep(0.1); print('done')"},
            },
            {
                "name": "code_executor",
                "parameters": {"code": "import time; time.sleep(0.1); print('done')"},
            },
        ]

        # Parallel execution
        start = time.time()
        results = await registry.execute_parallel(tool_calls)
        parallel_time = time.time() - start

        assert len(results) == 3
        # Should take ~0.1s (parallel) not ~0.3s (sequential)
        # Allow some overhead for CI environments
        assert parallel_time < 0.3

    @pytest.mark.asyncio
    async def test_parallel_mixed_success_failure(self):
        """Test parallel execution with mixed success/failure."""
        registry = ToolRegistry()
        calc = Calculator()
        registry.register(calc)

        tool_calls = [
            {"name": "calculator", "parameters": {"expression": "2 + 2"}},
            {"name": "calculator", "parameters": {"expression": "invalid"}},
            {"name": "calculator", "parameters": {"expression": "5 * 5"}},
        ]

        results = await registry.execute_parallel(tool_calls)
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True

    @pytest.mark.asyncio
    async def test_execute_with_missing_parameters(self):
        """Test executing tool with missing required parameters."""
        registry = ToolRegistry()
        calc = Calculator()
        registry.register(calc)

        result = await registry.execute("calculator")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_register_multiple_tools(self):
        """Test registering multiple tools."""
        registry = ToolRegistry()
        calc = Calculator()
        executor = CodeExecutor()
        file_io = FileIO()

        registry.register(calc)
        registry.register(executor)
        registry.register(file_io)

        tools = registry.list_tools()
        assert len(tools) == 3
        assert "calculator" in tools
        assert "code_executor" in tools
        assert "file_io" in tools

    @pytest.mark.asyncio
    async def test_tool_replacement(self):
        """Test replacing a tool with same name."""
        registry = ToolRegistry()
        calc1 = Calculator()
        calc2 = Calculator()

        registry.register(calc1)
        registry.register(calc2)

        # Should have only one calculator
        tools = registry.list_tools()
        assert tools.count("calculator") == 1


class TestToolPerformance:
    """Performance tests for tool system."""

    @pytest.mark.asyncio
    async def test_calculator_performance(self):
        """Test calculator performance with many operations."""
        calc = Calculator()

        start = time.time()
        for i in range(100):
            result = await calc.execute(expression=f"{i} + {i}")
            assert result.success is True
        elapsed = time.time() - start

        assert elapsed < 1.0  # Should be very fast

    @pytest.mark.asyncio
    async def test_registry_lookup_performance(self):
        """Test registry lookup performance."""
        registry = ToolRegistry()
        for i in range(100):
            calc = Calculator()
            calc.name = f"calculator_{i}"
            registry.register(calc)

        start = time.time()
        for i in range(100):
            tool = registry.get(f"calculator_{i}")
            assert tool is not None
        elapsed = time.time() - start

        assert elapsed < 0.1  # Lookups should be instant


class TestToolErrorRecovery:
    """Test error recovery and resilience."""

    @pytest.mark.asyncio
    async def test_tool_exception_doesnt_crash_registry(self):
        """Test that tool exceptions don't crash the registry."""
        registry = ToolRegistry()

        @tool(name="crasher")
        async def crash_tool():
            raise RuntimeError("Intentional crash")

        # The decorator registers to global registry, so we need to get it from there
        global_registry = get_global_registry()
        result = await global_registry.execute("crasher")
        assert result.success is False
        assert "Intentional crash" in result.error

        # Registry should still work
        calc = Calculator()
        registry.register(calc)
        result = await registry.execute("calculator", expression="2+2")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_parallel_execution_one_failure(self):
        """Test that one failure doesn't affect other parallel executions."""
        registry = ToolRegistry()
        calc = Calculator()
        registry.register(calc)

        tool_calls = [
            {"name": "calculator", "parameters": {"expression": "2 + 2"}},
            {"name": "nonexistent", "parameters": {}},
            {"name": "calculator", "parameters": {"expression": "3 + 3"}},
        ]

        results = await registry.execute_parallel(tool_calls)
        assert len(results) == 3
        assert results[0].success is True
        assert results[0].output == "4"
        assert results[1].success is False
        assert results[2].success is True
        assert results[2].output == "6"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
