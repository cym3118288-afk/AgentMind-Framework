# AgentMind CLI Tutorial

A hands-on tutorial for getting started with the AgentMind CLI.

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Basic understanding of command-line interfaces

## Installation

```bash
pip install agentmind
```

Verify installation:

```bash
agentmind --help
```

## Tutorial Overview

This tutorial covers:

1. Setting up your environment
2. Creating your first project
3. Building custom agents
4. Running collaborations
5. Testing and benchmarking
6. Deployment

## Part 1: Initial Setup

### Step 1: Initialize Configuration

First, let's set up the global configuration:

```bash
# Initialize config directory
agentmind config init

# Set your preferred LLM provider
agentmind config set provider ollama

# Set the model
agentmind config set model llama3.2

# Set temperature
agentmind config set temperature 0.7
```

Verify your configuration:

```bash
agentmind config show
```

### Step 2: Create Configuration Profiles

Create profiles for different environments:

```bash
# Development profile (local, fast)
agentmind config set provider ollama --profile dev
agentmind config set model llama3.2 --profile dev
agentmind config set temperature 0.7 --profile dev

# Production profile (cloud, powerful)
agentmind config set provider openai --profile prod
agentmind config set model gpt-4 --profile prod
agentmind config set temperature 0.5 --profile prod
```

List your profiles:

```bash
agentmind config list-profiles
```

## Part 2: Creating Your First Project

### Step 3: Initialize a New Project

Let's create a research team project:

```bash
agentmind init
```

Follow the interactive prompts:

```
Project name: research-team
Project description: AI research collaboration team
LLM provider: ollama
Project template: research
Number of agents: 3
Enable memory system? Yes
Enable custom tools? Yes
Enable plugin system? No
```

Navigate to your project:

```bash
cd research-team
ls -la
```

You should see:

```
research-team/
├── main.py
├── requirements.txt
├── .env.example
├── README.md
├── config/
│   └── config.yaml
├── agents/
├── tools/
├── tests/
│   └── test_agents.py
└── logs/
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

## Part 3: Building Custom Agents

### Step 6: Create a Research Agent

```bash
agentmind agent create
```

Interactive prompts:

```
Agent name: ResearchLead
Agent role: Research Team Leader
Use custom system prompt? Yes
Enter system prompt: You are a research team leader specializing in AI and machine learning. 
Your role is to coordinate research efforts, identify key questions, and synthesize findings.
Enable memory? Yes
Enable tools? Yes
Tool names (comma-separated): web_search, arxiv_search
```

Save the output:

```bash
agentmind agent create \
  --name ResearchLead \
  --role "Research Team Leader" \
  --output agents/research_lead.py \
  --no-interactive
```

### Step 7: Create Additional Agents

Create a data analyst agent:

```bash
agentmind agent create \
  --name DataAnalyst \
  --role "Data Analysis Expert" \
  --output agents/data_analyst.py \
  --temperature 0.6 \
  --no-interactive
```

Create a writer agent:

```bash
agentmind agent create \
  --name TechnicalWriter \
  --role "Technical Documentation Specialist" \
  --output agents/technical_writer.py \
  --temperature 0.8 \
  --no-interactive
```

### Step 8: Review Generated Agents

```bash
cat agents/research_lead.py
```

## Part 4: Running Collaborations

### Step 9: Quick Test Run

Run a simple collaboration:

```bash
agentmind run --task "What are the latest trends in AI for 2024?" --agents 3
```

### Step 10: Run with Tracing

Enable tracing to analyze the collaboration:

```bash
agentmind run \
  --task "Analyze the impact of large language models on software development" \
  --agents 3 \
  --rounds 5 \
  --trace-file traces/llm-impact-$(date +%Y%m%d).jsonl
```

### Step 11: Analyze the Trace

```bash
agentmind analyze traces/llm-impact-*.jsonl
```

This shows:
- Event statistics
- Agent activity
- Token usage
- Cost estimates

### Step 12: Run with Different Profiles

Development run (fast, local):

```bash
agentmind --profile dev run \
  --task "Quick research on transformer architectures" \
  --agents 2 \
  --rounds 3
```

Production run (powerful, cloud):

```bash
agentmind --profile prod run \
  --task "Comprehensive analysis of AI safety research" \
  --agents 5 \
  --rounds 10 \
  --trace-file traces/ai-safety-prod.jsonl
```

## Part 5: Testing

### Step 13: Write Tests

Edit `tests/test_agents.py`:

```python
import pytest
from agentmind import Agent, AgentMind


@pytest.mark.asyncio
async def test_research_lead():
    """Test research lead agent."""
    agent = Agent(name="ResearchLead", role="Research Team Leader")
    assert agent.name == "ResearchLead"
    assert agent.role == "Research Team Leader"


@pytest.mark.asyncio
async def test_collaboration():
    """Test basic collaboration."""
    mind = AgentMind()
    
    agents = [
        Agent(name="Researcher", role="Researcher"),
        Agent(name="Analyst", role="Analyst"),
    ]
    
    for agent in agents:
        mind.add_agent(agent)
    
    assert len(mind.agents) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_collaboration():
    """Test full collaboration flow."""
    mind = AgentMind()
    
    agents = [
        Agent(name="Agent1", role="Role1"),
        Agent(name="Agent2", role="Role2"),
    ]
    
    for agent in agents:
        mind.add_agent(agent)
    
    # This would run actual collaboration
    # result = await mind.collaborate("Test task", max_rounds=2)
    # assert result is not None
```

### Step 14: Run Tests

Run all tests:

```bash
agentmind test
```

Run with coverage:

```bash
agentmind test --coverage
```

Run only unit tests:

```bash
agentmind test --markers unit
```

Run with verbose output:

```bash
agentmind test --verbose
```

### Step 15: View Coverage Report

```bash
# Open coverage report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Part 6: Benchmarking

### Step 16: Run Basic Benchmark

```bash
agentmind benchmark --iterations 10 --agents 3
```

### Step 17: Run Comprehensive Benchmark

```bash
agentmind benchmark \
  --iterations 20 \
  --agents 5 \
  --task "Complex multi-step analysis task" \
  --output benchmarks/baseline-$(date +%Y%m%d).json
```

### Step 18: Compare Benchmarks

Run benchmark before optimization:

```bash
agentmind benchmark --iterations 10 --output benchmarks/before.json
```

Make optimizations to your code, then run again:

```bash
agentmind benchmark --iterations 10 --output benchmarks/after.json
```

Compare results:

```bash
# View results
cat benchmarks/before.json
cat benchmarks/after.json
```

## Part 7: Deployment

### Step 19: Test Deployment (Dry Run)

```bash
agentmind deploy --target docker --env staging --dry-run
```

### Step 20: Deploy to Docker

First, ensure you have a Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Deploy:

```bash
agentmind deploy --target docker --env production
```

### Step 21: Deploy Locally

For testing:

```bash
agentmind deploy --target local --env dev
```

## Part 8: Advanced Usage

### Step 22: Plugin Management

List available plugins:

```bash
agentmind plugin list
```

Search for plugins:

```bash
agentmind plugin search --query "memory"
```

Create a custom plugin:

```bash
agentmind plugin create my-tool --type tool --author "Your Name"
```

### Step 23: Using the Dashboard

Launch the web dashboard:

```bash
agentmind dashboard
```

Open http://localhost:8001 in your browser.

### Step 24: Running Examples

Explore built-in examples:

```bash
# List available examples
agentmind examples

# Run research example
agentmind example research

# Run code review example
agentmind example code-review
```

## Part 9: Best Practices

### Organizing Your Project

```
my-project/
├── agents/              # Custom agent definitions
│   ├── __init__.py
│   ├── researcher.py
│   ├── analyst.py
│   └── writer.py
├── tools/               # Custom tools
│   ├── __init__.py
│   ├── web_search.py
│   └── data_processor.py
├── config/              # Configuration files
│   ├── config.yaml
│   ├── dev.yaml
│   └── prod.yaml
├── tests/               # Test files
│   ├── test_agents.py
│   ├── test_tools.py
│   └── test_integration.py
├── traces/              # Trace files
├── benchmarks/          # Benchmark results
├── logs/                # Log files
├── main.py              # Main entry point
├── requirements.txt     # Dependencies
├── .env                 # Environment variables (gitignored)
├── .env.example         # Environment template
└── README.md            # Documentation
```

### Configuration Management

Create a `.agentmind.yaml` in your project root:

```yaml
# Project-specific configuration
project:
  name: research-team
  version: 1.0.0

agents:
  default_temperature: 0.7
  max_agents: 5

collaboration:
  default_rounds: 5
  strategy: sequential

logging:
  level: INFO
  file: logs/agentmind.log
```

### Version Control

Create a `.gitignore`:

```
# Environment
.env
*.env

# Logs
logs/
*.log

# Traces
traces/
*.jsonl

# Benchmarks
benchmarks/*.json

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
```

## Part 10: Troubleshooting

### Common Issues

**Issue: Command not found**

```bash
# Solution: Ensure agentmind is in PATH
pip install --user agentmind
# Or use full path
python -m agentmind --help
```

**Issue: Configuration not loading**

```bash
# Solution: Check config file
agentmind config show

# Reinitialize if needed
rm -rf ~/.agentmind
agentmind config init
```

**Issue: Tests failing**

```bash
# Solution: Run with verbose output
agentmind test --verbose

# Check specific test
agentmind test tests/test_specific.py -v
```

**Issue: Deployment fails**

```bash
# Solution: Use dry-run first
agentmind deploy --target docker --env prod --dry-run

# Check logs
cat logs/agentmind.log
```

## Next Steps

Now that you've completed the tutorial, you can:

1. **Explore Advanced Features**: Check out the [CLI Reference](CLI_REFERENCE.md)
2. **Build Custom Plugins**: See [Plugin Development Guide](PLUGIN_DEVELOPMENT.md)
3. **Optimize Performance**: Read [Performance Guide](PERFORMANCE.md)
4. **Deploy to Production**: Follow [Deployment Guide](DEPLOYMENT.md)
5. **Join the Community**: Visit [GitHub Discussions](https://github.com/cym3118288-afk/AgentMind-Framework/discussions)

## Additional Resources

- [CLI Reference](CLI_REFERENCE.md) - Complete command reference
- [API Documentation](API.md) - Python API documentation
- [Examples](../examples/) - Code examples
- [FAQ](FAQ.md) - Frequently asked questions
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

## Feedback

Have questions or suggestions? Please:

- Open an issue on [GitHub](https://github.com/cym3118288-afk/AgentMind-Framework/issues)
- Join our [Discord community](https://discord.gg/agentmind)
- Check the [FAQ](FAQ.md)

Happy building with AgentMind!
