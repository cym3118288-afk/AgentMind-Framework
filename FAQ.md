# Frequently Asked Questions (FAQ)

Common questions and answers about AgentMind.

## Table of Contents

- [General Questions](#general-questions)
- [Installation & Setup](#installation--setup)
- [Usage & Development](#usage--development)
- [LLM Providers](#llm-providers)
- [Performance & Optimization](#performance--optimization)
- [Troubleshooting](#troubleshooting)
- [Comparison with Other Frameworks](#comparison-with-other-frameworks)
- [Contributing & Community](#contributing--community)

## General Questions

### What is AgentMind?

AgentMind is a lightweight, LLM-agnostic multi-agent framework for Python. It enables you to build collaborative AI systems where multiple specialized agents work together to solve complex tasks.

### Why choose AgentMind over other frameworks?

- **Truly Lightweight**: Core framework is under 500 lines of code
- **LLM Agnostic**: Works with any LLM provider (Ollama, OpenAI, Anthropic, etc.)
- **Local-First**: Full support for local models via Ollama
- **Async Native**: Built on asyncio for true concurrent execution
- **No Vendor Lock-in**: Not tied to any specific LLM provider
- **Easy to Learn**: Simple API, minimal concepts to master

### What can I build with AgentMind?

- Research and analysis systems
- Content generation pipelines
- Code review automation
- Customer support systems
- Data analysis teams
- Financial analysis tools
- E-commerce recommendations
- And much more!

### Is AgentMind production-ready?

Yes! AgentMind includes:
- Comprehensive test suite (340+ tests, 93%+ coverage)
- Type hints throughout
- Error handling and retry mechanisms
- REST API server
- Docker support
- Observability and monitoring tools

## Installation & Setup

### How do I install AgentMind?

```bash
# From source
git clone https://github.com/cym3118288-afk/AgentMind.git
cd AgentMind
pip install -e .
```

### What are the system requirements?

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- For local LLMs: 8GB+ RAM depending on model size

### Do I need an API key?

It depends on your LLM provider:
- **Ollama (local)**: No API key needed
- **OpenAI**: Requires `OPENAI_API_KEY`
- **Anthropic**: Requires `ANTHROPIC_API_KEY`
- **Other providers**: Check LiteLLM documentation

### How do I set up Ollama for local models?

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2

# Use in AgentMind
from agentmind.llm import OllamaProvider
llm = OllamaProvider(model="llama3.2")
```

### Can I use multiple LLM providers in one application?

Yes! Each agent can use a different LLM provider:

```python
ollama_llm = OllamaProvider(model="llama3.2")
openai_llm = LiteLLMProvider(model="gpt-4")

agent1 = Agent(name="Local", llm_provider=ollama_llm)
agent2 = Agent(name="Cloud", llm_provider=openai_llm)
```

## Usage & Development

### How do I create a basic agent?

```python
from agentmind import Agent

agent = Agent(
    name="Assistant",
    role="helper",
    system_prompt="You are a helpful assistant."
)
```

### How do agents collaborate?

Agents collaborate through the `AgentMind` orchestrator:

```python
from agentmind import AgentMind

mind = AgentMind(llm_provider=llm)
mind.add_agent(agent1)
mind.add_agent(agent2)

result = await mind.collaborate("Your task here", max_rounds=3)
```

### How do I add tools to agents?

```python
from agentmind.tools import Tool

class MyTool(Tool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="What this tool does",
            parameters={"param": {"type": "string"}}
        )
    
    async def execute(self, param: str) -> str:
        return f"Result: {param}"

agent = Agent(name="Worker", tools=[MyTool()])
```

### How do I save and restore agent conversations?

```python
# Save session
await mind.save_session("session_id")

# Restore session
await mind.restore_session("session_id")
```

### Can I customize the orchestration pattern?

Yes! Implement custom orchestration:

```python
from agentmind.orchestration import Orchestrator

class MyOrchestrator(Orchestrator):
    async def orchestrate(self, task: str) -> str:
        # Your custom logic here
        pass

mind = AgentMind(llm_provider=llm, orchestrator=MyOrchestrator())
```

## LLM Providers

### Which LLM providers are supported?

- **Ollama**: Local models (llama3.2, mistral, etc.)
- **OpenAI**: GPT-3.5, GPT-4, GPT-4-turbo
- **Anthropic**: Claude models
- **100+ more**: Via LiteLLM (Cohere, AI21, Replicate, etc.)

### How do I switch between providers?

Just change the provider initialization:

```python
# Ollama
llm = OllamaProvider(model="llama3.2")

# OpenAI
llm = LiteLLMProvider(model="gpt-4")

# Anthropic
llm = LiteLLMProvider(model="claude-3-opus-20240229")
```

### Which models work best?

For best results:
- **Local**: llama3.2, mistral, mixtral
- **Cloud**: GPT-4, Claude 3 Opus, GPT-4-turbo
- **Budget**: GPT-3.5-turbo, llama3.2 (local)

### Can I use custom/fine-tuned models?

Yes! If your model is compatible with Ollama or accessible via LiteLLM, it will work with AgentMind.

### How do I handle rate limits?

Use the built-in retry mechanism:

```python
from agentmind.utils.retry import RetryConfig, retry_with_backoff

config = RetryConfig(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
result = await retry_with_backoff(agent.generate, config)
```

## Performance & Optimization

### How fast is AgentMind?

Performance depends on:
- LLM provider (local vs cloud)
- Model size
- Number of agents
- Task complexity

Typical response times:
- Local (llama3.2): 2-5 seconds per agent turn
- Cloud (GPT-4): 1-3 seconds per agent turn

### How do I optimize performance?

1. **Use async properly**: Let agents work concurrently
2. **Cache results**: Use memory systems effectively
3. **Limit rounds**: Set appropriate `max_rounds`
4. **Choose right model**: Balance speed vs quality
5. **Batch operations**: Process multiple items together

See [PERFORMANCE.md](PERFORMANCE.md) for detailed optimization guide.

### How much does it cost to run?

Costs vary by provider:
- **Ollama (local)**: Free! Only hardware costs
- **OpenAI GPT-3.5**: ~$0.002 per 1K tokens
- **OpenAI GPT-4**: ~$0.03 per 1K tokens
- **Anthropic Claude**: ~$0.015 per 1K tokens

Track costs with:
```python
from agentmind.utils.observability import CostTracker
tracker = CostTracker()
```

### Can AgentMind handle large-scale applications?

Yes! AgentMind includes:
- REST API server for production deployment
- Docker support for containerization
- Horizontal scaling capabilities
- Session management
- Monitoring and observability

## Troubleshooting

### Agent responses are slow

**Solutions:**
- Use faster models (GPT-3.5 instead of GPT-4)
- Reduce `max_rounds`
- Use local models for faster iteration
- Check network latency for cloud providers

### Agents aren't collaborating effectively

**Solutions:**
- Improve system prompts with clearer instructions
- Add more specific roles to agents
- Increase `max_rounds` for complex tasks
- Use tools to give agents more capabilities

### Out of memory errors

**Solutions:**
- Use smaller models
- Limit conversation history length
- Clear memory periodically
- Increase system RAM

### Import errors

**Solutions:**
```bash
# Reinstall dependencies
pip install -e .

# Install optional dependencies
pip install -e ".[api]"  # For API server
pip install -e ".[cli]"  # For CLI tool
```

### Ollama connection errors

**Solutions:**
```bash
# Check Ollama is running
ollama list

# Restart Ollama
systemctl restart ollama  # Linux
# or restart Ollama app on macOS/Windows

# Verify model is pulled
ollama pull llama3.2
```

### API rate limit errors

**Solutions:**
- Implement retry with backoff
- Use multiple API keys (if allowed)
- Switch to local models
- Reduce request frequency

## Comparison with Other Frameworks

### AgentMind vs CrewAI

| Feature | AgentMind | CrewAI |
|---------|-----------|--------|
| Code Size | ~500 lines | ~15K lines |
| LLM Support | Any provider | Mainly OpenAI |
| Local Models | Full support | Limited |
| Learning Curve | Low | Medium |
| Flexibility | High | Medium |

### AgentMind vs LangGraph

| Feature | AgentMind | LangGraph |
|---------|-----------|-----------|
| Complexity | Simple | Complex |
| Graph-based | No | Yes |
| LLM Agnostic | Yes | Yes |
| Async Native | Yes | Yes |
| Dependencies | Minimal | Heavy |

### AgentMind vs AutoGen

| Feature | AgentMind | AutoGen |
|---------|-----------|---------|
| Code Size | ~500 lines | ~25K lines |
| Setup | Easy | Complex |
| Local Models | Full support | Limited |
| Async | Native | Supported |
| Microsoft-focused | No | Yes |

### When should I use AgentMind?

Choose AgentMind when you want:
- Lightweight, minimal dependencies
- Full control over LLM providers
- Local model support
- Easy to understand and modify
- Quick prototyping to production

### When should I use other frameworks?

Consider alternatives when you need:
- **LangGraph**: Complex graph-based workflows
- **CrewAI**: Opinionated structure and patterns
- **AutoGen**: Microsoft ecosystem integration

## Contributing & Community

### How can I contribute?

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code contributions
- Documentation improvements
- Bug reports
- Feature requests
- Example submissions

### Where can I get help?

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community help
- **Documentation**: Comprehensive guides and examples
- **Examples**: 20+ working examples in `examples/` directory

### How do I report a bug?

1. Check existing issues first
2. Create new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (Python version, OS, etc.)

### Can I use AgentMind commercially?

Yes! AgentMind is MIT licensed, allowing commercial use.

### How do I stay updated?

- Star the repository on GitHub
- Watch for releases
- Follow discussions
- Check the [CHANGELOG.md](CHANGELOG.md)

### Is there a roadmap?

Yes! See [ROADMAP.md](ROADMAP.md) for planned features and improvements.

## Additional Resources

- [Quick Start Guide](QUICKSTART.md)
- [Architecture Overview](ARCHITECTURE.md)
- [API Documentation](API.md)
- [Performance Guide](PERFORMANCE.md)
- [Integration Examples](docs/INTEGRATIONS.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

---

**Still have questions?** Open a [GitHub Discussion](https://github.com/cym3118288-afk/AgentMind/discussions) or [Issue](https://github.com/cym3118288-afk/AgentMind/issues).
