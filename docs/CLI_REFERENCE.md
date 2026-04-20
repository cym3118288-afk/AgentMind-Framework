# AgentMind CLI Reference

Complete reference for the AgentMind command-line interface.

## Table of Contents

- [Installation](#installation)
- [Global Options](#global-options)
- [Commands](#commands)
  - [init](#init)
  - [run](#run)
  - [agent](#agent)
  - [test](#test)
  - [deploy](#deploy)
  - [benchmark](#benchmark)
  - [config](#config)
  - [plugin](#plugin)
  - [Other Commands](#other-commands)
- [Configuration](#configuration)
- [Examples](#examples)

## Installation

```bash
pip install agentmind
```

## Global Options

Available for all commands:

- `--profile PROFILE` - Use a specific configuration profile
- `--verbose, -v` - Enable verbose output
- `--quiet, -q` - Suppress non-essential output
- `--help` - Show help message

## Commands

### init

Initialize a new AgentMind project with scaffolding wizard.

```bash
agentmind init [OPTIONS]
```

**Options:**

- `--name TEXT` - Project name (prompted if not provided)
- `--description TEXT` - Project description (prompted if not provided)
- `--provider [ollama|openai|anthropic]` - LLM provider (default: ollama)
- `--template [basic|research|development|marketing|custom]` - Project template (default: basic)
- `--interactive/--no-interactive` - Enable/disable interactive mode (default: interactive)

**Examples:**

```bash
# Interactive mode (default)
agentmind init

# Non-interactive with options
agentmind init --name my-project --template research --provider ollama --no-interactive

# Quick start with basic template
agentmind init --name quick-start --template basic
```

**Project Structure Created:**

```
my-project/
├── main.py              # Main entry point
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── README.md           # Project documentation
├── config/
│   └── config.yaml     # Configuration file
├── agents/             # Custom agent definitions
├── tools/              # Custom tools (if enabled)
├── plugins/            # Custom plugins (if enabled)
├── tests/              # Test files
│   └── test_agents.py
└── logs/               # Log files
```

### run

Run a multi-agent collaboration.

```bash
agentmind run [OPTIONS]
```

**Options:**

- `--task, -t TEXT` - Task description (required)
- `--agents, -a INTEGER` - Number of agents (1-5, default: 3)
- `--rounds, -r INTEGER` - Maximum collaboration rounds (default: 5)
- `--provider, -p TEXT` - LLM provider (uses config default)
- `--model, -m TEXT` - LLM model name (uses config default)
- `--temperature FLOAT` - LLM temperature 0.0-2.0 (uses config default)
- `--trace/--no-trace` - Enable/disable tracing (default: enabled)
- `--trace-file PATH` - Save trace to file

**Examples:**

```bash
# Basic usage
agentmind run --task "Design a REST API for a todo app"

# With custom configuration
agentmind run --task "Analyze this codebase" --agents 5 --rounds 10 --provider openai

# Save trace for analysis
agentmind run --task "Plan marketing campaign" --trace-file traces/campaign.jsonl

# Using profile
agentmind --profile production run --task "Deploy application"
```

### agent

Agent management commands.

#### agent create

Create a new agent with interactive builder.

```bash
agentmind agent create [OPTIONS]
```

**Options:**

- `--name TEXT` - Agent name (prompted if not provided)
- `--role TEXT` - Agent role/specialty (prompted if not provided)
- `--system-prompt TEXT` - Custom system prompt
- `--temperature FLOAT` - Temperature setting (default: 0.7)
- `--output PATH` - Save agent code to file
- `--interactive/--no-interactive` - Enable/disable interactive mode (default: interactive)

**Examples:**

```bash
# Interactive mode
agentmind agent create

# Create specific agent
agentmind agent create --name DataAnalyst --role "Data Analysis Expert"

# Save to file
agentmind agent create --name Researcher --role "Research Specialist" --output agents/researcher.py

# With custom prompt
agentmind agent create --name CustomAgent --role "Custom Role" \
  --system-prompt "You are a specialized agent for X"
```

### test

Run agent tests with pytest.

```bash
agentmind test [TEST_PATH] [OPTIONS]
```

**Arguments:**

- `TEST_PATH` - Path to tests (default: tests/)

**Options:**

- `--pattern TEXT` - Test file pattern (default: test_*.py)
- `--verbose, -v` - Verbose test output
- `--coverage` - Run with coverage report
- `--markers TEXT` - Run tests with specific markers

**Examples:**

```bash
# Run all tests
agentmind test

# Run with coverage
agentmind test --coverage

# Run specific test markers
agentmind test --markers integration

# Verbose output
agentmind test --verbose

# Run specific test file
agentmind test tests/test_custom.py
```

### deploy

Deployment helper for AgentMind projects.

```bash
agentmind deploy [OPTIONS]
```

**Options:**

- `--target [docker|kubernetes|aws|local]` - Deployment target (prompted if not provided)
- `--env [dev|staging|production]` - Environment (prompted if not provided)
- `--dry-run` - Show what would be deployed without deploying

**Examples:**

```bash
# Interactive deployment
agentmind deploy

# Deploy to Docker
agentmind deploy --target docker --env production

# Dry run to see what would happen
agentmind deploy --target kubernetes --env staging --dry-run

# Local deployment
agentmind deploy --target local --env dev
```

### benchmark

Run performance benchmarks.

```bash
agentmind benchmark [OPTIONS]
```

**Options:**

- `--iterations INTEGER` - Number of benchmark iterations (default: 10)
- `--agents INTEGER` - Number of agents (default: 3)
- `--task TEXT` - Benchmark task (default: "Analyze this problem")
- `--output PATH` - Save results to JSON file

**Examples:**

```bash
# Basic benchmark
agentmind benchmark

# Custom iterations and agents
agentmind benchmark --iterations 20 --agents 5

# Save results
agentmind benchmark --output results/benchmark_$(date +%Y%m%d).json

# Custom task
agentmind benchmark --task "Complex analysis task" --iterations 15
```

### config

Configuration management commands.

#### config init

Initialize configuration directory.

```bash
agentmind config init
```

Creates `~/.agentmind/config.yaml` with default settings.

#### config show

Show current configuration.

```bash
agentmind config show [OPTIONS]
```

**Options:**

- `--profile TEXT` - Show specific profile

**Examples:**

```bash
# Show current config
agentmind config show

# Show specific profile
agentmind config show --profile production
```

#### config set

Set a configuration value.

```bash
agentmind config set KEY VALUE [OPTIONS]
```

**Options:**

- `--profile TEXT` - Set in specific profile

**Examples:**

```bash
# Set global config
agentmind config set provider openai
agentmind config set model gpt-4
agentmind config set temperature 0.8

# Set in profile
agentmind config set provider anthropic --profile production
```

#### config list-profiles

List all configuration profiles.

```bash
agentmind config list-profiles
```

### plugin

Plugin management commands. See [Plugin CLI Reference](PLUGIN_CLI.md) for details.

```bash
agentmind plugin [COMMAND]
```

**Commands:**

- `create` - Create a new plugin
- `list` - List installed plugins
- `info` - Show plugin information
- `install` - Install a plugin
- `uninstall` - Uninstall a plugin
- `search` - Search plugin marketplace
- `test` - Test a plugin

### Other Commands

#### new

Create a new agent team project (legacy command, use `init` instead).

```bash
agentmind new NAME [OPTIONS]
```

#### example

Run a built-in example.

```bash
agentmind example EXAMPLE_NAME
```

Available examples: research, code-review, customer-support, marketing, data-analysis

#### dashboard

Launch the web dashboard.

```bash
agentmind dashboard
```

#### analyze

Analyze a trace file.

```bash
agentmind analyze TRACE_FILE
```

#### examples

Show example commands and use cases.

```bash
agentmind examples
```

#### version

Show version information.

```bash
agentmind version
```

## Configuration

### Configuration Files

AgentMind uses YAML configuration files stored in `~/.agentmind/`:

- `config.yaml` - Global configuration
- `profiles.yaml` - Named configuration profiles

### Configuration Structure

**config.yaml:**

```yaml
# LLM Settings
provider: ollama
model: llama3.2
temperature: 0.7
max_tokens: 2000

# Collaboration Settings
max_rounds: 10
strategy: sequential
enable_memory: true

# System Settings
max_retries: 3
timeout: 30
log_level: INFO
```

**profiles.yaml:**

```yaml
dev:
  provider: ollama
  model: llama3.2
  temperature: 0.7

staging:
  provider: openai
  model: gpt-3.5-turbo
  temperature: 0.7

production:
  provider: openai
  model: gpt-4
  temperature: 0.5
  max_retries: 5
```

### Environment Variables

Configuration can also be set via environment variables:

```bash
# LLM Settings
export AGENTMIND_PROVIDER=ollama
export AGENTMIND_MODEL=llama3.2
export AGENTMIND_TEMPERATURE=0.7

# API Keys
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# System Settings
export AGENTMIND_LOG_LEVEL=INFO
export AGENTMIND_MAX_RETRIES=3
export AGENTMIND_TIMEOUT=30
```

### Configuration Priority

Configuration is merged in the following order (later overrides earlier):

1. Default values
2. Global config file (`~/.agentmind/config.yaml`)
3. Profile config (if `--profile` specified)
4. Environment variables
5. Command-line options

## Examples

### Complete Workflow

```bash
# 1. Initialize configuration
agentmind config init
agentmind config set provider ollama
agentmind config set model llama3.2

# 2. Create a new project
agentmind init --name research-team --template research

# 3. Navigate to project
cd research-team

# 4. Create custom agents
agentmind agent create --name Researcher --role "Research Specialist" \
  --output agents/researcher.py

agentmind agent create --name Analyst --role "Data Analyst" \
  --output agents/analyst.py

# 5. Run tests
agentmind test --coverage

# 6. Run collaboration
agentmind run --task "Research AI trends in 2024" --agents 3

# 7. Benchmark performance
agentmind benchmark --iterations 10 --output results.json

# 8. Deploy
agentmind deploy --target docker --env production
```

### Using Profiles

```bash
# Create profiles
agentmind config set provider ollama --profile dev
agentmind config set model llama3.2 --profile dev

agentmind config set provider openai --profile prod
agentmind config set model gpt-4 --profile prod

# Use profiles
agentmind --profile dev run --task "Test task"
agentmind --profile prod run --task "Production task"
```

### CI/CD Integration

```bash
# In CI/CD pipeline
export AGENTMIND_PROVIDER=openai
export AGENTMIND_MODEL=gpt-3.5-turbo
export OPENAI_API_KEY=$OPENAI_API_KEY

# Run tests
agentmind test --coverage --markers "not slow"

# Run benchmarks
agentmind benchmark --iterations 5 --output ci-benchmark.json

# Deploy
agentmind deploy --target kubernetes --env staging --dry-run
```

## Tips and Best Practices

1. **Use Profiles**: Create profiles for different environments (dev, staging, prod)
2. **Enable Tracing**: Always use `--trace-file` for important runs to enable debugging
3. **Run Tests**: Use `agentmind test --coverage` regularly to ensure quality
4. **Benchmark**: Run benchmarks before and after changes to track performance
5. **Dry Run**: Always use `--dry-run` first when deploying to production
6. **Version Control**: Commit your project config files but not credentials
7. **Environment Variables**: Use environment variables for sensitive data like API keys

## Troubleshooting

### Command Not Found

```bash
# Ensure agentmind is installed
pip install agentmind

# Or install in development mode
pip install -e .
```

### Configuration Issues

```bash
# Reset configuration
rm -rf ~/.agentmind
agentmind config init

# Check current config
agentmind config show
```

### Test Failures

```bash
# Run with verbose output
agentmind test --verbose

# Run specific test
agentmind test tests/test_specific.py -v
```

## See Also

- [Plugin CLI Reference](PLUGIN_CLI.md)
- [Configuration Guide](CONFIGURATION.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Testing Guide](TESTING.md)
