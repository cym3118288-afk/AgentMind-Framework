# Quick Start Guide

Get started with AgentMind in under 5 minutes.

## Installation

Choose your installation method based on your needs:

=== "Basic (Ollama)"

    ```bash
    # Install AgentMind
    pip install agentmind
    
    # Install Ollama for local LLMs
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Pull a model
    ollama pull llama3.2
    ```

=== "Full (All Providers)"

    ```bash
    # Install with all LLM providers
    pip install agentmind[full]
    
    # Set your API key
    export OPENAI_API_KEY=your-key-here
    # or
    export ANTHROPIC_API_KEY=your-key-here
    ```

=== "From Source"

    ```bash
    # Clone the repository
    git clone https://github.com/cym3118288-afk/AgentMind-Framework.git
    cd AgentMind-Framework
    
    # Install in development mode
    pip install -e .
    ```

## Your First Agent

Create a simple agent that responds to queries:

```python
from agentmind import Agent
from agentmind.llm import OllamaProvider

# Create LLM provider
llm = OllamaProvider(model="llama3.2")

# Create an agent
agent = Agent(
    name="Assistant",
    role="helper",
    system_prompt="You are a helpful assistant.",
    llm_provider=llm
)

# Generate a response
response = await agent.generate("What is Python?")
print(response)
```

## Multi-Agent Collaboration

Create a team of agents that work together:

```python
from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
import asyncio

async def main():
    # Initialize
    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(llm_provider=llm)
    
    # Create agents with different roles
    analyst = Agent(
        name="Analyst",
        role="analyst",
        system_prompt="You analyze problems and break them down."
    )
    
    creative = Agent(
        name="Creative",
        role="creative",
        system_prompt="You generate creative solutions."
    )
    
    reviewer = Agent(
        name="Reviewer",
        role="reviewer",
        system_prompt="You review and improve solutions."
    )
    
    # Add agents to the team
    mind.add_agent(analyst)
    mind.add_agent(creative)
    mind.add_agent(reviewer)
    
    # Collaborate on a task
    result = await mind.collaborate(
        task="Design a mobile app for learning languages",
        max_rounds=3
    )
    
    print(result)

# Run the collaboration
asyncio.run(main())
```

## Using the CLI

AgentMind includes a powerful CLI for quick tasks:

```bash
# Run a collaboration from the command line
agentmind run --task "Design a REST API for a todo app" --agents 3

# Use a specific model
agentmind run --task "Analyze this codebase" --model gpt-4 --provider openai

# Save trace for analysis
agentmind run --task "Plan a marketing campaign" --trace-file trace.jsonl

# Analyze a previous collaboration
agentmind analyze trace.jsonl
```

## Web Interface

Start the interactive web interface:

```bash
# Start the chat server
python chat_server.py

# Open http://localhost:5000 in your browser
```

Or use the developer tools dashboard:

```bash
# Start the tools server
python tools_server.py

# Open http://localhost:8001 in your browser
```

## Common Patterns

### Pattern 1: Research Team

```python
async def research_team():
    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(llm_provider=llm)
    
    # Create research team
    researcher = Agent(name="Researcher", role="research")
    analyst = Agent(name="Analyst", role="analysis")
    writer = Agent(name="Writer", role="writing")
    
    mind.add_agent(researcher)
    mind.add_agent(analyst)
    mind.add_agent(writer)
    
    result = await mind.collaborate(
        "Research and write about renewable energy trends",
        max_rounds=5
    )
    return result
```

### Pattern 2: Code Review

```python
async def code_review_team():
    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(llm_provider=llm)
    
    # Create review team
    security = Agent(name="Security", role="security_review")
    performance = Agent(name="Performance", role="performance_review")
    quality = Agent(name="Quality", role="quality_review")
    
    mind.add_agent(security)
    mind.add_agent(performance)
    mind.add_agent(quality)
    
    code = """
    def process_data(data):
        result = []
        for item in data:
            result.append(item * 2)
        return result
    """
    
    result = await mind.collaborate(
        f"Review this code:\n{code}",
        max_rounds=2
    )
    return result
```

### Pattern 3: Customer Support

```python
async def customer_support():
    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(llm_provider=llm)
    
    # Create support team
    classifier = Agent(name="Classifier", role="ticket_classification")
    responder = Agent(name="Responder", role="response_generation")
    qa = Agent(name="QA", role="quality_assurance")
    
    mind.add_agent(classifier)
    mind.add_agent(responder)
    mind.add_agent(qa)
    
    ticket = "My order hasn't arrived and it's been 2 weeks"
    
    result = await mind.collaborate(
        f"Handle this support ticket: {ticket}",
        max_rounds=3
    )
    return result
```

## Configuration

### Environment Variables

```bash
# LLM Provider Settings
export OLLAMA_BASE_URL=http://localhost:11434
export OPENAI_API_KEY=your-key
export ANTHROPIC_API_KEY=your-key

# AgentMind Settings
export AGENTMIND_LOG_LEVEL=INFO
export AGENTMIND_MAX_RETRIES=3
export AGENTMIND_TIMEOUT=30
```

### Configuration File

Create `agentmind.yaml`:

```yaml
llm:
  provider: ollama
  model: llama3.2
  temperature: 0.7
  max_tokens: 2000

agents:
  max_agents: 10
  default_timeout: 30
  
memory:
  backend: in_memory
  max_history: 100

orchestration:
  strategy: round_robin
  max_rounds: 10
```

Load configuration:

```python
from agentmind import AgentMind
from agentmind.config import load_config

config = load_config("agentmind.yaml")
mind = AgentMind.from_config(config)
```

## Next Steps

Now that you have AgentMind running, explore these topics:

- [Basic Concepts](concepts.md) - Understand core concepts
- [Tutorials](../tutorials/index.md) - Step-by-step guides
- [Examples](../examples/index.md) - Production-ready examples
- [API Reference](../api/core/agent.md) - Complete API documentation

## Troubleshooting

### Ollama Connection Issues

If you see "Ollama not available":

1. Check Ollama is running: `ollama list`
2. Verify the base URL: `curl http://localhost:11434/api/tags`
3. Pull a model: `ollama pull llama3.2`

### Import Errors

If you get import errors:

```bash
# Reinstall AgentMind
pip uninstall agentmind
pip install agentmind

# Or install from source
pip install -e .
```

### Performance Issues

For better performance:

1. Use local models with Ollama for faster responses
2. Enable caching for repeated queries
3. Adjust `max_rounds` based on task complexity
4. Use parallel execution for independent tasks

## Getting Help

- [FAQ](../faq.md) - Common questions
- [GitHub Issues](https://github.com/cym3118288-afk/AgentMind-Framework/issues) - Report bugs
- [Discord](https://discord.gg/agentmind) - Community support
- [Discussions](https://github.com/cym3118288-afk/AgentMind-Framework/discussions) - Ask questions
