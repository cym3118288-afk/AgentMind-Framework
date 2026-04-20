# AgentMind Tutorials

Interactive Jupyter notebooks to learn AgentMind from basics to advanced topics.

## Getting Started

### Prerequisites

```bash
# Install AgentMind
pip install -e .

# Install Jupyter
pip install jupyter notebook

# For notebooks, install nest_asyncio
pip install nest_asyncio
```

### Running Tutorials

```bash
# Start Jupyter
jupyter notebook

# Navigate to tutorials/ directory
# Open any .ipynb file
```

## Available Tutorials

### 1. Getting Started (01_getting_started.ipynb)

Perfect for beginners. Learn:
- Creating your first agent
- Setting up LLM providers
- Multi-agent collaboration
- Adding tools to agents
- Memory and context
- Best practices

**Time**: 30-45 minutes  
**Level**: Beginner  
**Prerequisites**: Basic Python knowledge

### 2. Advanced Topics (02_advanced_topics.ipynb)

For building production systems. Learn:
- Custom orchestration patterns
- Error handling and retry mechanisms
- Performance optimization
- Cost tracking and monitoring
- External system integration
- Testing strategies

**Time**: 60-90 minutes  
**Level**: Advanced  
**Prerequisites**: Complete Tutorial 1, async/await knowledge

## Tutorial Structure

Each tutorial includes:
- Clear explanations
- Runnable code examples
- Hands-on exercises
- Best practices
- Links to additional resources

## Tips for Learning

1. **Run the code**: Don't just read - execute each cell
2. **Experiment**: Modify examples to see what happens
3. **Take notes**: Document your learnings
4. **Build projects**: Apply concepts to real problems
5. **Ask questions**: Use GitHub Discussions for help

## Common Issues

### Async in Jupyter

Jupyter notebooks require `nest_asyncio` for async code:

```python
import nest_asyncio
nest_asyncio.apply()
```

### Ollama Connection

Make sure Ollama is running:

```bash
# Check Ollama status
ollama list

# Pull required model
ollama pull llama3.2
```

### Import Errors

Ensure AgentMind is installed:

```bash
pip install -e .
```

## Next Steps After Tutorials

1. **Explore Examples**: Check `examples/` directory for more use cases
2. **Read Documentation**: Deep dive into [Architecture](../ARCHITECTURE.md)
3. **Build Projects**: Create your own multi-agent system
4. **Contribute**: Share your tutorials and improvements

## Additional Resources

- [FAQ](../FAQ.md) - Common questions answered
- [Quick Start Guide](../QUICKSTART.md) - Fast setup
- [API Documentation](../API.md) - Complete reference
- [Integration Guide](../docs/INTEGRATIONS.md) - Framework integrations
- [Performance Guide](../PERFORMANCE.md) - Optimization tips

## Contributing Tutorials

We welcome tutorial contributions! To add a tutorial:

1. Create a new `.ipynb` file
2. Follow the existing structure
3. Include clear explanations and examples
4. Test all code cells
5. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## Feedback

Have suggestions for tutorials? Open an issue or discussion on GitHub!

---

Happy learning with AgentMind!
