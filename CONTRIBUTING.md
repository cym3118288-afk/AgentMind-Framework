# Contributing to AgentMind

Thank you for your interest in contributing to AgentMind! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help create a welcoming environment for all contributors

## Getting Started

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/cym3118288-afk/AgentMind-Framework.git
   cd AgentMind-Framework
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Development Workflow

### Code Style

We use automated tools to maintain code quality:

- **Black**: Code formatting (line length: 100)
- **isort**: Import sorting
- **Ruff**: Fast Python linting
- **mypy**: Static type checking

Run all checks:
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

Pre-commit hooks will run these automatically on commit.

### Type Hints

- All public functions must have type hints
- Use Pydantic models for data validation
- Follow PEP 484 type hint conventions

### Documentation

- Use Google-style docstrings
- Include examples in docstrings where helpful
- Document all parameters and return values
- Add type information in docstrings

Example:
```python
def process_message(self, message: Message) -> Optional[Message]:
    """Process an incoming message and generate a response.

    Args:
        message: The incoming message to process

    Returns:
        A response message, or None if the agent is inactive

    Example:
        >>> agent = Agent(name="analyst", role="analyst")
        >>> msg = Message(content="What do you think?", sender="user")
        >>> response = await agent.process_message(msg)
    """
```

### Testing

- Write tests for all new features
- Maintain test coverage above 85%
- Use pytest for testing
- Use pytest-asyncio for async tests

Run tests:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agentmind --cov-report=html

# Run specific test file
pytest tests/test_basic.py -v
```

### Commit Messages

Follow conventional commit format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `style:` Code style changes (formatting, etc.)
- `chore:` Maintenance tasks

Example:
```
feat: add hierarchical orchestration strategy

- Implement supervisor-worker pattern
- Add delegation logic
- Update tests
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Run all checks**
   ```bash
   # Format and lint
   black src/ tests/
   isort src/ tests/
   ruff check src/ tests/
   mypy src/

   # Run tests
   pytest --cov=agentmind
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure all CI checks pass

## Areas for Contribution

### High Priority
- LLM provider implementations (Phase 1)
- Memory backend implementations (Phase 2)
- Tool implementations (Phase 2)
- Documentation improvements
- Example applications

### Good First Issues
- Adding new agent role templates
- Improving error messages
- Writing additional tests
- Documentation typos and clarifications

### Advanced Contributions
- Performance optimizations
- New orchestration strategies
- Advanced memory systems
- Distributed agent support

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
