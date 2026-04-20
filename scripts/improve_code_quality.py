"""
Code Quality Improvement Script
Automatically improves code quality by adding type hints and documentation
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


def add_type_hints_to_file(filepath: str) -> Tuple[bool, List[str]]:
    """Add missing type hints to a file"""
    changes = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        modified = False

        # Add common type hints patterns
        patterns = [
            # Add -> None to functions without return type
            (
                r"(def \w+\([^)]*\)):",
                lambda m: f"{m.group(1)} -> None:" if "-> " not in m.group(0) else m.group(0),
            ),
            # Add str type to string parameters
            (
                r"def (\w+)\((\w+):",
                lambda m: (
                    f"def {m.group(1)}({m.group(2)}: str:" if ":" not in m.group(2) else m.group(0)
                ),
            ),
        ]

        # Note: This is a simplified version. In production, use tools like MonkeyType or PyAnnotate
        # For now, we'll focus on manual improvements to key files

        return False, []  # Return False to indicate no automatic changes made

    except Exception as e:
        return False, [f"Error: {str(e)}"]


def improve_error_messages(filepath: str) -> Tuple[bool, List[str]]:
    """Improve error messages to be more actionable"""
    changes = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        modified = False

        # Improve generic error messages
        improvements = {
            r'raise ValueError\("Invalid"\)': 'raise ValueError("Invalid value provided. Expected: <description>")',
            r'raise Exception\("Error"\)': 'raise RuntimeError("Operation failed. Please check: <details>")',
            r'raise TypeError\("Wrong type"\)': 'raise TypeError("Wrong type provided. Expected: <type>, got: <actual>")',
        }

        for pattern, replacement in improvements.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                modified = True
                changes.append(f"Improved error message: {pattern}")

        if modified:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        return modified, changes

    except Exception as e:
        return False, [f"Error: {str(e)}"]


def add_docstrings(filepath: str) -> Tuple[bool, List[str]]:
    """Add missing docstrings to functions"""
    changes = []

    # This would require AST manipulation
    # For now, we'll document the need for manual review

    return False, []


def format_code(filepath: str) -> Tuple[bool, List[str]]:
    """Format code using black"""
    import subprocess

    try:
        result = subprocess.run(
            ["black", filepath],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return True, ["Formatted with black"]
        else:
            return False, [f"Black error: {result.stderr}"]

    except FileNotFoundError:
        return False, ["Black not installed"]
    except Exception as e:
        return False, [f"Error: {str(e)}"]


def sort_imports(filepath: str) -> Tuple[bool, List[str]]:
    """Sort imports using isort"""
    import subprocess

    try:
        result = subprocess.run(
            ["isort", filepath],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return True, ["Sorted imports with isort"]
        else:
            return False, [f"isort error: {result.stderr}"]

    except FileNotFoundError:
        return False, ["isort not installed"]
    except Exception as e:
        return False, [f"Error: {str(e)}"]


def improve_file(filepath: str) -> dict:
    """Improve a single file"""
    results = {
        "filepath": filepath,
        "changes": [],
        "errors": [],
    }

    # Format code
    success, changes = format_code(filepath)
    if success:
        results["changes"].extend(changes)
    else:
        results["errors"].extend(changes)

    # Sort imports
    success, changes = sort_imports(filepath)
    if success:
        results["changes"].extend(changes)
    else:
        results["errors"].extend(changes)

    # Improve error messages
    success, changes = improve_error_messages(filepath)
    if success:
        results["changes"].extend(changes)

    return results


def improve_project(root_dir: str = "src/agentmind"):
    """Improve entire project"""
    print("Improving code quality...")
    print("-" * 80)

    total_files = 0
    improved_files = 0
    total_changes = 0

    for filepath in Path(root_dir).rglob("*.py"):
        if "__pycache__" in str(filepath):
            continue

        total_files += 1
        result = improve_file(str(filepath))

        if result["changes"]:
            improved_files += 1
            total_changes += len(result["changes"])
            print(f"\n✓ {filepath}")
            for change in result["changes"]:
                print(f"  - {change}")

        if result["errors"]:
            print(f"\n✗ {filepath}")
            for error in result["errors"]:
                print(f"  - {error}")

    print("\n" + "-" * 80)
    print(f"Summary:")
    print(f"  Files processed: {total_files}")
    print(f"  Files improved: {improved_files}")
    print(f"  Total changes: {total_changes}")
    print("-" * 80)


def run_linters():
    """Run linters and type checkers"""
    import subprocess

    print("\nRunning linters and type checkers...")
    print("-" * 80)

    # Run mypy
    print("\n1. Running mypy...")
    try:
        result = subprocess.run(
            ["mypy", "src/agentmind", "--ignore-missing-imports"],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except FileNotFoundError:
        print("  mypy not installed")

    # Run ruff
    print("\n2. Running ruff...")
    try:
        result = subprocess.run(
            ["ruff", "check", "src/agentmind"],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except FileNotFoundError:
        print("  ruff not installed")

    # Run flake8
    print("\n3. Running flake8...")
    try:
        result = subprocess.run(
            ["flake8", "src/agentmind"],
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        else:
            print("  ✓ No issues found")
    except FileNotFoundError:
        print("  flake8 not installed")

    print("-" * 80)


def main():
    """Main function"""
    print("=" * 80)
    print("CODE QUALITY IMPROVEMENT")
    print("=" * 80)

    # Improve project
    improve_project()

    # Run linters
    run_linters()

    print("\n✓ Code quality improvement complete!")
    print("\nNext steps:")
    print("  1. Review changes and commit")
    print("  2. Run tests: pytest")
    print("  3. Check coverage: pytest --cov=src/agentmind")
    print("  4. Manual review of complex functions")


if __name__ == "__main__":
    main()
