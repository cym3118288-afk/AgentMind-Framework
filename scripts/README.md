# Code Quality Scripts

This directory contains scripts for analyzing and improving code quality in the AgentMind project.

## Scripts

### analyze_code_quality.py

Analyzes code complexity, type coverage, and overall code quality.

**Usage:**
```bash
python scripts/analyze_code_quality.py
```

**Output:**
- `code_quality_report.md`: Detailed markdown report
- `code_quality_analysis.json`: Raw analysis data

**Metrics:**
- Cyclomatic complexity
- Type hint coverage
- Lines of code
- Function count
- Documentation coverage

### improve_code_quality.py

Automatically improves code quality by formatting and organizing code.

**Usage:**
```bash
python scripts/improve_code_quality.py
```

**Actions:**
- Formats code with black
- Sorts imports with isort
- Improves error messages
- Runs linters (mypy, ruff, flake8)

### analyze_documentation.py

Analyzes documentation coverage and generates improvement report.

**Usage:**
```bash
python scripts/analyze_documentation.py
```

**Output:**
- `documentation_report.md`: Documentation analysis report

**Checks:**
- Module docstrings
- Function docstrings
- Class docstrings
- Documentation standards compliance

## Prerequisites

Install required tools:

```bash
pip install black isort mypy ruff flake8 radon
```

## Workflow

1. **Analyze current state:**
   ```bash
   python scripts/analyze_code_quality.py
   python scripts/analyze_documentation.py
   ```

2. **Review reports:**
   - Check `code_quality_report.md`
   - Check `documentation_report.md`

3. **Improve code:**
   ```bash
   python scripts/improve_code_quality.py
   ```

4. **Manual improvements:**
   - Refactor complex functions (complexity > 10)
   - Add missing type hints
   - Add missing docstrings
   - Improve error messages

5. **Verify improvements:**
   ```bash
   pytest --cov=src/agentmind
   mypy src/agentmind --strict
   ```

## Code Quality Standards

### Complexity
- Target: Cyclomatic complexity < 10
- Functions exceeding this should be refactored

### Type Coverage
- Target: >90% parameter coverage
- Target: >90% return type coverage

### Documentation
- All public functions must have docstrings
- All classes must have docstrings
- All modules must have docstrings

### Testing
- Target: >90% code coverage
- All new features must include tests

## CI/CD Integration

Add to your CI pipeline:

```yaml
- name: Check Code Quality
  run: |
    python scripts/analyze_code_quality.py
    python scripts/improve_code_quality.py
    pytest --cov=src/agentmind --cov-fail-under=90
```

## Contributing

When contributing code:
1. Run quality scripts before committing
2. Ensure all checks pass
3. Add tests for new features
4. Update documentation

## License

MIT License - see LICENSE file for details
