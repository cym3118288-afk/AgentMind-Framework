"""Built-in tools for AgentMind agents.

This module provides commonly used tools:
- Calculator: Perform mathematical calculations
- WebSearch: Search the web using DuckDuckGo
- CodeExecutor: Execute Python code safely
- FileIO: Read and write files
"""

import ast
import asyncio
import operator
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

from .base import Tool, ToolResult


class Calculator(Tool):
    """Perform safe mathematical calculations."""

    def __init__(self):
        super().__init__()
        self.name = "calculator"
        self.description = "Evaluate mathematical expressions safely. Supports +, -, *, /, **, (), and basic functions."

        # Safe operators
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

    async def execute(self, expression: str) -> ToolResult:
        """Execute a mathematical calculation.

        Args:
            expression: Mathematical expression to evaluate

        Returns:
            ToolResult with calculation result
        """
        try:
            # Parse the expression
            tree = ast.parse(expression, mode='eval')
            result = self._eval_node(tree.body)

            return ToolResult(
                success=True,
                output=str(result),
                metadata={"expression": expression}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Calculation error: {str(e)}",
                metadata={"expression": expression}
            )

    def _eval_node(self, node):
        """Safely evaluate an AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.operators.get(type(node.op))
            if op:
                return op(left, right)
            raise ValueError(f"Unsupported operator: {type(node.op)}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op = self.operators.get(type(node.op))
            if op:
                return op(operand)
            raise ValueError(f"Unsupported unary operator: {type(node.op)}")
        else:
            raise ValueError(f"Unsupported expression type: {type(node)}")


class WebSearch(Tool):
    """Search the web using DuckDuckGo."""

    def __init__(self):
        super().__init__()
        self.name = "web_search"
        self.description = "Search the web for information using DuckDuckGo. Returns top search results."

    async def execute(self, query: str, max_results: int = 5) -> ToolResult:
        """Search the web.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            ToolResult with search results
        """
        try:
            # Try to use duckduckgo_search if available
            try:
                from duckduckgo_search import DDGS

                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))

                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"{i}. {result.get('title', 'No title')}\n"
                        f"   URL: {result.get('href', 'No URL')}\n"
                        f"   {result.get('body', 'No description')}"
                    )

                output = "\n\n".join(formatted_results)

                return ToolResult(
                    success=True,
                    output=output,
                    metadata={
                        "query": query,
                        "num_results": len(results)
                    }
                )
            except ImportError:
                return ToolResult(
                    success=False,
                    error="duckduckgo_search package not installed. Install with: pip install duckduckgo-search"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}",
                metadata={"query": query}
            )


class CodeExecutor(Tool):
    """Execute Python code safely in a subprocess with timeout."""

    def __init__(self, timeout: int = 10):
        super().__init__()
        self.name = "code_executor"
        self.description = "Execute Python code safely in an isolated subprocess with timeout protection."
        self.timeout = timeout

    async def execute(self, code: str, timeout: int = None) -> ToolResult:
        """Execute Python code.

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds (default: 10)

        Returns:
            ToolResult with execution output
        """
        exec_timeout = timeout or self.timeout

        try:
            # Run code in subprocess for isolation
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                '-c',
                code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=exec_timeout
                )

                stdout_text = stdout.decode('utf-8') if stdout else ""
                stderr_text = stderr.decode('utf-8') if stderr else ""

                if process.returncode == 0:
                    return ToolResult(
                        success=True,
                        output=stdout_text,
                        metadata={
                            "return_code": process.returncode,
                            "stderr": stderr_text if stderr_text else None
                        }
                    )
                else:
                    return ToolResult(
                        success=False,
                        error=stderr_text or "Code execution failed",
                        output=stdout_text,
                        metadata={"return_code": process.returncode}
                    )

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    error=f"Code execution timed out after {exec_timeout} seconds"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Execution error: {str(e)}"
            )


class FileIO(Tool):
    """Read and write files safely."""

    def __init__(self, base_dir: str = "."):
        super().__init__()
        self.name = "file_io"
        self.description = "Read from and write to files. Operations are restricted to the base directory."
        self.base_dir = Path(base_dir).resolve()

    async def execute(self, operation: str, path: str, content: str = None) -> ToolResult:
        """Perform file I/O operation.

        Args:
            operation: 'read' or 'write'
            path: File path (relative to base_dir)
            content: Content to write (for write operation)

        Returns:
            ToolResult with operation outcome
        """
        try:
            # Resolve path and ensure it's within base_dir
            file_path = (self.base_dir / path).resolve()

            if not str(file_path).startswith(str(self.base_dir)):
                return ToolResult(
                    success=False,
                    error="Access denied: path outside base directory"
                )

            if operation == "read":
                if not file_path.exists():
                    return ToolResult(
                        success=False,
                        error=f"File not found: {path}"
                    )

                content = file_path.read_text(encoding='utf-8')
                return ToolResult(
                    success=True,
                    output=content,
                    metadata={
                        "operation": "read",
                        "path": str(path),
                        "size": len(content)
                    }
                )

            elif operation == "write":
                if content is None:
                    return ToolResult(
                        success=False,
                        error="Content is required for write operation"
                    )

                # Create parent directories if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)

                file_path.write_text(content, encoding='utf-8')
                return ToolResult(
                    success=True,
                    output=f"Successfully wrote {len(content)} characters to {path}",
                    metadata={
                        "operation": "write",
                        "path": str(path),
                        "size": len(content)
                    }
                )

            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown operation: {operation}. Use 'read' or 'write'."
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"File I/O error: {str(e)}",
                metadata={"operation": operation, "path": path}
            )
