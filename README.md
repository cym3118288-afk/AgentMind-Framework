# AgentMind 🧠

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**The lightest multi-agent framework for Python.** Build collaborative AI systems with minimal code and maximum flexibility.

## Why AgentMind?

Unlike heavyweight frameworks that force you into rigid patterns, AgentMind gives you the essentials:

- **Truly Lightweight**: Core framework is <500 lines. No bloat, no vendor lock-in
- **LLM Agnostic**: Works with Ollama, OpenAI, Anthropic, or any LiteLLM-supported provider
- **Async First**: Built on asyncio for real concurrent agent collaboration
- **Memory Built-in**: Conversation history and context management out of the box
- **Tool System**: Extensible function calling for agents
- **Production Ready**: Type hints, comprehensive tests, proper error handling

## Quick Start

```bash
pip install -e .
```

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

## Features

### Core Capabilities

- **Multi-Agent Orchestration**: Coordinate multiple AI agents with different roles and expertise
- **Flexible LLM Support**: Ollama for local models, LiteLLM for 100+ cloud providers
- **Memory Management**: Automatic conversation history with configurable backends
- **Tool System**: Give agents access to functions, APIs, and external tools
- **Async Architecture**: True concurrent execution for faster collaboration
- **Type Safety**: Full type hints for better IDE support and fewer bugs

### Advanced Features

- **Custom Orchestration**: Implement your own collaboration patterns
- **Streaming Support**: Real-time token streaming from LLMs
- **Session Persistence**: Save and restore agent conversations
- **Web UI**: Interactive chat interface for testing (see `chat_server.py`)
- **Extensible**: Plugin architecture for custom memory, tools, and providers

## Comparison

| Feature | AgentMind | CrewAI | LangGraph | AutoGen |
|---------|-----------|--------|-----------|---------|
| Lines of Code | ~500 | ~15K | ~20K | ~25K |
| LLM Agnostic | ✅ | ❌ | ✅ | ✅ |
| Local LLM Support | ✅ | Limited | ✅ | Limited |
| Async Native | ✅ | ❌ | ✅ | ✅ |
| Learning Curve | Low | Medium | High | High |
| Dependencies | Minimal | Heavy | Heavy | Heavy |

## Examples

### Research Team

```python
# Create a team of agents that research and summarize topics
from examples.research_team import run_research_team

await run_research_team("Latest developments in AI safety")
```

### Code Review Team

```python
# Automated code review with multiple perspectives
from examples.code_review_team import run_code_review

await run_code_review("path/to/code.py")
```

### Hierarchical Agents

```python
# Manager agent coordinating worker agents
from examples.hierarchical_example import run_hierarchical

await run_hierarchical("Plan a product launch")
```

### Data Analysis Team

```python
# Multi-agent data analysis with specialized roles
from examples.data_analysis_team import analyze_dataset

await analyze_dataset("E-commerce sales data for Q1 2024")
```

### FastAPI Integration

```python
# Production API with AgentMind
# See examples/fastapi_integration.py for full implementation
python examples/fastapi_integration.py
# API available at http://localhost:8000
```

See the [examples/](examples/) directory for more.

## Documentation

- [Quick Start Guide](QUICKSTART.md) - Get up and running in 5 minutes
- [Architecture Overview](ARCHITECTURE.md) - Understand the design
- [Performance Guide](PERFORMANCE.md) - Optimization tips and benchmarks
- [API Documentation](API.md) - REST API reference
- [Docker Guide](DOCKER.md) - Container deployment
- [Contributing Guide](CONTRIBUTING.md) - Help improve AgentMind
- [Roadmap](ROADMAP.md) - What's coming next

## Installation

### From Source

```bash
git clone https://github.com/cym3118288-afk/AgentMind.git
cd AgentMind
pip install -e .
```

### With Ollama (Recommended for Local)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2

# Run AgentMind
python examples/basic_collaboration.py
```

### With OpenAI/Anthropic

```bash
pip install litellm
export OPENAI_API_KEY=your-key-here
# or
export ANTHROPIC_API_KEY=your-key-here

python examples/basic_collaboration.py
```

## Production Features (Phase 3)

### REST API Server

Run AgentMind as a production API service:

```bash
pip install -e ".[api]"
python api_server.py
# API available at http://localhost:8000
```

API endpoints:
- `POST /collaborate` - Run agent collaboration
- `GET /health` - Health check
- `GET /sessions/{id}` - Get session details
- `GET /metrics` - System metrics

### CLI Tool

Use AgentMind from the command line:

```bash
pip install -e ".[cli]"
agentmind run --task "Analyze this codebase" --agents 3 --model llama3.2
```

### Docker Deployment

Run with Docker (includes Ollama):

```bash
docker-compose up
# API available at http://localhost:8000
# Ollama at http://localhost:11434
```

### Error Recovery & Observability

Built-in retry mechanisms and cost tracking:

```python
from agentmind.utils.retry import RetryConfig, retry_with_backoff
from agentmind.utils.observability import Tracer, CostTracker

# Automatic retry with exponential backoff
config = RetryConfig(max_retries=3, initial_delay=1.0)
result = await retry_with_backoff(agent.generate, config)

# Track costs and performance
tracer = Tracer(session_id="my-session")
tracer.start()
# ... your code ...
tracer.end()
print(tracer.get_summary())
```

## Interactive Chat UI

AgentMind includes a web-based chat interface:

```bash
python chat_server.py
# Open http://localhost:5000
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/agentmind

# Run specific test
pytest tests/test_agent_llm.py
```

## Project Structure

```
agentmind/
├── src/agentmind/
│   ├── core/           # Agent, Mind, Message types
│   ├── llm/            # LLM provider abstractions
│   ├── memory/         # Memory management
│   ├── tools/          # Tool system
│   ├── orchestration/  # Collaboration patterns
│   └── prompts/        # Prompt templates
├── examples/           # Example implementations
├── tests/              # Comprehensive test suite
└── docs/               # Documentation
```

## Roadmap

- [x] Phase 0: Core architecture (Days 1-10)
- [x] Phase 1: LLM integration (Days 11-20)
- [x] Phase 2: Memory & Tools (Days 11-20)
- [x] Phase 3: Production features (Days 21-40)
  - [x] Error recovery & retry mechanisms
  - [x] Observability (tracing, cost tracking)
  - [x] FastAPI REST API
  - [x] Docker image with Ollama
  - [x] CLI tool
  - [ ] Multi-modal support
- [x] Phase 4: Advanced features (Days 41-60)
  - [x] Self-improvement mechanisms (prompt optimization, debate, feedback loops)
  - [x] Template marketplace (20+ built-in templates)
  - [x] Evaluation suite (GAIA/AgentBench subsets, benchmarks)
  - [x] Visualization dashboard (Gradio UI)
  - [x] Advanced orchestration (consensus, dynamic spawning, parallel decomposition)
  - [ ] Integration examples (LangChain, LlamaIndex, etc.)
  - [ ] Performance optimizations (caching, batching)

See [ROADMAP.md](ROADMAP.md) for details.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick ways to contribute:
- Report bugs or request features via [Issues](https://github.com/cym3118288-afk/AgentMind/issues)
- Improve documentation
- Add examples
- Submit pull requests

## License

MIT License - see [LICENSE](LICENSE) for details.

## Citation

If you use AgentMind in your research or project, please cite:

```bibtex
@software{agentmind2024,
  title = {AgentMind: Lightweight Multi-Agent Framework for Python},
  author = {Terry Carson},
  year = {2024},
  url = {https://github.com/cym3118288-afk/AgentMind}
}
```

## Community

- GitHub Discussions: [Ask questions, share ideas](https://github.com/cym3118288-afk/AgentMind/discussions)
- Issues: [Report bugs, request features](https://github.com/cym3118288-afk/AgentMind/issues)

## Star History

If you find AgentMind useful, please star the repository to help others discover it!

---

Built with ❤️ by the AgentMind community
