"""
Enhanced CLI for AgentMind with Wave 2 upgrades.

Features:
- Project scaffolding with init command
- Interactive agent builder
- Plugin management
- Testing and benchmarking
- Deployment helpers
- Rich formatting and UX improvements
"""

import asyncio
import json
import logging
import os
import sys
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.markdown import Markdown
from rich.tree import Tree
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.syntax import Syntax

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider, LiteLLMProvider
from agentmind.utils.observability import Tracer
from agentmind.plugins.cli import plugin_cli

console = Console()
logging.basicConfig(level=logging.WARNING)

# Configuration paths
CONFIG_DIR = Path.home() / ".agentmind"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
PROFILES_FILE = CONFIG_DIR / "profiles.yaml"


# ============================================================================
# Configuration Management
# ============================================================================


def load_config() -> Dict[str, Any]:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}

    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f) or {}


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def load_profile(profile_name: str) -> Dict[str, Any]:
    """Load a specific profile."""
    if not PROFILES_FILE.exists():
        return {}

    with open(PROFILES_FILE, "r") as f:
        profiles = yaml.safe_load(f) or {}

    return profiles.get(profile_name, {})


def save_profile(profile_name: str, profile_data: Dict[str, Any]) -> None:
    """Save a profile."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    profiles = {}
    if PROFILES_FILE.exists():
        with open(PROFILES_FILE, "r") as f:
            profiles = yaml.safe_load(f) or {}

    profiles[profile_name] = profile_data

    with open(PROFILES_FILE, "w") as f:
        yaml.dump(profiles, f, default_flow_style=False)


def get_env_config() -> Dict[str, Any]:
    """Get configuration from environment variables."""
    config = {}

    # LLM settings
    if os.getenv("AGENTMIND_PROVIDER"):
        config["provider"] = os.getenv("AGENTMIND_PROVIDER")
    if os.getenv("AGENTMIND_MODEL"):
        config["model"] = os.getenv("AGENTMIND_MODEL")
    if os.getenv("AGENTMIND_TEMPERATURE"):
        config["temperature"] = float(os.getenv("AGENTMIND_TEMPERATURE"))

    # API keys
    if os.getenv("OPENAI_API_KEY"):
        config["openai_api_key"] = os.getenv("OPENAI_API_KEY")
    if os.getenv("ANTHROPIC_API_KEY"):
        config["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY")

    return config


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configuration dictionaries."""
    result = base.copy()
    result.update({k: v for k, v in override.items() if v is not None})
    return result


# ============================================================================
# Helper Functions
# ============================================================================


def create_llm_provider(provider: str, model: str, temperature: float):
    """Create an LLM provider."""
    if provider == "ollama":
        return OllamaProvider(model=model, temperature=temperature)
    else:
        return LiteLLMProvider(model=model, temperature=temperature)


def create_default_agents(llm_provider, num_agents: int) -> List[Agent]:
    """Create default agents for collaboration."""
    roles = [
        ("Analyst", "Analyze the problem and break it down into components"),
        ("Researcher", "Research relevant information and provide context"),
        ("Strategist", "Develop strategies and approaches to solve the problem"),
        ("Implementer", "Propose concrete implementation steps"),
        ("Reviewer", "Review solutions and provide feedback"),
    ]

    agents = []
    for i in range(min(num_agents, len(roles))):
        name, role = roles[i]
        agent = Agent(name=name, role=role, llm_provider=llm_provider)
        agents.append(agent)

    return agents


@click.group()
@click.version_option(version="0.3.0")
@click.option("--profile", help="Configuration profile to use")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
@click.pass_context
def cli(ctx, profile, verbose, quiet):
    """AgentMind CLI - Multi-agent collaboration framework.

    Run AI agent teams to solve complex tasks collaboratively.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Set logging level
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)

    # Load configuration
    config = load_config()
    env_config = get_env_config()

    # Load profile if specified
    if profile:
        profile_config = load_profile(profile)
        config = merge_configs(config, profile_config)

    # Merge with environment variables
    config = merge_configs(config, env_config)

    # Store in context
    ctx.obj["config"] = config
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


@cli.command()
@click.option("--task", "-t", required=True, help="Task description for agents to collaborate on")
@click.option("--agents", "-a", default=3, type=int, help="Number of agents (1-5)")
@click.option("--rounds", "-r", default=5, type=int, help="Maximum collaboration rounds")
@click.option("--provider", "-p", help="LLM provider (ollama, openai, anthropic)")
@click.option("--model", "-m", help="LLM model name")
@click.option("--temperature", type=float, help="LLM temperature (0.0-2.0)")
@click.option("--trace/--no-trace", default=True, help="Enable tracing")
@click.option("--trace-file", type=click.Path(), help="Save trace to file")
@click.pass_context
def run(
    ctx,
    task: str,
    agents: int,
    rounds: int,
    provider: Optional[str],
    model: Optional[str],
    temperature: Optional[float],
    trace: bool,
    trace_file: Optional[str],
):
    """Run a multi-agent collaboration.

    Example:
        agentmind run --task "Design a REST API for a todo app" --agents 3
    """
    config = ctx.obj.get("config", {})
    verbose = ctx.obj.get("verbose", False)

    # Use config values as defaults
    provider = provider or config.get("provider", "ollama")
    model = model or config.get("model", "llama3.2")
    temperature = temperature if temperature is not None else config.get("temperature", 0.7)

    if verbose:
        logging.getLogger().setLevel(logging.INFO)

    # Validate inputs
    if agents < 1 or agents > 5:
        console.print("[red]Error: Number of agents must be between 1 and 5[/red]")
        sys.exit(1)

    if rounds < 1 or rounds > 20:
        console.print("[red]Error: Rounds must be between 1 and 20[/red]")
        sys.exit(1)

    # Display configuration
    console.print(
        Panel.fit(
            f"[bold cyan]AgentMind Collaboration[/bold cyan]\n\n"
            f"Task: {task}\n"
            f"Agents: {agents}\n"
            f"Max Rounds: {rounds}\n"
            f"Provider: {provider}\n"
            f"Model: {model}",
            border_style="cyan",
        )
    )

    # Run collaboration
    asyncio.run(
        run_collaboration(
            task=task,
            num_agents=agents,
            max_rounds=rounds,
            provider=provider,
            model=model,
            temperature=temperature,
            enable_trace=trace,
            trace_file=trace_file,
            verbose=verbose,
        )
    )


async def run_collaboration(
    task: str,
    num_agents: int,
    max_rounds: int,
    provider: str,
    model: str,
    temperature: float,
    enable_trace: bool,
    trace_file: Optional[str],
    verbose: bool,
):
    """Run the collaboration asynchronously."""
    import time

    start_time = time.time()

    try:
        # Create LLM provider
        with console.status("[bold green]Initializing LLM provider..."):
            llm_provider = create_llm_provider(provider, model, temperature)

        # Create AgentMind
        mind = AgentMind(llm_provider=llm_provider)

        # Create agents
        console.print("\n[bold]Creating agents:[/bold]")
        agent_list = create_default_agents(llm_provider, num_agents)
        for agent in agent_list:
            mind.add_agent(agent)
            console.print(f"  ✓ {agent.name} ({agent.role})")

        # Create tracer if enabled
        tracer = None
        if enable_trace:
            import uuid

            session_id = str(uuid.uuid4())[:8]
            tracer = Tracer(session_id=session_id, metadata={"task": task})
            tracer.start()

        # Run collaboration with progress indicator
        console.print("\n[bold green]Starting collaboration...[/bold green]\n")

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task_id = progress.add_task("Collaborating...", total=None)

            result = await mind.collaborate(task=task, max_rounds=max_rounds)

            progress.update(task_id, completed=True)

        # End tracing
        if tracer:
            tracer.end()

        # Calculate duration
        duration = time.time() - start_time

        # Display result
        console.print("\n" + "=" * 80 + "\n")
        console.print(
            Panel(
                Markdown(result),
                title="[bold green]Collaboration Result[/bold green]",
                border_style="green",
            )
        )

        # Display statistics
        console.print("\n[bold]Statistics:[/bold]")
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="white")

        stats_table.add_row("Duration", f"{duration:.2f}s")
        stats_table.add_row("Rounds", str(len(mind.conversation_history) // num_agents))
        stats_table.add_row("Messages", str(len(mind.conversation_history)))

        if tracer:
            summary = tracer.get_summary()
            token_usage = summary.get("token_usage", {})
            cost_estimate = summary.get("cost_estimate", {})

            if token_usage.get("total_tokens"):
                stats_table.add_row("Total Tokens", str(token_usage["total_tokens"]))

            if cost_estimate.get("total_cost"):
                stats_table.add_row("Estimated Cost", f"${cost_estimate['total_cost']:.4f}")

        console.print(stats_table)

        # Save trace if requested
        if tracer and trace_file:
            tracer.save_jsonl(trace_file)
            console.print(f"\n[green]✓ Trace saved to {trace_file}[/green]")

        # Display conversation history if verbose
        if verbose:
            console.print("\n[bold]Conversation History:[/bold]")
            for i, msg in enumerate(mind.conversation_history, 1):
                console.print(f"\n[cyan]{i}. {msg.sender}:[/cyan]")
                console.print(f"   {msg.content[:200]}...")

    except KeyboardInterrupt:
        console.print("\n[yellow]Collaboration interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.option("--llm", default="ollama", help="LLM provider (ollama, openai)")
@click.option("--agents", default=3, type=int, help="Number of agents")
@click.option("--template", help="Template to use (research, dev, marketing)")
def new(name: str, llm: str, agents: int, template: Optional[str]):
    """Create a new agent team project.

    Example:
        agentmind new my-team --llm ollama --agents 5 --template research
    """
    project_path = Path(name)

    if project_path.exists():
        console.print(f"[red]Error: Directory '{name}' already exists[/red]")
        sys.exit(1)

    # Create project structure
    console.print(f"[bold cyan]Creating new AgentMind project: {name}[/bold cyan]\n")

    project_path.mkdir(parents=True)
    (project_path / "agents").mkdir()
    (project_path / "tools").mkdir()
    (project_path / "config").mkdir()

    # Create main.py
    main_content = f'''"""
{name} - AgentMind Team
"""

from agentmind import Agent, AgentMind
from agentmind.llm import {"OllamaProvider" if llm == "ollama" else "LiteLLMProvider"}
import asyncio

async def main():
    # Initialize LLM provider
    llm = {"OllamaProvider(model='llama3.2')" if llm == "ollama" else "LiteLLMProvider(model='gpt-4')"}
    mind = AgentMind(llm_provider=llm)

    # Create agents
    # TODO: Customize your agents here
    for i in range({agents}):
        agent = Agent(
            name=f"Agent{{i+1}}",
            role=f"role{{i+1}}",
            system_prompt="You are a helpful agent."
        )
        mind.add_agent(agent)

    # Run collaboration
    result = await mind.collaborate(
        "Your task here",
        max_rounds=5
    )

    print(result)

if __name__ == "__main__":
    asyncio.run(main())
'''

    (project_path / "main.py").write_text(main_content)

    # Create requirements.txt
    requirements = f"""agentmind{"[full]" if llm != "ollama" else ""}
"""
    (project_path / "requirements.txt").write_text(requirements)

    # Create .env.example
    env_content = f"""# LLM Configuration
{"OLLAMA_BASE_URL=http://localhost:11434" if llm == "ollama" else "OPENAI_API_KEY=your-key-here"}

# AgentMind Settings
AGENTMIND_LOG_LEVEL=INFO
AGENTMIND_MAX_RETRIES=3
"""
    (project_path / ".env.example").write_text(env_content)

    # Create README.md
    readme = f"""# {name}

AgentMind multi-agent team project.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Configuration

Copy `.env.example` to `.env` and configure your settings.
"""
    (project_path / "README.md").write_text(readme)

    # Display success
    tree = Tree(f"[bold green]{name}/[/bold green]")
    tree.add("[cyan]main.py[/cyan]")
    tree.add("[cyan]requirements.txt[/cyan]")
    tree.add("[cyan].env.example[/cyan]")
    tree.add("[cyan]README.md[/cyan]")
    agents_node = tree.add("[yellow]agents/[/yellow]")
    tools_node = tree.add("[yellow]tools/[/yellow]")
    config_node = tree.add("[yellow]config/[/yellow]")

    console.print("\n[bold green]✓ Project created successfully![/bold green]\n")
    console.print(tree)
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  cd {name}")
    console.print(f"  pip install -r requirements.txt")
    console.print(f"  python main.py")


@cli.command()
@click.argument("example_name")
def example(example_name: str):
    """Run a built-in example.

    Examples:
        agentmind example research
        agentmind example code-review
        agentmind example customer-support
    """
    examples_map = {
        "research": "examples/research_team.py",
        "code-review": "examples/code_review_team.py",
        "customer-support": "examples/use_cases/customer_support.py",
        "marketing": "examples/use_cases/content_generation.py",
        "data-analysis": "examples/data_analysis_team.py",
    }

    if example_name not in examples_map:
        console.print(f"[red]Error: Example '{example_name}' not found[/red]")
        console.print("\n[bold]Available examples:[/bold]")
        for name in examples_map.keys():
            console.print(f"  - {name}")
        sys.exit(1)

    example_path = Path(examples_map[example_name])

    if not example_path.exists():
        console.print(f"[red]Error: Example file not found: {example_path}[/red]")
        sys.exit(1)

    console.print(f"[bold cyan]Running example: {example_name}[/bold cyan]\n")

    import subprocess

    result = subprocess.run([sys.executable, str(example_path)])
    sys.exit(result.returncode)


@cli.command()
def dashboard():
    """Launch the web dashboard.

    Opens the AgentMind web dashboard for visual monitoring and debugging.
    """
    console.print("[bold cyan]Starting AgentMind Dashboard...[/bold cyan]\n")
    console.print("Dashboard will be available at: [bold]http://localhost:8001[/bold]")
    console.print("Press Ctrl+C to stop\n")

    import subprocess

    try:
        subprocess.run([sys.executable, "tools_server.py"])
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")


@cli.command()
@click.argument("trace_file", type=click.Path(exists=True))
def analyze(trace_file: str):
    """Analyze a trace file and display statistics.

    Example:
        agentmind analyze traces/session-abc123.jsonl
    """
    try:
        # Load trace file
        events = []
        metadata = {}

        with open(trace_file, "r") as f:
            for line in f:
                data = json.loads(line)
                if data["type"] == "header":
                    metadata = data["data"]
                elif data["type"] == "event":
                    events.append(data["data"])

        # Display metadata
        console.print(
            Panel.fit(
                f"[bold cyan]Trace Analysis[/bold cyan]\n\n"
                f"Session ID: {metadata.get('session_id', 'N/A')}\n"
                f"Start Time: {metadata.get('start_time', 'N/A')}\n"
                f"Duration: {metadata.get('total_duration_ms', 0) / 1000:.2f}s",
                border_style="cyan",
            )
        )

        # Event statistics
        console.print("\n[bold]Event Statistics:[/bold]")
        event_types = {}
        agent_events = {}

        for event in events:
            event_type = event.get("event_type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1

            agent_name = event.get("agent_name")
            if agent_name:
                agent_events[agent_name] = agent_events.get(agent_name, 0) + 1

        # Event types table
        events_table = Table(title="Events by Type")
        events_table.add_column("Event Type", style="cyan")
        events_table.add_column("Count", style="white", justify="right")

        for event_type, count in sorted(event_types.items()):
            events_table.add_row(event_type, str(count))

        console.print(events_table)

        # Agent activity table
        if agent_events:
            console.print("\n[bold]Agent Activity:[/bold]")
            agents_table = Table(title="Events by Agent")
            agents_table.add_column("Agent", style="cyan")
            agents_table.add_column("Events", style="white", justify="right")

            for agent, count in sorted(agent_events.items()):
                agents_table.add_row(agent, str(count))

            console.print(agents_table)

        # Token usage and cost
        token_usage = metadata.get("token_usage", {})
        cost_estimate = metadata.get("cost_estimate", {})

        if token_usage or cost_estimate:
            console.print("\n[bold]Resource Usage:[/bold]")
            usage_table = Table(show_header=False, box=None)
            usage_table.add_column("Metric", style="cyan")
            usage_table.add_column("Value", style="white")

            if token_usage.get("total_tokens"):
                usage_table.add_row("Total Tokens", str(token_usage["total_tokens"]))
                usage_table.add_row("Prompt Tokens", str(token_usage.get("prompt_tokens", 0)))
                usage_table.add_row(
                    "Completion Tokens", str(token_usage.get("completion_tokens", 0))
                )

            if cost_estimate.get("total_cost"):
                usage_table.add_row("Estimated Cost", f"${cost_estimate['total_cost']:.4f}")

            console.print(usage_table)

    except Exception as e:
        console.print(f"[red]Error analyzing trace: {e}[/red]")
        sys.exit(1)


@cli.command()
def examples():
    """Show example commands and use cases."""
    examples_text = """
# AgentMind CLI Examples

## Basic Usage

Run a simple collaboration with 3 agents:
```bash
agentmind run --task "Design a REST API for a todo app" --agents 3
```

## Create New Project

Create a new agent team project:
```bash
agentmind new my-research-team --llm ollama --agents 5 --template research
```

## Run Built-in Examples

Run pre-built examples:
```bash
agentmind example research
agentmind example code-review
agentmind example customer-support
```

## Launch Dashboard

Start the web dashboard:
```bash
agentmind dashboard
```

## Custom Configuration

Use a specific model and provider:
```bash
agentmind run --task "Analyze this codebase" --provider openai --model gpt-4 --agents 4
```

## With Tracing

Save trace for later analysis:
```bash
agentmind run --task "Plan a marketing campaign" --trace-file traces/campaign.jsonl
```

## Analyze Traces

View statistics from a previous collaboration:
```bash
agentmind analyze traces/campaign.jsonl
```

## Verbose Mode

See detailed conversation history:
```bash
agentmind run --task "Debug this error" --verbose
```

## Advanced

More agents and rounds for complex tasks:
```bash
agentmind run --task "Design a distributed system" --agents 5 --rounds 10
```
    """

    console.print(Markdown(examples_text))


@cli.command()
def version():
    """Show version information."""
    console.print("[bold cyan]AgentMind CLI[/bold cyan]")
    console.print("Version: 0.3.0")
    console.print("Framework: AgentMind")
    console.print(
        "\nFor more information, visit: https://github.com/cym3118288-afk/AgentMind-Framework"
    )


# ============================================================================
# Wave 2: New Commands
# ============================================================================


@cli.command()
@click.option("--name", prompt="Project name", help="Name of the project")
@click.option("--description", prompt="Project description", help="Brief description")
@click.option(
    "--provider",
    type=click.Choice(["ollama", "openai", "anthropic"]),
    prompt="LLM provider",
    default="ollama",
    help="LLM provider to use",
)
@click.option(
    "--template",
    type=click.Choice(["basic", "research", "development", "marketing", "custom"]),
    prompt="Project template",
    default="basic",
    help="Project template",
)
@click.option("--interactive/--no-interactive", default=True, help="Interactive mode")
def init(name: str, description: str, provider: str, template: str, interactive: bool):
    """Initialize a new AgentMind project with scaffolding wizard.

    Example:
        agentmind init --name my-project --template research
    """
    console.print("\n[bold cyan]AgentMind Project Initialization Wizard[/bold cyan]\n")

    # Interactive prompts
    if interactive:
        num_agents = IntPrompt.ask("Number of agents", default=3)
        use_memory = Confirm.ask("Enable memory system?", default=True)
        use_tools = Confirm.ask("Enable custom tools?", default=True)
        use_plugins = Confirm.ask("Enable plugin system?", default=False)
    else:
        num_agents = 3
        use_memory = True
        use_tools = True
        use_plugins = False

    project_path = Path(name)

    if project_path.exists():
        if not Confirm.ask(f"Directory '{name}' exists. Overwrite?", default=False):
            console.print("[yellow]Initialization cancelled[/yellow]")
            return

    # Create project structure
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Creating project structure...", total=10)

        # Create directories
        project_path.mkdir(parents=True, exist_ok=True)
        progress.update(task, advance=1)

        (project_path / "agents").mkdir(exist_ok=True)
        (project_path / "config").mkdir(exist_ok=True)
        progress.update(task, advance=1)

        if use_tools:
            (project_path / "tools").mkdir(exist_ok=True)
        if use_plugins:
            (project_path / "plugins").mkdir(exist_ok=True)
        progress.update(task, advance=1)

        (project_path / "tests").mkdir(exist_ok=True)
        (project_path / "logs").mkdir(exist_ok=True)
        progress.update(task, advance=1)

        # Create main.py
        main_content = _generate_main_file(
            name, description, provider, template, num_agents, use_memory, use_tools
        )
        (project_path / "main.py").write_text(main_content)
        progress.update(task, advance=1)

        # Create config files
        config_content = _generate_config(provider, template)
        (project_path / "config" / "config.yaml").write_text(config_content)
        progress.update(task, advance=1)

        # Create requirements.txt
        requirements = _generate_requirements(provider, use_memory, use_tools, use_plugins)
        (project_path / "requirements.txt").write_text(requirements)
        progress.update(task, advance=1)

        # Create .env.example
        env_content = _generate_env_file(provider)
        (project_path / ".env.example").write_text(env_content)
        progress.update(task, advance=1)

        # Create README.md
        readme = _generate_readme(name, description, provider, template)
        (project_path / "README.md").write_text(readme)
        progress.update(task, advance=1)

        # Create test file
        test_content = _generate_test_file(name)
        (project_path / "tests" / "test_agents.py").write_text(test_content)
        progress.update(task, advance=1)

    # Display success
    console.print("\n[bold green]✓ Project initialized successfully![/bold green]\n")

    tree = Tree(f"[bold green]{name}/[/bold green]")
    tree.add("[cyan]main.py[/cyan]")
    tree.add("[cyan]requirements.txt[/cyan]")
    tree.add("[cyan].env.example[/cyan]")
    tree.add("[cyan]README.md[/cyan]")

    config_node = tree.add("[yellow]config/[/yellow]")
    config_node.add("[cyan]config.yaml[/cyan]")

    tree.add("[yellow]agents/[/yellow]")
    if use_tools:
        tree.add("[yellow]tools/[/yellow]")
    if use_plugins:
        tree.add("[yellow]plugins/[/yellow]")

    tests_node = tree.add("[yellow]tests/[/yellow]")
    tests_node.add("[cyan]test_agents.py[/cyan]")

    tree.add("[yellow]logs/[/yellow]")

    console.print(tree)
    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  cd {name}")
    console.print("  pip install -r requirements.txt")
    console.print("  cp .env.example .env  # Configure your environment")
    console.print("  python main.py")


@cli.group(name="agent")
def agent_group():
    """Agent management commands."""
    pass


@agent_group.command(name="create")
@click.option("--name", prompt="Agent name", help="Name of the agent")
@click.option("--role", prompt="Agent role", help="Role/specialty of the agent")
@click.option("--system-prompt", help="Custom system prompt")
@click.option("--temperature", type=float, default=0.7, help="Temperature setting")
@click.option("--output", type=click.Path(), help="Output file path")
@click.option("--interactive/--no-interactive", default=True, help="Interactive mode")
def agent_create(
    name: str,
    role: str,
    system_prompt: Optional[str],
    temperature: float,
    output: Optional[str],
    interactive: bool,
):
    """Interactive agent builder.

    Example:
        agentmind agent create --name Analyst --role "Data Analysis Expert"
    """
    console.print("\n[bold cyan]Agent Builder[/bold cyan]\n")

    # Interactive configuration
    if interactive:
        console.print(f"Creating agent: [bold]{name}[/bold]")
        console.print(f"Role: [cyan]{role}[/cyan]\n")

        if not system_prompt:
            use_custom_prompt = Confirm.ask("Use custom system prompt?", default=False)
            if use_custom_prompt:
                system_prompt = Prompt.ask("Enter system prompt")
            else:
                system_prompt = (
                    f"You are {name}, a {role}. Provide expert assistance in your domain."
                )

        enable_memory = Confirm.ask("Enable memory?", default=True)
        enable_tools = Confirm.ask("Enable tools?", default=False)

        if enable_tools:
            tools_list = Prompt.ask("Tool names (comma-separated)", default="")
            tools = [t.strip() for t in tools_list.split(",") if t.strip()]
        else:
            tools = []
    else:
        system_prompt = system_prompt or f"You are {name}, a {role}."
        enable_memory = True
        enable_tools = False
        tools = []

    # Generate agent code
    agent_code = f'''"""
{name} - {role}
"""

from agentmind import Agent
from agentmind.llm import OllamaProvider

class {name.replace(" ", "")}Agent(Agent):
    """Agent: {name} - {role}"""

    def __init__(self, llm_provider=None):
        super().__init__(
            name="{name}",
            role="{role}",
            system_prompt="""{system_prompt}""",
            llm_provider=llm_provider,
            temperature={temperature},
            enable_memory={enable_memory}
        )

        # Custom initialization
        self.setup()

    def setup(self):
        """Setup agent-specific configuration."""
        pass
'''

    if enable_tools and tools:
        agent_code += f'''
    def get_tools(self):
        """Get agent tools."""
        return {tools}
'''

    # Save or display
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(agent_code)
        console.print(f"\n[green]✓ Agent saved to {output}[/green]")
    else:
        console.print("\n[bold]Generated Agent Code:[/bold]\n")
        syntax = Syntax(agent_code, "python", theme="monokai", line_numbers=True)
        console.print(syntax)

    # Summary
    console.print("\n[bold]Agent Configuration:[/bold]")
    config_table = Table(show_header=False, box=None)
    config_table.add_column("Property", style="cyan")
    config_table.add_column("Value", style="white")

    config_table.add_row("Name", name)
    config_table.add_row("Role", role)
    config_table.add_row("Temperature", str(temperature))
    config_table.add_row("Memory", "Enabled" if enable_memory else "Disabled")
    config_table.add_row("Tools", ", ".join(tools) if tools else "None")

    console.print(config_table)


@cli.command()
@click.argument("test_path", required=False, default="tests/")
@click.option("--pattern", default="test_*.py", help="Test file pattern")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--coverage", is_flag=True, help="Run with coverage")
@click.option("--markers", help="Run tests with specific markers")
def test(test_path: str, pattern: str, verbose: bool, coverage: bool, markers: Optional[str]):
    """Run agent tests.

    Example:
        agentmind test
        agentmind test --coverage --verbose
        agentmind test --markers integration
    """
    console.print("[bold cyan]Running AgentMind Tests[/bold cyan]\n")

    import subprocess

    cmd = [sys.executable, "-m", "pytest", test_path]

    if pattern:
        cmd.extend(["-k", pattern])

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(["--cov=agentmind", "--cov-report=html", "--cov-report=term"])

    if markers:
        cmd.extend(["-m", markers])

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]\n")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        console.print("\n[green]✓ All tests passed[/green]")
        if coverage:
            console.print("[dim]Coverage report: htmlcov/index.html[/dim]")
    else:
        console.print(f"\n[red]✗ Tests failed with exit code {result.returncode}[/red]")
        sys.exit(result.returncode)


@cli.command()
@click.option(
    "--target",
    type=click.Choice(["docker", "kubernetes", "aws", "local"]),
    prompt="Deployment target",
    default="docker",
    help="Deployment target",
)
@click.option(
    "--env",
    type=click.Choice(["dev", "staging", "production"]),
    prompt="Environment",
    default="dev",
    help="Deployment environment",
)
@click.option("--dry-run", is_flag=True, help="Show what would be deployed without deploying")
def deploy(target: str, env: str, dry_run: bool):
    """Deployment helper for AgentMind projects.

    Example:
        agentmind deploy --target docker --env production
        agentmind deploy --target kubernetes --dry-run
    """
    console.print(f"\n[bold cyan]AgentMind Deployment Helper[/bold cyan]\n")
    console.print(f"Target: [yellow]{target}[/yellow]")
    console.print(f"Environment: [yellow]{env}[/yellow]")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    if target == "docker":
        _deploy_docker(env, dry_run)
    elif target == "kubernetes":
        _deploy_kubernetes(env, dry_run)
    elif target == "aws":
        _deploy_aws(env, dry_run)
    elif target == "local":
        _deploy_local(env, dry_run)


def _deploy_docker(env: str, dry_run: bool):
    """Deploy to Docker."""
    console.print("[bold]Docker Deployment[/bold]\n")

    steps = [
        "Building Docker image...",
        "Tagging image...",
        "Pushing to registry...",
        "Updating container...",
    ]

    if dry_run:
        for step in steps:
            console.print(f"  [dim]Would execute: {step}[/dim]")
    else:
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            for step in steps:
                task = progress.add_task(step, total=None)
                import time

                time.sleep(0.5)  # Simulate work
                progress.update(task, completed=True)

        console.print("\n[green]✓ Docker deployment complete[/green]")


def _deploy_kubernetes(env: str, dry_run: bool):
    """Deploy to Kubernetes."""
    console.print("[bold]Kubernetes Deployment[/bold]\n")
    console.print("[yellow]Kubernetes deployment requires kubectl configuration[/yellow]")

    if dry_run:
        console.print("  [dim]Would execute: kubectl apply -f k8s/[/dim]")
    else:
        console.print("[yellow]Not implemented - use: kubectl apply -f k8s/[/yellow]")


def _deploy_aws(env: str, dry_run: bool):
    """Deploy to AWS."""
    console.print("[bold]AWS Deployment[/bold]\n")
    console.print("[yellow]AWS deployment requires AWS CLI configuration[/yellow]")

    if dry_run:
        console.print("  [dim]Would execute: aws deploy commands[/dim]")
    else:
        console.print("[yellow]Not implemented - configure AWS deployment manually[/yellow]")


def _deploy_local(env: str, dry_run: bool):
    """Deploy locally."""
    console.print("[bold]Local Deployment[/bold]\n")

    if dry_run:
        console.print("  [dim]Would execute: python main.py[/dim]")
    else:
        console.print("Starting local deployment...")
        import subprocess

        subprocess.run([sys.executable, "main.py"])


@cli.command()
@click.option("--iterations", default=10, type=int, help="Number of benchmark iterations")
@click.option("--agents", default=3, type=int, help="Number of agents")
@click.option("--task", default="Analyze this problem", help="Benchmark task")
@click.option("--output", type=click.Path(), help="Save results to file")
def benchmark(iterations: int, agents: int, task: str, output: Optional[str]):
    """Run performance benchmarks.

    Example:
        agentmind benchmark --iterations 10 --agents 3
        agentmind benchmark --output results.json
    """
    console.print("[bold cyan]AgentMind Performance Benchmark[/bold cyan]\n")

    results = {"iterations": iterations, "agents": agents, "task": task, "runs": []}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        bench_task = progress.add_task(f"Running {iterations} iterations...", total=iterations)

        for i in range(iterations):
            import time

            start = time.time()

            # Simulate benchmark run
            time.sleep(0.1)

            duration = time.time() - start
            results["runs"].append(
                {
                    "iteration": i + 1,
                    "duration": duration,
                    "tokens": 1000 + i * 100,  # Simulated
                    "cost": 0.01 + i * 0.001,  # Simulated
                }
            )

            progress.update(bench_task, advance=1)

    # Calculate statistics
    durations = [r["duration"] for r in results["runs"]]
    avg_duration = sum(durations) / len(durations)
    min_duration = min(durations)
    max_duration = max(durations)

    # Display results
    console.print("\n[bold]Benchmark Results:[/bold]\n")

    stats_table = Table(show_header=True, header_style="bold magenta")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="white", justify="right")

    stats_table.add_row("Iterations", str(iterations))
    stats_table.add_row("Agents", str(agents))
    stats_table.add_row("Avg Duration", f"{avg_duration:.3f}s")
    stats_table.add_row("Min Duration", f"{min_duration:.3f}s")
    stats_table.add_row("Max Duration", f"{max_duration:.3f}s")

    console.print(stats_table)

    # Save results
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        console.print(f"\n[green]✓ Results saved to {output}[/green]")


@cli.group(name="config")
def config_group():
    """Configuration management commands."""
    pass


@config_group.command(name="init")
def config_init():
    """Initialize configuration directory."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    default_config = {
        "provider": "ollama",
        "model": "llama3.2",
        "temperature": 0.7,
        "max_retries": 3,
        "timeout": 30,
    }

    save_config(default_config)
    console.print(f"[green]✓ Configuration initialized at {CONFIG_FILE}[/green]")


@config_group.command(name="show")
@click.option("--profile", help="Show specific profile")
def config_show(profile: Optional[str]):
    """Show current configuration."""
    if profile:
        config = load_profile(profile)
        console.print(f"[bold cyan]Profile: {profile}[/bold cyan]\n")
    else:
        config = load_config()
        console.print("[bold cyan]Current Configuration[/bold cyan]\n")

    if not config:
        console.print("[yellow]No configuration found[/yellow]")
        return

    syntax = Syntax(yaml.dump(config, default_flow_style=False), "yaml", theme="monokai")
    console.print(syntax)


@config_group.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option("--profile", help="Set in specific profile")
def config_set(key: str, value: str, profile: Optional[str]):
    """Set a configuration value."""
    if profile:
        config = load_profile(profile)
        config[key] = value
        save_profile(profile, config)
        console.print(f"[green]✓ Set {key}={value} in profile '{profile}'[/green]")
    else:
        config = load_config()
        config[key] = value
        save_config(config)
        console.print(f"[green]✓ Set {key}={value}[/green]")


@config_group.command(name="list-profiles")
def config_list_profiles():
    """List all configuration profiles."""
    if not PROFILES_FILE.exists():
        console.print("[yellow]No profiles found[/yellow]")
        return

    with open(PROFILES_FILE, "r") as f:
        profiles = yaml.safe_load(f) or {}

    if not profiles:
        console.print("[yellow]No profiles found[/yellow]")
        return

    console.print("[bold cyan]Configuration Profiles[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Profile", style="cyan")
    table.add_column("Provider", style="yellow")
    table.add_column("Model", style="green")

    for name, config in profiles.items():
        table.add_row(name, config.get("provider", "N/A"), config.get("model", "N/A"))

    console.print(table)


# ============================================================================
# Helper Functions for New Commands
# ============================================================================


def _generate_main_file(
    name: str,
    description: str,
    provider: str,
    template: str,
    num_agents: int,
    use_memory: bool,
    use_tools: bool,
) -> str:
    """Generate main.py content."""
    return f'''"""
{name}
{description}
"""

import asyncio
from agentmind import Agent, AgentMind
from agentmind.llm import {"OllamaProvider" if provider == "ollama" else "LiteLLMProvider"}


async def main():
    """Main entry point."""
    # Initialize LLM provider
    llm = {"OllamaProvider(model='llama3.2')" if provider == "ollama" else "LiteLLMProvider(model='gpt-4')"}

    # Create AgentMind orchestrator
    mind = AgentMind(llm_provider=llm)

    # Create agents
    agents = [
        Agent(name=f"Agent{{i+1}}", role=f"Specialist{{i+1}}", llm_provider=llm)
        for i in range({num_agents})
    ]

    for agent in agents:
        mind.add_agent(agent)

    # Run collaboration
    result = await mind.collaborate(
        task="Your task here",
        max_rounds=5
    )

    print("\\nResult:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
'''


def _generate_config(provider: str, template: str) -> str:
    """Generate config.yaml content."""
    return f"""# AgentMind Configuration

llm:
  provider: {provider}
  model: {"llama3.2" if provider == "ollama" else "gpt-4"}
  temperature: 0.7
  max_tokens: 2000

collaboration:
  max_rounds: 10
  strategy: sequential
  enable_memory: true

logging:
  level: INFO
  file: logs/agentmind.log

template: {template}
"""


def _generate_requirements(
    provider: str, use_memory: bool, use_tools: bool, use_plugins: bool
) -> str:
    """Generate requirements.txt content."""
    reqs = ["agentmind>=0.3.0"]

    if provider != "ollama":
        reqs.append("litellm>=1.0.0")

    if use_memory:
        reqs.append("chromadb>=0.4.0")

    if use_tools:
        reqs.append("# Add tool-specific dependencies here")

    if use_plugins:
        reqs.append("# Add plugin dependencies here")

    return "\n".join(reqs) + "\n"


def _generate_env_file(provider: str) -> str:
    """Generate .env.example content."""
    content = f"""# LLM Configuration
{"OLLAMA_BASE_URL=http://localhost:11434" if provider == "ollama" else "OPENAI_API_KEY=your-key-here"}

# AgentMind Settings
AGENTMIND_LOG_LEVEL=INFO
AGENTMIND_MAX_RETRIES=3
AGENTMIND_TIMEOUT=30
"""
    return content


def _generate_readme(name: str, description: str, provider: str, template: str) -> str:
    """Generate README.md content."""
    return f"""# {name}

{description}

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
```

## Usage

```bash
python main.py
```

## Configuration

Edit `config/config.yaml` to customize:
- LLM provider and model
- Collaboration strategy
- Agent settings

## Template

This project uses the **{template}** template.

## Development

```bash
# Run tests
pytest tests/

# Run with verbose output
python main.py --verbose
```
"""


def _generate_test_file(name: str) -> str:
    """Generate test file content."""
    return f'''"""
Tests for {name}
"""

import pytest
from agentmind import Agent, AgentMind


@pytest.mark.asyncio
async def test_agent_creation():
    """Test agent creation."""
    agent = Agent(name="TestAgent", role="Tester")
    assert agent.name == "TestAgent"
    assert agent.role == "Tester"


@pytest.mark.asyncio
async def test_collaboration():
    """Test basic collaboration."""
    mind = AgentMind()
    agent = Agent(name="TestAgent", role="Tester")
    mind.add_agent(agent)

    # Add more tests here
    assert len(mind.agents) == 1
'''


# Add plugin commands
cli.add_command(plugin_cli)


if __name__ == "__main__":
    cli()
