"""
LlamaIndex Integration Example

This example demonstrates how to integrate AgentMind with LlamaIndex for
advanced RAG (Retrieval-Augmented Generation) capabilities.

Combines:
- LlamaIndex: Document indexing, vector search, and retrieval
- AgentMind: Multi-agent reasoning and collaboration
"""

import asyncio
from typing import List, Optional

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


class LlamaIndexRetriever(Tool):
    """Wraps LlamaIndex query engine as an AgentMind tool"""

    def __init__(self, query_engine, name: str = "retrieve_documents"):
        self.query_engine = query_engine
        super().__init__(
            name=name,
            description="Retrieve relevant information from the knowledge base using semantic search",
            parameters={
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant information",
                }
            },
        )

    async def execute(self, query: str) -> str:
        """Execute retrieval using LlamaIndex"""
        try:
            # Query the index
            response = await asyncio.to_thread(self.query_engine.query, query)
            return str(response)
        except Exception as e:
            return f"Error retrieving documents: {str(e)}"


# Example 1: Basic RAG with LlamaIndex and AgentMind
async def example_basic_rag():
    """Use LlamaIndex for retrieval and AgentMind for multi-agent reasoning"""
    print("\n=== Example 1: Basic RAG with LlamaIndex ===\n")

    try:
        from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document
        from llama_index.core.node_parser import SimpleNodeParser

        # Create sample documents
        documents = [
            Document(
                text="AgentMind is a lightweight multi-agent framework for Python. It supports multiple LLM providers including Ollama, OpenAI, and Anthropic."
            ),
            Document(
                text="The framework features built-in memory management, tool systems, and async-first architecture for concurrent agent collaboration."
            ),
            Document(
                text="AgentMind is designed to be production-ready with comprehensive error handling, type hints, and extensive testing."
            ),
            Document(
                text="Key features include multi-agent orchestration, flexible LLM support, memory backends, and extensible tool system."
            ),
        ]

        # Create LlamaIndex
        index = VectorStoreIndex.from_documents(documents)
        query_engine = index.as_query_engine()

        # Create retrieval tool
        retriever = LlamaIndexRetriever(query_engine)

        # Create AgentMind with RAG capabilities
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # Create RAG agent
        rag_agent = Agent(
            name="RAG_Expert",
            role="rag_specialist",
            system_prompt="You are an expert at answering questions using retrieved documents. Always base your answers on the retrieved information and cite sources when possible.",
            tools=[retriever],
        )

        mind.add_agent(rag_agent)

        # Query the system
        questions = [
            "What is AgentMind?",
            "What LLM providers does it support?",
            "What are the key features?",
        ]

        for question in questions:
            print(f"\nQuestion: {question}")
            result = await mind.collaborate(question, max_rounds=2)
            print(f"Answer: {result}\n")

    except ImportError:
        print("LlamaIndex not installed. Install with: pip install llama-index")


# Example 2: Multi-agent RAG system
async def example_multi_agent_rag():
    """Multiple specialized agents working with LlamaIndex retrieval"""
    print("\n=== Example 2: Multi-Agent RAG System ===\n")

    try:
        from llama_index.core import VectorStoreIndex, Document

        # Create knowledge base
        tech_docs = [
            Document(
                text="Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms."
            ),
            Document(
                text="JavaScript is the language of the web, running in browsers and on servers via Node.js. It's essential for modern web development."
            ),
            Document(
                text="Rust is a systems programming language focused on safety, speed, and concurrency. It prevents memory errors at compile time."
            ),
            Document(
                text="Go is designed for building scalable network services and cloud applications. It features built-in concurrency support."
            ),
        ]

        # Create index
        index = VectorStoreIndex.from_documents(tech_docs)
        query_engine = index.as_query_engine()

        # Create retrieval tool
        retriever = LlamaIndexRetriever(query_engine, name="search_tech_docs")

        # Create AgentMind system
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # Retriever agent
        retriever_agent = Agent(
            name="Retriever",
            role="retriever",
            system_prompt="You retrieve relevant information from the knowledge base. Focus on finding accurate, relevant documents.",
            tools=[retriever],
        )

        # Analyzer agent
        analyzer = Agent(
            name="Analyzer",
            role="analyst",
            system_prompt="You analyze retrieved information and extract key insights. Identify patterns and important details.",
        )

        # Synthesizer agent
        synthesizer = Agent(
            name="Synthesizer",
            role="synthesizer",
            system_prompt="You synthesize information from multiple sources into clear, comprehensive answers.",
        )

        mind.add_agent(retriever_agent)
        mind.add_agent(analyzer)
        mind.add_agent(synthesizer)

        # Collaborate on complex query
        result = await mind.collaborate(
            "Compare Python and Rust for systems programming. What are the trade-offs?",
            max_rounds=3,
        )

        print(f"Result: {result}")

    except ImportError:
        print("LlamaIndex not installed. Install with: pip install llama-index")


# Example 3: Document analysis pipeline
async def example_document_analysis():
    """Analyze documents using LlamaIndex indexing and AgentMind reasoning"""
    print("\n=== Example 3: Document Analysis Pipeline ===\n")

    try:
        from llama_index.core import VectorStoreIndex, Document

        # Simulate a collection of research papers
        papers = [
            Document(
                text="Study 1: Machine learning models show 85% accuracy in predicting customer churn. Key factors include usage frequency and support tickets."
            ),
            Document(
                text="Study 2: Deep learning approaches achieve 92% accuracy but require 10x more training data and computational resources."
            ),
            Document(
                text="Study 3: Ensemble methods combining multiple models reach 89% accuracy with better interpretability than deep learning."
            ),
            Document(
                text="Study 4: Feature engineering is critical - domain-specific features improve accuracy by 15% across all model types."
            ),
        ]

        # Index the papers
        index = VectorStoreIndex.from_documents(papers)
        query_engine = index.as_query_engine()

        # Create tools
        paper_retriever = LlamaIndexRetriever(query_engine, name="search_papers")

        # Create analysis team
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # Literature reviewer
        reviewer = Agent(
            name="Reviewer",
            role="literature_reviewer",
            system_prompt="You review academic papers and extract key findings, methodologies, and results.",
            tools=[paper_retriever],
        )

        # Statistician
        statistician = Agent(
            name="Statistician",
            role="statistician",
            system_prompt="You analyze numerical results, compare metrics, and identify statistical patterns.",
        )

        # Synthesizer
        synthesizer = Agent(
            name="Synthesizer",
            role="research_synthesizer",
            system_prompt="You synthesize findings from multiple studies into coherent insights and recommendations.",
        )

        mind.add_agent(reviewer)
        mind.add_agent(statistician)
        mind.add_agent(synthesizer)

        # Analyze the literature
        result = await mind.collaborate(
            "What are the most effective approaches for predicting customer churn based on these studies?",
            max_rounds=3,
        )

        print(f"Analysis: {result}")

    except ImportError:
        print("LlamaIndex not installed. Install with: pip install llama-index")


# Example 4: Hybrid search with metadata filtering
async def example_hybrid_search():
    """Advanced RAG with metadata filtering and multi-agent processing"""
    print("\n=== Example 4: Hybrid Search with Metadata ===\n")

    try:
        from llama_index.core import VectorStoreIndex, Document

        # Documents with metadata
        documents = [
            Document(
                text="Q1 2024 revenue increased 25% year-over-year to $50M.",
                metadata={"type": "financial", "quarter": "Q1", "year": 2024},
            ),
            Document(
                text="Q2 2024 revenue reached $55M, showing continued growth momentum.",
                metadata={"type": "financial", "quarter": "Q2", "year": 2024},
            ),
            Document(
                text="Customer satisfaction scores improved from 4.2 to 4.5 in Q1 2024.",
                metadata={"type": "customer", "quarter": "Q1", "year": 2024},
            ),
            Document(
                text="New product launch in Q2 2024 exceeded expectations with 10K users in first month.",
                metadata={"type": "product", "quarter": "Q2", "year": 2024},
            ),
        ]

        # Create index
        index = VectorStoreIndex.from_documents(documents)
        query_engine = index.as_query_engine()

        # Create specialized retrievers
        financial_retriever = LlamaIndexRetriever(query_engine, name="search_financial_data")

        # Create AgentMind system
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # Financial analyst
        financial_analyst = Agent(
            name="Financial_Analyst",
            role="financial_analyst",
            system_prompt="You analyze financial data and identify trends, growth patterns, and key metrics.",
            tools=[financial_retriever],
        )

        # Business strategist
        strategist = Agent(
            name="Strategist",
            role="business_strategist",
            system_prompt="You provide strategic insights based on financial and operational data.",
        )

        mind.add_agent(financial_analyst)
        mind.add_agent(strategist)

        # Query the system
        result = await mind.collaborate(
            "Analyze our 2024 performance and provide strategic recommendations.", max_rounds=3
        )

        print(f"Strategic Analysis: {result}")

    except ImportError:
        print("LlamaIndex not installed. Install with: pip install llama-index")


# Example 5: Real-time document ingestion
async def example_realtime_ingestion():
    """Demonstrate adding documents to index and querying in real-time"""
    print("\n=== Example 5: Real-time Document Ingestion ===\n")

    try:
        from llama_index.core import VectorStoreIndex, Document

        # Start with empty index
        initial_docs = [Document(text="AgentMind version 1.0 released with core features.")]

        index = VectorStoreIndex.from_documents(initial_docs)

        # Create AgentMind system
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # Create agent with dynamic retriever
        query_engine = index.as_query_engine()
        retriever = LlamaIndexRetriever(query_engine)

        agent = Agent(
            name="Knowledge_Agent",
            role="knowledge_specialist",
            system_prompt="You answer questions based on the latest information in the knowledge base.",
            tools=[retriever],
        )

        mind.add_agent(agent)

        # Query 1
        print("Query 1: What versions are available?")
        result1 = await mind.collaborate("What versions are available?", max_rounds=1)
        print(f"Answer: {result1}\n")

        # Add new document
        print("Adding new document about version 2.0...")
        new_doc = Document(
            text="AgentMind version 2.0 released with advanced features including self-improvement and template marketplace."
        )
        index.insert(new_doc)

        # Update query engine
        query_engine = index.as_query_engine()
        retriever.query_engine = query_engine

        # Query 2
        print("\nQuery 2: What versions are available now?")
        result2 = await mind.collaborate("What versions are available?", max_rounds=1)
        print(f"Answer: {result2}")

    except ImportError:
        print("LlamaIndex not installed. Install with: pip install llama-index")


async def main():
    """Run all LlamaIndex integration examples"""
    print("=" * 60)
    print("AgentMind + LlamaIndex Integration Examples")
    print("=" * 60)

    await example_basic_rag()
    await example_multi_agent_rag()
    await example_document_analysis()
    await example_hybrid_search()
    await example_realtime_ingestion()

    print("\n" + "=" * 60)
    print("LlamaIndex integration examples completed!")
    print("=" * 60)
    print("\nNote: These examples require LlamaIndex to be installed:")
    print("  pip install llama-index")


if __name__ == "__main__":
    asyncio.run(main())
