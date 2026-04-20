# Integration Examples - Complete Guide

This comprehensive guide covers all integration examples and how to use AgentMind with popular AI/ML frameworks.

## Table of Contents

1. [Overview](#overview)
2. [LangChain Integration](#langchain-integration)
3. [LlamaIndex Integration](#llamaindex-integration)
4. [Haystack Integration](#haystack-integration)
5. [OpenAI Assistants Compatibility](#openai-assistants-compatibility)
6. [Hugging Face Integration](#hugging-face-integration)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Overview

AgentMind integrations allow you to:
- Leverage existing tools and ecosystems
- Gradually migrate from other frameworks
- Combine strengths of multiple frameworks
- Access specialized capabilities (RAG, NLP, etc.)

### Integration Philosophy

AgentMind follows these principles for integrations:

1. **Lightweight wrappers**: Minimal overhead, maximum compatibility
2. **Bidirectional**: Use external tools in AgentMind AND use AgentMind in external frameworks
3. **Optional dependencies**: Integrations don't bloat core framework
4. **Production-ready**: All examples are tested and production-grade

## LangChain Integration

### Installation

```bash
pip install langchain langchain-community
```

### Use Case 1: LangChain Tools in AgentMind

Leverage LangChain's rich tool ecosystem within AgentMind agents:

```python
from langchain.tools import DuckDuckGoSearchRun
from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider

# Wrap LangChain tool
class LangChainToolWrapper(Tool):
    def __init__(self, langchain_tool):
        self.lc_tool = langchain_tool
        super().__init__(
            name=langchain_tool.name,
            description=langchain_tool.description,
            parameters=self._extract_parameters(langchain_tool)
        )
    
    async def execute(self, **kwargs) -> str:
        input_value = kwargs.get('input', str(kwargs))
        result = await asyncio.to_thread(self.lc_tool.run, input_value)
        return str(result)

# Use in AgentMind
search_tool = LangChainToolWrapper(DuckDuckGoSearchRun())
agent = Agent(name="Researcher", tools=[search_tool])
```

### Use Case 2: AgentMind in LangChain Chains

Use AgentMind as a component in LangChain pipelines:

```python
class AgentMindChain:
    def __init__(self, mind: AgentMind, max_rounds: int = 3):
        self.mind = mind
        self.max_rounds = max_rounds
    
    async def arun(self, input_text: str) -> str:
        result = await self.mind.collaborate(input_text, max_rounds=self.max_rounds)
        return result

# Use in pipeline
agentmind_chain = AgentMindChain(mind)
result = await agentmind_chain.arun("Your task")
```

### Benefits

- Access to 100+ LangChain tools
- Compatibility with existing LangChain code
- Gradual migration path
- Best of both frameworks

## LlamaIndex Integration

### Installation

```bash
pip install llama-index
```

### Use Case 1: RAG with LlamaIndex

Build advanced RAG systems combining LlamaIndex retrieval with AgentMind reasoning:

```python
from llama_index.core import VectorStoreIndex, Document
from agentmind import Agent, AgentMind

# Create LlamaIndex
documents = [Document(text="Your content here")]
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

# Wrap as AgentMind tool
class LlamaIndexRetriever(Tool):
    def __init__(self, query_engine):
        self.query_engine = query_engine
        super().__init__(
            name="retrieve_documents",
            description="Retrieve relevant information using semantic search",
            parameters={"query": {"type": "string"}}
        )
    
    async def execute(self, query: str) -> str:
        response = await asyncio.to_thread(self.query_engine.query, query)
        return str(response)

# Use in multi-agent system
retriever = LlamaIndexRetriever(query_engine)
agent = Agent(name="RAG_Expert", tools=[retriever])
```

### Use Case 2: Multi-Agent RAG

Multiple agents with specialized retrieval:

```python
# Create specialized indexes
tech_index = VectorStoreIndex.from_documents(tech_docs)
business_index = VectorStoreIndex.from_documents(business_docs)

# Create specialized agents
tech_agent = Agent(
    name="Tech_Expert",
    tools=[LlamaIndexRetriever(tech_index.as_query_engine())]
)

business_agent = Agent(
    name="Business_Analyst",
    tools=[LlamaIndexRetriever(business_index.as_query_engine())]
)

# Collaborate
mind.add_agent(tech_agent)
mind.add_agent(business_agent)
result = await mind.collaborate("Your complex query")
```

### Benefits

- Powerful vector search capabilities
- Document indexing and retrieval
- Semantic search
- Multiple index types (vector, graph, etc.)

## Haystack Integration

### Installation

```bash
pip install haystack-ai
```

### Use Case: Production NLP Pipelines

Build production-ready NLP systems:

```python
from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever

# Create Haystack pipeline
document_store = InMemoryDocumentStore()
document_store.write_documents(documents)
retriever = InMemoryBM25Retriever(document_store=document_store)

# Wrap for AgentMind
class HaystackRetrieverTool(Tool):
    def __init__(self, retriever):
        self.retriever = retriever
        super().__init__(
            name="retrieve_documents",
            description="Retrieve relevant documents using BM25",
            parameters={"query": {"type": "string"}, "top_k": {"type": "integer"}}
        )
    
    async def execute(self, query: str, top_k: int = 3) -> str:
        results = await asyncio.to_thread(
            self.retriever.run,
            query=query,
            top_k=top_k
        )
        documents = results.get("documents", [])
        return "\n\n".join(doc.content for doc in documents)

# Use in AgentMind
retriever_tool = HaystackRetrieverTool(retriever)
agent = Agent(name="QA_Agent", tools=[retriever_tool])
```

### Benefits

- Production-ready components
- Multiple retrieval strategies
- Document processing pipelines
- Scalable architecture

## OpenAI Assistants Compatibility

### Use Case: Drop-in Replacement

Migrate from OpenAI Assistants API to AgentMind:

```python
from examples.integrations.openai_assistants_compat import Assistant

# Create assistant (OpenAI-compatible API)
assistant = Assistant(
    name="Math Tutor",
    instructions="You are a helpful math tutor.",
    model="llama3.2"  # Use any model, not just OpenAI!
)

# Create thread
thread = assistant.threads.create()

# Add message
assistant.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="What is the quadratic formula?"
)

# Create run
run = assistant.threads.runs.create(thread_id=thread.id)

# Wait for completion
while run.status != "completed":
    run = assistant.threads.runs.retrieve(thread.id, run.id)
    await asyncio.sleep(0.5)

# Get messages
messages = assistant.threads.messages.list(thread_id=thread.id)
```

### Benefits

- Familiar API for OpenAI users
- Works with any LLM provider
- No vendor lock-in
- Cost savings with local models

## Hugging Face Integration

### Installation

```bash
pip install transformers torch
```

### Use Case: Local NLP Models

Use Hugging Face models as AgentMind tools:

```python
from transformers import pipeline

# Create HF pipeline
sentiment_pipeline = pipeline("sentiment-analysis")

# Wrap as tool
class HuggingFacePipelineTool(Tool):
    def __init__(self, pipeline, task_name: str):
        self.pipeline = pipeline
        super().__init__(
            name=f"hf_{task_name}",
            description=f"Perform {task_name} using Hugging Face",
            parameters={"text": {"type": "string"}}
        )
    
    async def execute(self, text: str) -> str:
        result = await asyncio.to_thread(self.pipeline, text)
        return str(result)

# Use in AgentMind
sentiment_tool = HuggingFacePipelineTool(sentiment_pipeline, "sentiment_analysis")
agent = Agent(name="Sentiment_Analyst", tools=[sentiment_tool])
```

### Available Tasks

- Sentiment analysis
- Named Entity Recognition (NER)
- Text summarization
- Question answering
- Translation
- Text generation

### Benefits

- Local model execution
- No API costs
- Privacy (data stays local)
- Offline capability

## Best Practices

### 1. Choose the Right Integration

| Need | Use |
|------|-----|
| Rich tool ecosystem | LangChain |
| Advanced RAG | LlamaIndex |
| Production NLP | Haystack |
| OpenAI migration | Assistants Compat |
| Local NLP models | Hugging Face |

### 2. Performance Optimization

```python
# Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=100)
def get_embeddings(text: str):
    return embedding_model.encode(text)

# Use async for I/O operations
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Batch processing
tasks = [process_item(item) for item in items]
results = await asyncio.gather(*tasks)
```

### 3. Error Handling

```python
from agentmind.utils.retry import retry_with_backoff, RetryConfig

# Retry on failures
config = RetryConfig(max_retries=3, initial_delay=1.0)
result = await retry_with_backoff(
    lambda: agent.generate(prompt),
    config
)

# Graceful degradation
try:
    result = await external_api_call()
except Exception as e:
    logger.error(f"External API failed: {e}")
    result = await fallback_method()
```

### 4. Cost Management

```python
from agentmind.utils.observability import CostTracker

# Track costs
tracker = CostTracker()
tracker.start()

# Your code here

tracker.end()
print(f"Total cost: ${tracker.total_cost:.4f}")
print(f"Total tokens: {tracker.total_tokens}")
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Install missing dependencies
pip install langchain langchain-community
pip install llama-index
pip install haystack-ai
pip install transformers torch
```

#### 2. Model Loading Issues

```python
# Specify model explicitly
from transformers import AutoModel, AutoTokenizer

model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
```

#### 3. Async Compatibility

```python
# Wrap sync functions for async
import asyncio

result = await asyncio.to_thread(sync_function, args)
```

#### 4. Memory Issues

```python
# Clear cache periodically
import gc
import torch

gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()
```

### Getting Help

- **Documentation**: Check framework-specific docs
- **Issues**: [GitHub Issues](https://github.com/cym3118288-afk/AgentMind/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cym3118288-afk/AgentMind/discussions)
- **Examples**: See `examples/integrations/` for working code

## Next Steps

1. **Try the examples**: Run integration examples to see them in action
2. **Customize**: Adapt examples to your use case
3. **Contribute**: Share your integration patterns
4. **Deploy**: Take to production with confidence

## Contributing

Have an integration pattern to share? We welcome contributions!

1. Create integration example
2. Add documentation
3. Include tests
4. Submit pull request

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.
