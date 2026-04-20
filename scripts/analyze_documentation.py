"""
Documentation Improvement Script
Generates comprehensive inline documentation for AgentMind
"""

from pathlib import Path
import ast
from typing import List, Dict, Any


class DocstringGenerator:
    """Generate docstrings for functions and classes"""

    @staticmethod
    def generate_function_docstring(func_name: str, args: List[str], returns: bool = True) -> str:
        """Generate a docstring template for a function"""
        docstring = f'''"""
        {func_name.replace('_', ' ').title()}

        Args:
'''

        for arg in args:
            if arg != "self" and arg != "cls":
                docstring += f"            {arg}: Description of {arg}\n"

        if returns:
            docstring += """
        Returns:
            Description of return value

        Raises:
            Exception: Description of when this is raised

        Examples:
            >>> # Example usage
            >>> result = {func_name}()
        """

        docstring += '        """'
        return docstring

    @staticmethod
    def generate_class_docstring(class_name: str) -> str:
        """Generate a docstring template for a class"""
        return f'''"""
        {class_name.replace('_', ' ').title()}

        This class provides functionality for...

        Attributes:
            attribute_name: Description of attribute

        Examples:
            >>> instance = {class_name}()
            >>> instance.method()
        """'''


def analyze_missing_docstrings(root_dir: str = "src/agentmind") -> Dict[str, Any]:
    """Analyze files for missing docstrings"""
    missing = {
        "functions": [],
        "classes": [],
        "modules": [],
    }

    for filepath in Path(root_dir).rglob("*.py"):
        if "__pycache__" in str(filepath):
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # Check module docstring
            if not ast.get_docstring(tree):
                missing["modules"].append(str(filepath))

            # Check functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not ast.get_docstring(node):
                        missing["functions"].append(
                            {
                                "file": str(filepath),
                                "name": node.name,
                                "line": node.lineno,
                            }
                        )

                elif isinstance(node, ast.ClassDef):
                    if not ast.get_docstring(node):
                        missing["classes"].append(
                            {
                                "file": str(filepath),
                                "name": node.name,
                                "line": node.lineno,
                            }
                        )

        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")

    return missing


def generate_documentation_report(output_file: str = "documentation_report.md"):
    """Generate documentation improvement report"""
    missing = analyze_missing_docstrings()

    report = f"""# Documentation Improvement Report

**Generated:** {__import__('datetime').datetime.now().isoformat()}

## Summary

- **Modules without docstrings:** {len(missing['modules'])}
- **Functions without docstrings:** {len(missing['functions'])}
- **Classes without docstrings:** {len(missing['classes'])}

## Modules Missing Docstrings

"""

    for module in missing["modules"][:20]:
        report += f"- {module}\n"

    report += """
## Functions Missing Docstrings (Top 50)

| File | Function | Line |
|------|----------|------|
"""

    for func in missing["functions"][:50]:
        report += f"| {func['file']} | {func['name']} | {func['line']} |\n"

    report += """
## Classes Missing Docstrings

| File | Class | Line |
|------|-------|------|
"""

    for cls in missing["classes"][:50]:
        report += f"| {cls['file']} | {cls['name']} | {cls['line']} |\n"

    report += """
## Documentation Standards

### Module Docstrings

Every module should have a docstring at the top:

```python
\"\"\"
Module Name

Brief description of what this module does.

This module provides...
\"\"\"
```

### Function Docstrings

Use Google-style docstrings:

```python
def function_name(arg1: str, arg2: int) -> bool:
    \"\"\"
    Brief description of function.

    Longer description if needed.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When invalid input is provided

    Examples:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    \"\"\"
    pass
```

### Class Docstrings

```python
class ClassName:
    \"\"\"
    Brief description of class.

    Longer description of what this class does and how to use it.

    Attributes:
        attribute_name: Description of attribute

    Examples:
        >>> instance = ClassName()
        >>> instance.method()
    \"\"\"
    pass
```

## Action Items

1. Add module docstrings to all files
2. Add docstrings to all public functions
3. Add docstrings to all classes
4. Include examples in docstrings
5. Document all parameters and return values
6. Document exceptions that can be raised

---

*Generated by AgentMind Documentation Analyzer*
"""

    with open(output_file, "w") as f:
        f.write(report)

    print(f"✓ Report saved to {output_file}")


def main():
    """Main function"""
    print("Analyzing documentation...")
    print("-" * 80)

    missing = analyze_missing_docstrings()

    print(f"\nSummary:")
    print(f"  Modules without docstrings: {len(missing['modules'])}")
    print(f"  Functions without docstrings: {len(missing['functions'])}")
    print(f"  Classes without docstrings: {len(missing['classes'])}")

    print("\nGenerating report...")
    generate_documentation_report()

    print("\n" + "-" * 80)
    print("✓ Documentation analysis complete!")


if __name__ == "__main__":
    main()
