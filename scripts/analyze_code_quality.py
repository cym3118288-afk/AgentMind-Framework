"""
Code Quality Analysis Script
Analyzes code complexity, type coverage, and documentation
"""

import os
import ast
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json


class ComplexityAnalyzer(ast.NodeVisitor):
    """Analyze cyclomatic complexity of Python code"""

    def __init__(self):
        self.functions = []
        self.current_function = None
        self.complexity = 0

    def visit_FunctionDef(self, node):
        """Visit function definition"""
        old_function = self.current_function
        old_complexity = self.complexity

        self.current_function = node.name
        self.complexity = 1  # Base complexity

        self.generic_visit(node)

        self.functions.append(
            {
                "name": node.name,
                "lineno": node.lineno,
                "complexity": self.complexity,
                "args": len(node.args.args),
                "has_docstring": ast.get_docstring(node) is not None,
            }
        )

        self.current_function = old_function
        self.complexity = old_complexity

    def visit_If(self, node):
        """Visit if statement"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        """Visit for loop"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        """Visit while loop"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        """Visit exception handler"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        """Visit with statement"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        """Visit boolean operation"""
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


class TypeHintAnalyzer(ast.NodeVisitor):
    """Analyze type hint coverage"""

    def __init__(self):
        self.functions = []
        self.total_params = 0
        self.typed_params = 0
        self.total_returns = 0
        self.typed_returns = 0

    def visit_FunctionDef(self, node):
        """Visit function definition"""
        # Count parameters
        for arg in node.args.args:
            if arg.arg != "self":
                self.total_params += 1
                if arg.annotation is not None:
                    self.typed_params += 1

        # Count return type
        self.total_returns += 1
        if node.returns is not None:
            self.typed_returns += 1

        self.functions.append(
            {
                "name": node.name,
                "lineno": node.lineno,
                "has_return_type": node.returns is not None,
                "param_count": len([a for a in node.args.args if a.arg != "self"]),
                "typed_param_count": len(
                    [a for a in node.args.args if a.arg != "self" and a.annotation]
                ),
            }
        )

        self.generic_visit(node)


def analyze_file(filepath: str) -> Dict[str, Any]:
    """Analyze a single Python file"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        # Complexity analysis
        complexity_analyzer = ComplexityAnalyzer()
        complexity_analyzer.visit(tree)

        # Type hint analysis
        type_analyzer = TypeHintAnalyzer()
        type_analyzer.visit(tree)

        # Count lines
        lines = content.split("\n")
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith("#")])
        comment_lines = len([l for l in lines if l.strip().startswith("#")])
        docstring_lines = content.count('"""') // 2 * 3  # Rough estimate

        return {
            "filepath": filepath,
            "total_lines": len(lines),
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "docstring_lines": docstring_lines,
            "functions": complexity_analyzer.functions,
            "type_coverage": {
                "total_params": type_analyzer.total_params,
                "typed_params": type_analyzer.typed_params,
                "total_returns": type_analyzer.total_returns,
                "typed_returns": type_analyzer.typed_returns,
                "param_coverage": (
                    type_analyzer.typed_params / type_analyzer.total_params * 100
                    if type_analyzer.total_params > 0
                    else 0
                ),
                "return_coverage": (
                    type_analyzer.typed_returns / type_analyzer.total_returns * 100
                    if type_analyzer.total_returns > 0
                    else 0
                ),
            },
        }

    except Exception as e:
        return {
            "filepath": filepath,
            "error": str(e),
        }


def analyze_project(root_dir: str = "src/agentmind") -> Dict[str, Any]:
    """Analyze entire project"""
    results = []
    complex_functions = []
    missing_types = []

    # Find all Python files
    for filepath in Path(root_dir).rglob("*.py"):
        if "__pycache__" in str(filepath):
            continue

        result = analyze_file(str(filepath))
        if "error" not in result:
            results.append(result)

            # Find complex functions (complexity > 10)
            for func in result["functions"]:
                if func["complexity"] > 10:
                    complex_functions.append(
                        {
                            "file": result["filepath"],
                            "function": func["name"],
                            "complexity": func["complexity"],
                            "line": func["lineno"],
                        }
                    )

            # Find functions missing type hints
            for func in result["functions"]:
                if not func["has_return_type"] or func["typed_param_count"] < func["param_count"]:
                    missing_types.append(
                        {
                            "file": result["filepath"],
                            "function": func["name"],
                            "line": func["lineno"],
                            "missing_return": not func["has_return_type"],
                            "missing_params": func["param_count"] - func["typed_param_count"],
                        }
                    )

    # Aggregate statistics
    total_lines = sum(r["total_lines"] for r in results)
    total_code_lines = sum(r["code_lines"] for r in results)
    total_functions = sum(len(r["functions"]) for r in results)

    total_params = sum(r["type_coverage"]["total_params"] for r in results)
    typed_params = sum(r["type_coverage"]["typed_params"] for r in results)
    total_returns = sum(r["type_coverage"]["total_returns"] for r in results)
    typed_returns = sum(r["type_coverage"]["typed_returns"] for r in results)

    return {
        "summary": {
            "total_files": len(results),
            "total_lines": total_lines,
            "total_code_lines": total_code_lines,
            "total_functions": total_functions,
            "complex_functions": len(complex_functions),
            "type_coverage": {
                "param_coverage": typed_params / total_params * 100 if total_params > 0 else 0,
                "return_coverage": typed_returns / total_returns * 100 if total_returns > 0 else 0,
            },
        },
        "files": results,
        "complex_functions": sorted(complex_functions, key=lambda x: x["complexity"], reverse=True),
        "missing_types": missing_types[:50],  # Top 50
    }


def generate_report(analysis: Dict[str, Any], output_file: str = "code_quality_report.md"):
    """Generate markdown report"""
    summary = analysis["summary"]

    report = f"""# Code Quality Analysis Report

**Generated:** {__import__('datetime').datetime.now().isoformat()}

## Summary

- **Total Files:** {summary['total_files']}
- **Total Lines:** {summary['total_lines']:,}
- **Code Lines:** {summary['total_code_lines']:,}
- **Total Functions:** {summary['total_functions']}
- **Complex Functions (>10):** {summary['complex_functions']}

## Type Coverage

- **Parameter Type Coverage:** {summary['type_coverage']['param_coverage']:.1f}%
- **Return Type Coverage:** {summary['type_coverage']['return_coverage']:.1f}%

## Complex Functions (Cyclomatic Complexity > 10)

These functions should be refactored to reduce complexity:

| File | Function | Complexity | Line |
|------|----------|------------|------|
"""

    for func in analysis["complex_functions"][:20]:
        report += (
            f"| {func['file']} | {func['function']} | {func['complexity']} | {func['line']} |\n"
        )

    report += """
## Missing Type Hints

Functions missing type hints (top 50):

| File | Function | Line | Missing Return | Missing Params |
|------|----------|------|----------------|----------------|
"""

    for func in analysis["missing_types"][:50]:
        report += f"| {func['file']} | {func['function']} | {func['line']} | {'Yes' if func['missing_return'] else 'No'} | {func['missing_params']} |\n"

    report += """
## Recommendations

### High Priority

1. **Refactor Complex Functions**: Functions with complexity > 10 should be broken down into smaller functions
2. **Add Type Hints**: Improve type coverage to at least 90% for better IDE support and type checking
3. **Add Docstrings**: Ensure all public functions have comprehensive docstrings

### Medium Priority

1. **Increase Test Coverage**: Aim for >90% code coverage
2. **Add More Comments**: Complex logic should be well-commented
3. **Improve Error Messages**: Make error messages more actionable

### Low Priority

1. **Code Formatting**: Ensure consistent formatting with black/ruff
2. **Import Organization**: Use isort for consistent import ordering
3. **Remove Dead Code**: Identify and remove unused code

## Next Steps

1. Run `mypy --strict` to identify type issues
2. Run `radon cc src/agentmind -a` for detailed complexity analysis
3. Run `pytest --cov=src/agentmind` for coverage report
4. Address high-priority issues first

---

*Generated by AgentMind Code Quality Analyzer*
"""

    with open(output_file, "w") as f:
        f.write(report)

    print(f"✓ Report saved to {output_file}")


def main():
    """Main function"""
    print("Analyzing code quality...")
    print("-" * 80)

    # Analyze project
    analysis = analyze_project("src/agentmind")

    # Print summary
    summary = analysis["summary"]
    print(f"\nSummary:")
    print(f"  Files analyzed: {summary['total_files']}")
    print(f"  Total lines: {summary['total_lines']:,}")
    print(f"  Code lines: {summary['total_code_lines']:,}")
    print(f"  Functions: {summary['total_functions']}")
    print(f"  Complex functions (>10): {summary['complex_functions']}")
    print(f"\nType Coverage:")
    print(f"  Parameters: {summary['type_coverage']['param_coverage']:.1f}%")
    print(f"  Returns: {summary['type_coverage']['return_coverage']:.1f}%")

    # Show top complex functions
    if analysis["complex_functions"]:
        print(f"\nTop 5 Most Complex Functions:")
        for func in analysis["complex_functions"][:5]:
            print(f"  - {func['function']} ({func['file']}): {func['complexity']}")

    # Generate report
    print("\nGenerating detailed report...")
    generate_report(analysis)

    # Save JSON
    with open("code_quality_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    print("✓ Analysis saved to code_quality_analysis.json")

    print("\n" + "-" * 80)
    print("✓ Code quality analysis complete!")


if __name__ == "__main__":
    main()
