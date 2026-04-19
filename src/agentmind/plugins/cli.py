"""Plugin CLI commands for AgentMind."""

import asyncio
import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from typing import Optional

from agentmind.plugins.manager import PluginManager
from agentmind.plugins.loader import PluginRegistry
from agentmind.plugins.marketplace import (
    PluginRegistry as MarketplaceRegistry,
    PluginManifest,
    PluginCategory,
)
from agentmind.plugins.config import ConfigManager
from agentmind.plugins.dependencies import DependencyResolver
from agentmind.plugins.audit import PluginAuditLogger

console = Console()


@click.group(name="plugin")
def plugin_cli():
    """Plugin management commands."""
    pass


@plugin_cli.command()
@click.argument("name")
@click.option(
    "--type",
    "plugin_type",
    type=click.Choice(["tool", "integration", "memory", "llm", "orchestration", "middleware"]),
    default="tool",
    help="Plugin type",
)
@click.option("--author", default="Your Name", help="Plugin author")
@click.option("--description", default="A new AgentMind plugin", help="Plugin description")
@click.option("--output", type=click.Path(), help="Output directory")
def create(name: str, plugin_type: str, author: str, description: str, output: Optional[str]):
    """Create a new plugin from template.

    Example:
        agentmind plugin create my-plugin --type tool --author "John Doe"
    """
    output_dir = Path(output) if output else Path.cwd() / f"agentmind-plugin-{name}"

    if output_dir.exists():
        console.print(f"[red]Error: Directory {output_dir} already exists[/red]")
        return

    console.print(f"[bold cyan]Creating plugin: {name}[/bold cyan]\n")

    # Create directory structure
    output_dir.mkdir(parents=True)
    package_dir = output_dir / f"agentmind_plugin_{name.replace('-', '_')}"
    package_dir.mkdir()

    # Create __init__.py
    init_content = f'''"""
{name} - AgentMind Plugin
{description}
"""

from .plugin import {name.replace('-', '_').title()}Plugin

__version__ = "0.1.0"
__all__ = ["{name.replace('-', '_').title()}Plugin"]
'''
    (package_dir / "__init__.py").write_text(init_content)

    # Create plugin.py based on type
    plugin_content = _generate_plugin_code(name, plugin_type, author, description)
    (package_dir / "plugin.py").write_text(plugin_content)

    # Create setup.py
    setup_content = f"""from setuptools import setup, find_packages

setup(
    name="agentmind-plugin-{name}",
    version="0.1.0",
    description="{description}",
    author="{author}",
    packages=find_packages(),
    install_requires=[
        "agentmind>=0.3.0",
    ],
    entry_points={{
        "agentmind.plugins.{plugin_type}": [
            "{name} = agentmind_plugin_{name.replace('-', '_')}.plugin:{name.replace('-', '_').title()}Plugin",
        ],
    }},
    python_requires=">=3.8",
)
"""
    (output_dir / "setup.py").write_text(setup_content)

    # Create README.md
    readme_content = f"""# {name}

{description}

## Installation

```bash
pip install -e .
```

## Usage

```python
from agentmind.plugins import PluginManager

manager = PluginManager()
manager.discover_and_load()

# Your plugin will be automatically discovered
```

## Development

```bash
# Install in development mode
pip install -e .

# Run tests
pytest tests/
```

## License

MIT
"""
    (output_dir / "README.md").write_text(readme_content)

    # Create tests directory
    tests_dir = output_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")

    test_content = f'''"""Tests for {name} plugin."""

import pytest
from agentmind_plugin_{name.replace('-', '_')}.plugin import {name.replace('-', '_').title()}Plugin


def test_plugin_metadata():
    """Test plugin metadata."""
    plugin = {name.replace('-', '_').title()}Plugin()
    metadata = plugin.get_metadata()

    assert metadata.name == "{name}"
    assert metadata.version == "0.1.0"


@pytest.mark.asyncio
async def test_plugin_initialize():
    """Test plugin initialization."""
    plugin = {name.replace('-', '_').title()}Plugin()
    await plugin.initialize()
    assert plugin.is_initialized


@pytest.mark.asyncio
async def test_plugin_shutdown():
    """Test plugin shutdown."""
    plugin = {name.replace('-', '_').title()}Plugin()
    await plugin.initialize()
    await plugin.shutdown()
'''
    (tests_dir / "test_plugin.py").write_text(test_content)

    # Create config example
    config_content = f"""# Configuration for {name} plugin

enabled: true
environment: development

settings:
  # Add your plugin-specific settings here
  example_setting: "value"
"""
    (output_dir / "config.example.yaml").write_text(config_content)

    # Display success
    tree = Tree(f"[bold green]{output_dir.name}/[/bold green]")
    tree.add("[cyan]setup.py[/cyan]")
    tree.add("[cyan]README.md[/cyan]")
    tree.add("[cyan]config.example.yaml[/cyan]")

    package_node = tree.add(f"[yellow]{package_dir.name}/[/yellow]")
    package_node.add("[cyan]__init__.py[/cyan]")
    package_node.add("[cyan]plugin.py[/cyan]")

    tests_node = tree.add("[yellow]tests/[/yellow]")
    tests_node.add("[cyan]test_plugin.py[/cyan]")

    console.print("\n[bold green]✓ Plugin created successfully![/bold green]\n")
    console.print(tree)
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  cd {output_dir.name}")
    console.print(f"  pip install -e .")
    console.print(f"  pytest tests/")


def _generate_plugin_code(name: str, plugin_type: str, author: str, description: str) -> str:
    """Generate plugin code based on type."""
    class_name = name.replace("-", "_").title() + "Plugin"

    if plugin_type == "tool":
        return f'''"""
{name} - Tool Plugin
{description}
"""

from typing import Any, Dict, Optional
from agentmind.plugins.base import ToolPlugin, PluginMetadata, PluginType


class {class_name}(ToolPlugin):
    """Tool plugin: {name}."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize plugin."""
        super().__init__(config)

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="{name}",
            version="0.1.0",
            description="{description}",
            author="{author}",
            plugin_type=PluginType.TOOL,
            tags=["tool"],
        )

    async def initialize(self) -> None:
        """Initialize the plugin."""
        # Add initialization logic here
        pass

    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        # Add cleanup logic here
        pass

    async def execute(self, **kwargs) -> Any:
        """Execute the tool.

        Args:
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        # Implement your tool logic here
        return {{"status": "success", "result": "Tool executed"}}

    def get_tool_definition(self) -> Dict[str, Any]:
        """Get tool definition for LLM function calling."""
        return {{
            "name": "{name}",
            "description": "{description}",
            "parameters": {{
                "type": "object",
                "properties": {{
                    # Define your tool parameters here
                }},
                "required": []
            }}
        }}
'''

    elif plugin_type == "integration":
        return f'''"""
{name} - Integration Plugin
{description}
"""

from typing import Any, Dict, Optional
from agentmind.plugins.base import IntegrationPlugin, PluginMetadata, PluginType


class {class_name}(IntegrationPlugin):
    """Integration plugin: {name}."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize plugin."""
        super().__init__(config)
        self._connected = False

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="{name}",
            version="0.1.0",
            description="{description}",
            author="{author}",
            plugin_type=PluginType.INTEGRATION,
            tags=["integration"],
        )

    async def initialize(self) -> None:
        """Initialize the plugin."""
        await self.connect()

    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        await self.disconnect()

    async def connect(self) -> None:
        """Establish connection to external service."""
        # Implement connection logic
        self._connected = True

    async def disconnect(self) -> None:
        """Disconnect from external service."""
        # Implement disconnection logic
        self._connected = False

    async def send_message(self, message: str, **kwargs) -> Any:
        """Send message to external service."""
        if not self._connected:
            raise RuntimeError("Not connected")

        # Implement message sending logic
        return {{"status": "sent", "message": message}}
'''

    else:
        # Generic plugin template
        return f'''"""
{name} - AgentMind Plugin
{description}
"""

from typing import Any, Dict, Optional
from agentmind.plugins.base import Plugin, PluginMetadata, PluginType


class {class_name}(Plugin):
    """Plugin: {name}."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize plugin."""
        super().__init__(config)

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="{name}",
            version="0.1.0",
            description="{description}",
            author="{author}",
            plugin_type=PluginType.{plugin_type.upper()},
            tags=["{plugin_type}"],
        )

    async def initialize(self) -> None:
        """Initialize the plugin."""
        # Add initialization logic here
        pass

    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        # Add cleanup logic here
        pass
'''


@plugin_cli.command()
def list():
    """List all installed plugins."""
    console.print("[bold cyan]Installed Plugins[/bold cyan]\n")

    registry = PluginRegistry()
    manager = PluginManager(registry)
    manager.discover_and_load(auto_load=False)

    plugins = registry.list_plugins()

    if not plugins:
        console.print("[yellow]No plugins found[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Author", style="white")
    table.add_column("Description")

    for metadata in plugins:
        table.add_row(
            metadata.name,
            metadata.version,
            metadata.plugin_type.value,
            metadata.author,
            (
                metadata.description[:50] + "..."
                if len(metadata.description) > 50
                else metadata.description
            ),
        )

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {len(plugins)} plugins")


@plugin_cli.command()
@click.argument("plugin_name")
def info(plugin_name: str):
    """Show detailed information about a plugin."""
    registry = PluginRegistry()
    manager = PluginManager(registry)
    manager.discover_and_load(auto_load=False)

    metadata = registry.get_metadata(plugin_name)

    if not metadata:
        console.print(f"[red]Plugin not found: {plugin_name}[/red]")
        return

    info_text = f"""[bold cyan]{metadata.name}[/bold cyan] v{metadata.version}

[bold]Description:[/bold]
{metadata.description}

[bold]Author:[/bold] {metadata.author}
[bold]Type:[/bold] {metadata.plugin_type.value}
[bold]License:[/bold] {metadata.license or 'Not specified'}

[bold]Tags:[/bold] {', '.join(metadata.tags) if metadata.tags else 'None'}
[bold]Dependencies:[/bold] {', '.join(metadata.dependencies) if metadata.dependencies else 'None'}
"""

    if metadata.homepage:
        info_text += f"\n[bold]Homepage:[/bold] {metadata.homepage}"

    console.print(Panel(info_text, border_style="cyan"))


@plugin_cli.command()
@click.argument("plugin_name")
@click.option("--config", type=click.Path(exists=True), help="Config file path")
def install(plugin_name: str, config: Optional[str]):
    """Install and activate a plugin."""
    console.print(f"[bold cyan]Installing plugin: {plugin_name}[/bold cyan]\n")

    # This would integrate with pip or plugin marketplace
    console.print("[yellow]Note: Plugin installation from marketplace not yet implemented[/yellow]")
    console.print("Use: pip install agentmind-plugin-{plugin_name}")


@plugin_cli.command()
@click.argument("plugin_name")
def uninstall(plugin_name: str):
    """Uninstall a plugin."""
    console.print(f"[bold cyan]Uninstalling plugin: {plugin_name}[/bold cyan]\n")
    console.print("[yellow]Note: Use pip uninstall agentmind-plugin-{plugin_name}[/yellow]")


@plugin_cli.command()
@click.option("--query", help="Search query")
@click.option(
    "--category",
    type=click.Choice(["llm_provider", "memory", "tools", "integration"]),
    help="Filter by category",
)
@click.option("--min-rating", type=float, help="Minimum rating")
def search(query: Optional[str], category: Optional[str], min_rating: Optional[float]):
    """Search for plugins in marketplace."""
    console.print("[bold cyan]Searching Plugins[/bold cyan]\n")

    marketplace = MarketplaceRegistry()

    cat = PluginCategory(category) if category else None
    results = marketplace.search_plugins(query=query, category=cat, min_rating=min_rating)

    if not results:
        console.print("[yellow]No plugins found[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Rating", style="yellow")
    table.add_column("Downloads", style="white")
    table.add_column("Description")

    for manifest in results:
        table.add_row(
            manifest.name,
            manifest.version,
            f"{'⭐' * int(manifest.average_rating)} ({manifest.average_rating:.1f})",
            str(manifest.downloads),
            (
                manifest.description[:40] + "..."
                if len(manifest.description) > 40
                else manifest.description
            ),
        )

    console.print(table)


@plugin_cli.command()
@click.argument("plugin_name")
def test(plugin_name: str):
    """Run tests for a plugin."""
    console.print(f"[bold cyan]Testing plugin: {plugin_name}[/bold cyan]\n")

    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "pytest", f"tests/test_{plugin_name}.py", "-v"],
        capture_output=True,
        text=True,
    )

    console.print(result.stdout)
    if result.returncode != 0:
        console.print(result.stderr, style="red")
        console.print(f"\n[red]Tests failed with exit code {result.returncode}[/red]")
    else:
        console.print("\n[green]✓ All tests passed[/green]")


if __name__ == "__main__":
    plugin_cli()
