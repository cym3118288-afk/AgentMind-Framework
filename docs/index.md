# AgentMind Framework

<div align="center">
  <img src="assets/logo.png" alt="AgentMind Logo" width="200"/>
  <p><strong>The lightest multi-agent framework for Python</strong></p>
  <p>Build collaborative AI systems with minimal code and maximum flexibility</p>
</div>

## Why AgentMind?

Unlike heavyweight frameworks that force you into rigid patterns, AgentMind gives you the essentials:

<div class="grid cards" markdown>

-   :material-feather:{ .lg .middle } **Truly Lightweight**

    ---

    Core framework is <500 lines. No bloat, no vendor lock-in.

-   :material-cloud-outline:{ .lg .middle } **LLM Agnostic**

    ---

    Works with Ollama, OpenAI, Anthropic, or any LiteLLM-supported provider.

-   :material-lightning-bolt:{ .lg .middle } **Async First**

    ---

    Built on asyncio for real concurrent agent collaboration.

-   :material-memory:{ .lg .middle } **Memory Built-in**

    ---

    Conversation history and context management out of the box.

</div>

## Quick Start

Get started in under 2 minutes:

=== "Ollama (Local)"

    ```bash
    # Install Ollama
    curl -fsSL https://ollama.com/install.sh | sh
    ollama pull llama3.2
    
    # Install AgentMind
    pip install agentmind
    ```

=== "OpenAI"

    ```bash
    # Install AgentMind with LiteLLM
    pip install agentmind[full]
    
    # Set API key
    export OPENAI_API_KEY=your-key-here
    ```

=== "Anthropic"

    ```bash
    # Install AgentMind with LiteLLM
    pip install agentmind[full]
    
    # Set API key
    export ANTHROPIC_API_KEY=your-key-here
    ```

### Your First Agent Team

```python
from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
import asyncio

async def main():
    # Initialize with your LLM provider
    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(llm_provider=llm)
    
    # Create specialized agents
    researcher = Agent(
        name="Researcher",
        role="research",
        system_prompt="You are a thorough researcher who finds facts."
    )
    
    writer = Agent(
        name="Writer", 
        role="writer",
        system_prompt="You are a creative writer who crafts engaging content."
    )
    
    # Add agents and collaborate
    mind.add_agent(researcher)
    mind.add_agent(writer)
    
    result = await mind.collaborate(
        "Write a blog post about quantum computing",
        max_rounds=3
    )
    
    print(result)

asyncio.run(main())
```

## Feature Highlights

### Multi-Agent Orchestration

Coordinate multiple AI agents with different roles and expertise:

```python
# Hierarchical coordination
mind = AgentMind(strategy=CollaborationStrategy.HIERARCHICAL)

# Consensus-based decisions
mind = AgentMind(strategy=CollaborationStrategy.CONSENSUS)

# Custom orchestration patterns
mind = AgentMind(strategy=your_custom_strategy)
```

### Flexible LLM Support

Switch between providers seamlessly:

```python
# Local with Ollama
llm = OllamaProvider(model="llama3.2")

# Cloud with OpenAI
llm = LiteLLMProvider(model="gpt-4")

# Cloud with Anthropic
llm = LiteLLMProvider(model="claude-3-opus-20240229")
```

### Tool System

Give agents access to functions and APIs:

```python
from agentmind.tools import tool

@tool(name="calculator", description="Performs calculations")
def calculator(expression: str) -> float:
    return eval(expression)

agent.register_tool(calculator)
```

## Comparison with Other Frameworks

| Feature | AgentMind | CrewAI | LangGraph | AutoGen |
|---------|-----------|--------|-----------|---------|
| Lines of Code | ~500 | ~15K | ~20K | ~25K |
| LLM Agnostic | ✅ | ❌ | ✅ | ✅ |
| Local LLM Support | ✅ | Limited | ✅ | Limited |
| Async Native | ✅ | ❌ | ✅ | ✅ |
| Learning Curve | Low | Medium | High | High |
| Dependencies | Minimal | Heavy | Heavy | Heavy |
| Memory Usage | <50MB | ~200MB | ~300MB | ~250MB |
| Startup Time | <1s | ~5s | ~8s | ~6s |

## Production Ready

AgentMind includes everything you need for production:

- **REST API Server**: Deploy as a microservice
- **CLI Tool**: Command-line interface for quick tasks
- **Web Dashboard**: Visual monitoring and debugging
- **Docker Support**: Container-ready deployment
- **Distributed Execution**: Scale with Celery or Ray
- **Observability**: Built-in tracing and metrics

## Interactive Demo

Try AgentMind in your browser:

<div class="demo-buttons" markdown>
[Launch StackBlitz Demo](https://stackblitz.com/github/cym3118288-afk/AgentMind-Framework){ .md-button .md-button--primary }
[Open in Codespaces](https://github.com/codespaces/new?repo=cym3118288-afk/AgentMind-Framework){ .md-button }
</div>

## Next Steps

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **[Quick Start Guide](getting-started/quickstart.md)**

    ---

    Get up and running in 5 minutes

-   :material-school:{ .lg .middle } **[Tutorials](tutorials/index.md)**

    ---

    Learn through interactive examples

-   :material-book-open:{ .lg .middle } **[API Reference](api/core/agent.md)**

    ---

    Complete API documentation

-   :material-code-braces:{ .lg .middle } **[Examples](examples/index.md)**

    ---

    Production-ready code samples

</div>

## Community

Join our growing community:

- **GitHub Discussions**: Ask questions, share ideas
- **Discord**: Real-time chat and support
- **Twitter**: Latest updates and announcements

<div class="community-buttons" markdown>
[Join Discord](https://discord.gg/agentmind){ .md-button }
[GitHub Discussions](https://github.com/cym3118288-afk/AgentMind-Framework/discussions){ .md-button }
[Follow on Twitter](https://twitter.com/agentmind){ .md-button }
</div>

## Star Us on GitHub

If you find AgentMind useful, please star the repository to help others discover it!

<iframe src="https://ghbtns.com/github-btn.html?user=cym3118288-afk&repo=AgentMind-Framework&type=star&count=true&size=large" frameborder="0" scrolling="0" width="170" height="30" title="GitHub"></iframe>

---

Built with ❤️ by the AgentMind community
