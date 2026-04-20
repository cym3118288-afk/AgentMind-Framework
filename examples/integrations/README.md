# Integration Examples

This directory contains integration examples showing how to use AgentMind with popular AI/ML frameworks and tools.

## Available Integrations

### 1. LangChain Integration (`langchain_integration.py`)

Demonstrates how to combine AgentMind with LangChain:
- Use LangChain tools within AgentMind agents
- Use AgentMind as a component in LangChain chains
- Hybrid RAG system combining both frameworks
- Sequential processing pipelines

**Install**: `pip install langchain langchain-community`

**Run**: `python langchain_integration.py`

### 2. LlamaIndex Integration (`llamaindex_integration.py`)

Shows how to integrate AgentMind with LlamaIndex for advanced RAG:
- Basic RAG with vector search
- Multi-agent RAG systems
- Document analysis pipelines
- Hybrid search with metadata filtering
- Real-time document ingestion

**Install**: `pip install llama-index`

**Run**: `python llamaindex_integration.py`

### 3. Haystack Integration (`haystack_integration.py`)

Combines AgentMind with Haystack for production NLP pipelines:
- Document retrieval with BM25
- Multi-agent pipeline orchestration
- Question answering systems
- Document processing workflows

**Install**: `pip install haystack-ai`

**Run**: `python haystack_integration.py`

### 4. OpenAI Assistants API Compatibility (`openai_assistants_compat.py`)

Provides a compatibility layer for OpenAI Assistants API:
- Drop-in replacement for OpenAI Assistants
- Thread and message management
- Run execution and status tracking
- Works with any LLM provider (not just OpenAI)
- Custom tools support

**Install**: No additional dependencies (uses AgentMind's existing providers)

**Run**: `python openai_assistants_compat.py`

### 5. Hugging Face Transformers Integration (`huggingface_integration.py`)

Integrates Hugging Face models and pipelines with AgentMind:
- Sentiment analysis tools
- Named Entity Recognition (NER)
- Text summarization
- Multi-task NLP pipelines
- Question answering with context

**Install**: `pip install transformers torch`

**Run**: `python huggingface_integration.py`

### 6. AutoGen Integration (`autogen_integration.py`)

Microsoft AutoGen compatibility layer:
- AutoGen-style agent interface
- Group chat management
- Code execution capabilities
- Hybrid AutoGen + AgentMind systems

**Install**: `pip install pyautogen`

**Run**: `python autogen_integration.py`

### 7. CrewAI Integration (`crewai_integration.py`)

CrewAI-style crews and task-based workflows:
- Task-based agent collaboration
- Sequential, hierarchical, and consensus processes
- Task dependencies and context
- Role-based agent profiles

**Install**: `pip install crewai`

**Run**: `python crewai_integration.py`

## Quick Start

1. Install AgentMind:
```bash
pip install -e .
```

2. Install the integration you want to use:
```bash
# For LangChain
pip install langchain langchain-community

# For LlamaIndex
pip install llama-index

# For Haystack
pip install haystack-ai

# For Hugging Face
pip install transformers torch
```

3. Run the example:
```bash
cd examples/integrations
python langchain_integration.py
```

## Use Cases

### Research & Analysis
- **LlamaIndex + AgentMind**: Build advanced RAG systems for research
- **Haystack + AgentMind**: Production document search and analysis

### Content Processing
- **Hugging Face + AgentMind**: NLP tasks with local models
- **LangChain + AgentMind**: Complex content generation pipelines

### Migration & Compatibility
- **OpenAI Assistants Compat**: Migrate from OpenAI Assistants to AgentMind
- **LangChain Integration**: Gradually adopt AgentMind in existing LangChain projects

## Architecture Patterns

### Pattern 1: Tools Integration
Use external framework tools within AgentMind agents:
```python
from langchain.tools import DuckDuckGoSearchRun
from agentmind import Agent, AgentMind

# Wrap LangChain tool
search_tool = LangChainToolWrapper(DuckDuckGoSearchRun())

# Use in AgentMind agent
agent = Agent(name="Researcher", tools=[search_tool])
```

### Pattern 2: Pipeline Integration
Use AgentMind as a component in external pipelines:
```python
from agentmind import AgentMind

# Create AgentMind system
mind = AgentMind(llm_provider=llm)
# ... add agents ...

# Use in LangChain pipeline
agentmind_chain = AgentMindChain(mind)
result = await agentmind_chain.arun("Your task")
```

### Pattern 3: Hybrid Systems
Combine strengths of both frameworks:
```python
# LlamaIndex for retrieval
retriever = LlamaIndexRetriever(query_engine)

# AgentMind for multi-agent reasoning
agent = Agent(name="Analyst", tools=[retriever])
mind.add_agent(agent)

# Collaborate with retrieved context
result = await mind.collaborate(query)
```

## Benefits

### Why Integrate?

1. **Best of Both Worlds**: Combine AgentMind's lightweight multi-agent orchestration with specialized tools from other frameworks

2. **Gradual Migration**: Start using AgentMind in existing projects without rewriting everything

3. **Ecosystem Access**: Leverage the rich ecosystems of LangChain, LlamaIndex, and Hugging Face

4. **Flexibility**: Choose the right tool for each task while maintaining AgentMind's simplicity

## Contributing

Have an integration example to share? We welcome contributions!

1. Create a new integration file following the existing pattern
2. Include clear examples and documentation
3. Add installation instructions
4. Submit a pull request

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## Support

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/cym3118288-afk/AgentMind/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/cym3118288-afk/AgentMind/discussions)
- **Documentation**: See main [README.md](../../README.md) for more information

## License

MIT License - see [LICENSE](../../LICENSE) for details.
