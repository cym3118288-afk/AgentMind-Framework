# AgentMind Examples

This directory contains comprehensive examples demonstrating AgentMind's capabilities, from basic multi-agent collaboration to advanced orchestration patterns.

## Quick Start

All examples can be run directly:

```bash
python examples/basic_collaboration.py
```

## Examples by Difficulty

### Beginner Examples

Perfect for getting started with AgentMind. No prior multi-agent experience required.

#### basic_collaboration.py
**Time:** 5 minutes | **Prerequisites:** None

Learn the fundamentals of multi-agent collaboration:
- Creating agents with different roles (Analyst, Creative, Coordinator)
- Adding agents to AgentMind
- Starting collaborations and viewing results
- Understanding agent contributions and statistics

**Run it:**
```bash
python examples/basic_collaboration.py
```

**Expected Output:** Agents collaborate to suggest names for an AI productivity app, with each agent contributing based on their role.

---

#### debate_example.py
**Time:** 10 minutes | **Prerequisites:** Optional - Ollama with llama3.2

Multi-agent debate with contrasting perspectives:
- Configuring LLM providers (Ollama or LiteLLM)
- Creating agents with opposing viewpoints
- Running multi-round debates
- Analyzing debate outcomes

**Run it:**
```bash
python examples/debate_example.py
```

**Expected Output:** Optimist and Pessimist debate AI investment while Moderator synthesizes viewpoints. Works with or without LLM.

---

### Intermediate Examples

Build on basic concepts with more sophisticated patterns.

#### hierarchical_example.py
**Time:** 15 minutes | **Prerequisites:** Basic collaboration understanding

Hierarchical collaboration with supervisor coordination:
- Implementing hierarchical strategies
- Creating supervisor-subordinate relationships
- Coordinating specialized agents
- Decision-making workflows

**Run it:**
```bash
python examples/hierarchical_example.py
```

**Expected Output:** CEO supervises DataAnalyst, MarketResearcher, and RiskManager to make product launch decision.

---

#### custom_tools.py
**Time:** 20 minutes | **Prerequisites:** Basic agent collaboration

Create and use custom tools with agents:
- Building tools with @tool decorator
- Tool parameter validation
- Integrating tools with agents
- Error handling in tools

**Run it:**
```bash
python examples/custom_tools.py
```

**Expected Output:** Agents use calculator, weather, database, and time tools in collaborative workflows.

---

#### code_review_team.py
**Time:** 20 minutes | **Prerequisites:** Understanding of agent roles

Automated code review with specialized agents:
- Security analysis
- Performance optimization
- Code quality assessment
- Collaborative review process

**Run it:**
```bash
python examples/code_review_team.py
```

**Expected Output:** Team of agents reviews code for security, performance, and quality issues.

---

#### data_analysis_team.py
**Time:** 15 minutes | **Prerequisites:** Basic collaboration

Multi-agent data analysis workflow:
- Data collection and preprocessing
- Statistical analysis
- Visualization recommendations
- Collaborative insights

**Run it:**
```bash
python examples/data_analysis_team.py
```

---

#### research_team.py
**Time:** 15 minutes | **Prerequisites:** Basic collaboration

Collaborative research with specialized agents:
- Information gathering
- Analysis and synthesis
- Report generation
- Team coordination

**Run it:**
```bash
python examples/research_team.py
```

---

#### fastapi_integration.py
**Time:** 20 minutes | **Prerequisites:** FastAPI knowledge

Integrate AgentMind with FastAPI:
- REST API endpoints for agent collaboration
- Async request handling
- WebSocket support for real-time updates
- Production deployment patterns

**Run it:**
```bash
python examples/fastapi_integration.py
```

**Expected Output:** FastAPI server with endpoints for agent collaboration and real-time updates.

---

#### monitoring_example.py
**Time:** 15 minutes | **Prerequisites:** Basic collaboration

Monitor and observe agent behavior:
- Performance metrics collection
- Conversation tracking
- Agent activity monitoring
- Debugging and diagnostics

**Run it:**
```bash
python examples/monitoring_example.py
```

---

#### testing_example.py
**Time:** 20 minutes | **Prerequisites:** pytest knowledge

Test multi-agent systems:
- Unit testing agents
- Integration testing collaborations
- Mocking LLM providers
- Test fixtures and utilities

**Run it:**
```bash
pytest examples/testing_example.py -v
```

---

### Advanced Examples

Production-ready patterns for complex multi-agent systems.

#### advanced_orchestration.py
**Time:** 30-45 minutes | **Prerequisites:** Strong multi-agent understanding

Sophisticated orchestration patterns:
- Consensus mechanisms (majority, unanimous, weighted)
- Parallel task decomposition
- Dynamic agent spawning
- Skill-based agent matching
- Enterprise-grade coordination

**Run it:**
```bash
python examples/advanced_orchestration.py
```

**Expected Output:** Demonstrations of consensus voting, parallel task execution, dynamic scaling, and skill matching.

---

#### distributed_research_team.py
**Time:** 30 minutes | **Prerequisites:** Advanced orchestration

Large-scale distributed research:
- Multi-agent research coordination
- Distributed task allocation
- Result aggregation
- Scalable research workflows

**Run it:**
```bash
python examples/distributed_research_team.py
```

---

#### performance_optimization.py
**Time:** 25 minutes | **Prerequisites:** Performance tuning knowledge

Optimize multi-agent performance:
- Caching strategies
- Parallel execution
- Resource management
- Benchmarking and profiling

**Run it:**
```bash
python examples/performance_optimization.py
```

---

#### self_improvement.py
**Time:** 30 minutes | **Prerequisites:** Advanced concepts

Self-improving agent systems:
- Learning from interactions
- Performance feedback loops
- Adaptive behavior
- Continuous improvement

**Run it:**
```bash
python examples/self_improvement.py
```

---

### Multimodal Examples

Work with images, audio, and documents.

#### multimodal_image_example.py
**Time:** 20 minutes | **Prerequisites:** PIL/Pillow installed

Process and analyze images:
- Image understanding
- Visual question answering
- Multi-agent image analysis
- Vision-language integration

**Run it:**
```bash
python examples/multimodal_image_example.py
```

---

#### multimodal_audio_example.py
**Time:** 20 minutes | **Prerequisites:** Audio processing libraries

Audio processing and analysis:
- Speech recognition
- Audio classification
- Multi-agent audio analysis
- Audio-text integration

**Run it:**
```bash
python examples/multimodal_audio_example.py
```

---

#### multimodal_document_example.py
**Time:** 25 minutes | **Prerequisites:** Document processing libraries

Document understanding and analysis:
- PDF processing
- Document extraction
- Multi-agent document review
- Structured data extraction

**Run it:**
```bash
python examples/multimodal_document_example.py
```

---

### Integration Examples

Connect AgentMind with popular frameworks.

#### integrations/langchain_integration.py
**Time:** 20 minutes | **Prerequisites:** LangChain installed

Integrate with LangChain:
- LangChain tool compatibility
- Chain integration
- Memory sharing
- Hybrid workflows

**Run it:**
```bash
python examples/integrations/langchain_integration.py
```

---

#### integrations/llamaindex_integration.py
**Time:** 20 minutes | **Prerequisites:** LlamaIndex installed

Integrate with LlamaIndex:
- Index-based retrieval
- Query engines
- Multi-agent RAG
- Knowledge base integration

**Run it:**
```bash
python examples/integrations/llamaindex_integration.py
```

---

#### integrations/haystack_integration.py
**Time:** 20 minutes | **Prerequisites:** Haystack installed

Integrate with Haystack:
- Pipeline integration
- Document stores
- Multi-agent search
- NLP pipelines

**Run it:**
```bash
python examples/integrations/haystack_integration.py
```

---

#### integrations/huggingface_integration.py
**Time:** 20 minutes | **Prerequisites:** Transformers installed

Integrate with Hugging Face:
- Model loading
- Inference pipelines
- Multi-agent model usage
- Fine-tuning integration

**Run it:**
```bash
python examples/integrations/huggingface_integration.py
```

---

#### integrations/openai_assistants_compat.py
**Time:** 15 minutes | **Prerequisites:** OpenAI API key

OpenAI Assistants API compatibility:
- Assistant creation
- Thread management
- Tool integration
- Migration from OpenAI Assistants

**Run it:**
```bash
export OPENAI_API_KEY=your-key
python examples/integrations/openai_assistants_compat.py
```

---

### Plugin Examples

Extend AgentMind with plugins.

#### plugin_discord_example.py
**Time:** 25 minutes | **Prerequisites:** discord.py installed

Discord bot integration:
- Bot commands
- Multi-agent Discord interactions
- Channel management
- Real-time collaboration

**Run it:**
```bash
export DISCORD_TOKEN=your-token
python examples/plugin_discord_example.py
```

---

#### plugin_slack_example.py
**Time:** 25 minutes | **Prerequisites:** slack-sdk installed

Slack bot integration:
- Slash commands
- Interactive messages
- Multi-agent Slack workflows
- Team collaboration

**Run it:**
```bash
export SLACK_TOKEN=your-token
python examples/plugin_slack_example.py
```

---

### Use Case Examples

Real-world application scenarios.

#### use_cases/customer_support.py
**Time:** 25 minutes | **Prerequisites:** Intermediate knowledge

Automated customer support system:
- Ticket classification
- Response generation
- Escalation handling
- Multi-agent support workflows

**Run it:**
```bash
python examples/use_cases/customer_support.py
```

---

#### use_cases/code_review_automation.py
**Time:** 30 minutes | **Prerequisites:** Git knowledge

Automated code review pipeline:
- Pull request analysis
- Security scanning
- Performance review
- Automated feedback

**Run it:**
```bash
python examples/use_cases/code_review_automation.py
```

---

#### use_cases/content_generation.py
**Time:** 25 minutes | **Prerequisites:** Content creation understanding

Multi-agent content creation:
- Blog post generation
- SEO optimization
- Fact-checking
- Editorial review

**Run it:**
```bash
python examples/use_cases/content_generation.py
```

---

#### use_cases/financial_analysis.py
**Time:** 30 minutes | **Prerequisites:** Financial domain knowledge

Financial analysis and reporting:
- Market analysis
- Risk assessment
- Portfolio recommendations
- Report generation

**Run it:**
```bash
python examples/use_cases/financial_analysis.py
```

---

#### use_cases/ecommerce_recommendations.py
**Time:** 25 minutes | **Prerequisites:** E-commerce understanding

Product recommendation system:
- User preference analysis
- Collaborative filtering
- Multi-agent recommendations
- Personalization

**Run it:**
```bash
python examples/use_cases/ecommerce_recommendations.py
```

---

### Utility Examples

Tools and utilities for development.

#### visualization_dashboard.py
**Time:** 15 minutes | **Prerequisites:** Visualization libraries

Visualize agent interactions:
- Conversation graphs
- Performance dashboards
- Real-time monitoring
- Analytics visualization

**Run it:**
```bash
python examples/visualization_dashboard.py
```

---

#### template_marketplace.py
**Time:** 10 minutes | **Prerequisites:** None

Browse and use agent templates:
- Pre-built agent configurations
- Template customization
- Quick start templates
- Best practices

**Run it:**
```bash
python examples/template_marketplace.py
```

---

#### run_benchmarks.py
**Time:** 20 minutes | **Prerequisites:** Benchmarking understanding

Benchmark agent performance:
- Performance testing
- Scalability analysis
- Comparison metrics
- Optimization insights

**Run it:**
```bash
python examples/run_benchmarks.py
```

---

## Common Patterns

### Basic Collaboration Pattern

```python
from agentmind import Agent, AgentMind, AgentRole

# Create mind
mind = AgentMind()

# Create and add agents
agent1 = Agent(name="Alice", role=AgentRole.ANALYST.value)
agent2 = Agent(name="Bob", role=AgentRole.CREATIVE.value)
mind.add_agent(agent1)
mind.add_agent(agent2)

# Start collaboration
result = await mind.start_collaboration("Your task here")
print(result.final_output)
```

### LLM Integration Pattern

```python
from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider

# Configure LLM
llm = OllamaProvider(model="llama3.2")

# Create agents with LLM
agent = Agent(name="Assistant", role="helper", llm_provider=llm)
mind = AgentMind(llm_provider=llm)
mind.add_agent(agent)

# Use LLM in collaboration
result = await mind.start_collaboration("Task", use_llm=True)
```

### Custom Tools Pattern

```python
from agentmind.tools import tool

@tool(name="my_tool", description="Does something useful")
def my_tool(param: str) -> str:
    """Tool implementation."""
    return f"Result: {param}"

# Register with agent
agent.register_tool(my_tool)
```

### Hierarchical Pattern

```python
from agentmind import Agent, AgentMind, CollaborationStrategy

mind = AgentMind(strategy=CollaborationStrategy.HIERARCHICAL)

# Add supervisor first
supervisor = Agent(name="Boss", role="supervisor")
mind.add_agent(supervisor)

# Add subordinates
worker = Agent(name="Worker", role="worker")
mind.add_agent(worker)
```

## Troubleshooting

### Ollama Connection Issues

If you see "Ollama not available" messages:

1. Install Ollama: https://ollama.ai
2. Pull a model: `ollama pull llama3.2`
3. Verify it's running: `ollama list`

Examples will fall back to template responses if Ollama is unavailable.

### Import Errors

Make sure AgentMind is installed:

```bash
pip install -e .
```

Or add to Python path:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

### Performance Issues

For better performance:

1. Use caching (see `performance_optimization.py`)
2. Enable parallel execution
3. Optimize LLM parameters (temperature, max_tokens)
4. Use appropriate collaboration strategies

## Next Steps

1. Start with `basic_collaboration.py` to learn fundamentals
2. Progress to intermediate examples for real-world patterns
3. Explore advanced examples for production systems
4. Check use cases for complete application examples
5. Review integration examples for framework compatibility

## Contributing

Found a bug or have an example idea? See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

All examples are provided under the same license as AgentMind. See [LICENSE](../LICENSE) for details.
