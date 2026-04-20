#!/usr/bin/env python3
"""Version bumping utility for AgentMind.

This script handles semantic versioning (MAJOR.MINOR.PATCH) and updates
version strings across the project.
"""

import re
import sys
from pathlib import Path
from typing import Tuple


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def read_version_from_setup() -> str:
    """Read current version from setup.py."""
    setup_file = get_project_root() / "setup.py"
    content = setup_file.read_text()
    match = re.search(r'version="([^"]+)"', content)
    if not match:
        raise ValueError("Could not find version in setup.py")
    return match.group(1)


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse version string into (major, minor, patch) tuple."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return tuple(map(int, match.groups()))


def format_version(major: int, minor: int, patch: int) -> str:
    """Format version tuple into string."""
    return f"{major}.{minor}.{patch}"


def bump_version(version: str, bump_type: str) -> str:
    """Bump version according to type (major, minor, patch).

    Args:
        version: Current version string (e.g., "0.1.0")
        bump_type: Type of bump ("major", "minor", or "patch")

    Returns:
        New version string

    Raises:
        ValueError: If bump_type is invalid
    """
    major, minor, patch = parse_version(version)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return format_version(major, minor, patch)


def update_version_in_file(file_path: Path, old_version: str, new_version: str) -> bool:
    """Update version string in a file.

    Args:
        file_path: Path to file to update
        old_version: Current version string
        new_version: New version string

    Returns:
        True if file was updated, False otherwise
    """
    if not file_path.exists():
        return False

    content = file_path.read_text()
    updated_content = content.replace(f'version="{old_version}"', f'version="{new_version}"')
    updated_content = updated_content.replace(
        f"version = '{old_version}'", f"version = '{new_version}'"
    )
    updated_content = updated_content.replace(
        f'__version__ = "{old_version}"', f'__version__ = "{new_version}"'
    )

    if content != updated_content:
        file_path.write_text(updated_content)
        return True

    return False


def update_all_versions(old_version: str, new_version: str) -> None:
    """Update version in all relevant files.

    Args:
        old_version: Current version string
        new_version: New version string
    """
    project_root = get_project_root()

    # Files to update
    files_to_update = [
        project_root / "setup.py",
        project_root / "src" / "agentmind" / "__init__.py",
        project_root / "pyproject.toml",
    ]

    updated_files = []
    for file_path in files_to_update:
        if update_version_in_file(file_path, old_version, new_version):
            updated_files.append(file_path.relative_to(project_root))

    if updated_files:
        print(f"Updated version in {len(updated_files)} file(s):", file=sys.stderr)
        for file_path in updated_files:
            print(f"  - {file_path}", file=sys.stderr)
    else:
        print("Warning: No files were updated", file=sys.stderr)


def main() -> None:
    """Main entry point for version bumping."""
    if len(sys.argv) < 2:
        print("Usage: bump_version.py <major|minor|patch|custom> [version]", file=sys.stderr)
        print("", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  bump_version.py patch        # 0.1.0 -> 0.1.1", file=sys.stderr)
        print("  bump_version.py minor        # 0.1.0 -> 0.2.0", file=sys.stderr)
        print("  bump_version.py major        # 0.1.0 -> 1.0.0", file=sys.stderr)
        print("  bump_version.py custom 1.5.2 # Set to 1.5.2", file=sys.stderr)
        sys.exit(1)

    bump_type = sys.argv[1].lower()

    try:
        # Get current version
        current_version = read_version_from_setup()
        print(f"Current version: {current_version}", file=sys.stderr)

        # Calculate new version
        if bump_type == "custom":
            if len(sys.argv) < 3:
                print("Error: Custom version requires version argument", file=sys.stderr)
                sys.exit(1)
            new_version = sys.argv[2]
            # Validate format
            parse_version(new_version)
        elif bump_type in ("major", "minor", "patch"):
            new_version = bump_version(current_version, bump_type)
        else:
            print(f"Error: Invalid bump type: {bump_type}", file=sys.stderr)
            print("Valid types: major, minor, patch, custom", file=sys.stderr)
            sys.exit(1)

        # Update version in all files
        update_all_versions(current_version, new_version)

        print(f"New version: {new_version}", file=sys.stderr)
        # Print to stdout for script capture
        print(new_version)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
