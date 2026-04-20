# AgentMind Plugin Marketplace

Welcome to the AgentMind Plugin Marketplace! This directory contains information about available plugins and how to create your own.

## Available Plugin Types

AgentMind supports the following plugin types:

1. **LLM Providers** - Custom language model integrations
2. **Memory Backends** - Storage backends for agent memory
3. **Tools** - External tools and APIs agents can use
4. **Orchestrators** - Custom orchestration strategies
5. **Observers** - Monitoring and middleware plugins

## Official Plugins

### LLM Providers

- **agentmind-plugin-openai** - OpenAI GPT models integration
- **agentmind-plugin-anthropic** - Anthropic Claude integration
- **agentmind-plugin-ollama** - Local Ollama models (built-in)
- **agentmind-plugin-litellm** - LiteLLM unified interface (built-in)

### Memory Backends

- **agentmind-plugin-redis** - Redis-based memory backend
- **agentmind-plugin-pinecone** - Pinecone vector database
- **agentmind-plugin-weaviate** - Weaviate vector database
- **agentmind-plugin-chroma** - ChromaDB integration (built-in)

### Tools

- **agentmind-plugin-web-search** - Web search capabilities
- **agentmind-plugin-code-executor** - Safe code execution
- **agentmind-plugin-file-ops** - File system operations
- **agentmind-plugin-api-client** - REST API client

### Orchestrators

- **agentmind-plugin-langgraph** - LangGraph compatibility
- **agentmind-plugin-autogen** - AutoGen-style orchestration
- **agentmind-plugin-crewai** - CrewAI-style workflows

### Observers

- **agentmind-plugin-langsmith** - LangSmith tracing
- **agentmind-plugin-wandb** - Weights & Biases logging
- **agentmind-plugin-prometheus** - Prometheus metrics

## Installing Plugins

Install plugins using pip:

```bash
pip install agentmind-plugin-openai
pip install agentmind-plugin-redis
```

Plugins are automatically discovered via entry points. No additional configuration needed!

## Using Plugins

```python
from agentmind import discover_plugins, load_plugin

# Discover all available plugins
plugins = discover_plugins()
print(plugins)
# {'llm': ['openai', 'anthropic'], 'memory': ['redis', 'pinecone'], ...}

# Load a specific plugin
OpenAIProvider = load_plugin('llm', 'openai')
provider = OpenAIProvider(api_key='your-key')

# Use with AgentMind
from agentmind import Agent, AgentMind

agent = Agent(name="assistant", llm_provider=provider)
mind = AgentMind(llm_provider=provider)
```

## Creating Your Own Plugin

### 1. Create Plugin Package Structure

```
agentmind-plugin-myplugin/
├── setup.py
├── README.md
├── LICENSE
├── agentmind_plugin_myplugin/
│   ├── __init__.py
│   └── plugin.py
└── tests/
    └── test_plugin.py
```

### 2. Implement Plugin Interface

```python
# agentmind_plugin_myplugin/plugin.py
from agentmind.plugins.interfaces import LLMProvider, PluginMetadata

class MyLLMProvider(LLMProvider):
    """My custom LLM provider."""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="myplugin",
            version="0.1.0",
            description="My custom LLM provider",
            author="Your Name",
            plugin_type="llm_provider",
        )
    
    async def initialize(self, config=None):
        # Initialize your provider
        pass
    
    async def shutdown(self):
        # Cleanup
        pass
    
    def health_check(self):
        return True
    
    async def generate(self, messages, **kwargs):
        # Implement generation logic
        return {
            "content": "Generated response",
            "model": "my-model",
            "usage": {},
            "metadata": {},
        }
    
    async def generate_stream(self, messages, **kwargs):
        # Implement streaming
        yield "chunk1"
        yield "chunk2"
    
    def get_model_info(self):
        return {"name": "my-model", "max_tokens": 4096}
```

### 3. Configure Entry Points

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="agentmind-plugin-myplugin",
    version="0.1.0",
    description="My AgentMind plugin",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "agentmind>=0.2.0",
        # Your dependencies
    ],
    entry_points={
        "agentmind.plugins.llm": [
            "myplugin = agentmind_plugin_myplugin.plugin:MyLLMProvider",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
```

### 4. Test Your Plugin

```python
# tests/test_plugin.py
import pytest
from agentmind_plugin_myplugin.plugin import MyLLMProvider

@pytest.mark.asyncio
async def test_plugin():
    provider = MyLLMProvider()
    await provider.initialize()
    
    result = await provider.generate([
        {"role": "user", "content": "Hello"}
    ])
    
    assert result["content"]
    assert provider.health_check()
    
    await provider.shutdown()
```

### 5. Publish Your Plugin

```bash
# Build distribution
python setup.py sdist bdist_wheel

# Upload to PyPI
pip install twine
twine upload dist/*
```

## Plugin Templates

AgentMind provides templates for all plugin types:

```python
from agentmind.plugins.templates import (
    ExampleLLMProvider,
    ExampleMemoryBackend,
    ExampleOrchestrator,
    ExampleObserver,
    print_plugin_template,
)

# Print full template
print_plugin_template()
```

## Plugin Guidelines

### Best Practices

1. **Follow the interface** - Implement all required methods
2. **Handle errors gracefully** - Don't crash the main application
3. **Document thoroughly** - Provide clear documentation and examples
4. **Test extensively** - Include comprehensive tests
5. **Version properly** - Use semantic versioning
6. **Declare dependencies** - List all requirements in setup.py

### Security

1. **Validate inputs** - Never trust user input
2. **Use sandboxing** - For code execution plugins
3. **Respect permissions** - Declare required permissions
4. **Secure credentials** - Never hardcode API keys
5. **Audit dependencies** - Keep dependencies up to date

### Performance

1. **Async by default** - Use async/await for I/O operations
2. **Cache when possible** - Reduce redundant operations
3. **Batch operations** - Group similar operations
4. **Resource cleanup** - Properly close connections
5. **Monitor usage** - Track resource consumption

## Community Plugins

Submit your plugin to be listed here! Create a PR with:

- Plugin name and description
- Installation instructions
- Link to repository
- License information

## Support

- **Documentation**: https://agentmind.readthedocs.io
- **GitHub Issues**: https://github.com/cym3118288-afk/AgentMind-Framework/issues
- **Discord**: [Join our community]
- **Email**: cym3118288@gmail.com

## License

All official plugins are MIT licensed. Community plugins may have different licenses.
