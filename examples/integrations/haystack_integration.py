"""
Haystack Integration Example

This example demonstrates how to integrate AgentMind with Haystack for
building production - ready NLP pipelines with multi - agent reasoning.

Combines:
- Haystack: Document stores, retrievers, and NLP pipelines
- AgentMind: Multi - agent orchestration and collaboration
"""

import asyncio

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


class HaystackRetrieverTool(Tool):
    """Wraps a Haystack retriever as an AgentMind tool"""

    def __init__(self, retriever, name: str = "retrieve_documents"):
        self.retriever = retriever
        super().__init__(
            name=name,
            description="Retrieve relevant documents from the document store using Haystack",
            parameters={
                "query": {"type": "string", "description": "The search query"},
                "top_k": {
                    "type": "integer",
                    "description": "Number of documents to retrieve",
                    "default": 3,
                },
            },
        )

    async def execute(self, query: str, top_k: int = 3) -> str:
        """Execute retrieval using Haystack"""
        try:
            # Run Haystack retriever
            results = await asyncio.to_thread(self.retriever.run, query=query, top_k=top_k)

            # Format results
            documents = results.get("documents", [])
            if not documents:
                return "No relevant documents found."

            formatted = []
            for i, doc in enumerate(documents, 1):
                content = doc.content if hasattr(doc, "content") else str(doc)
                score = doc.score if hasattr(doc, "score") else "N / A"
                formatted.append(f"[{i}] (Score: {score})\n{content}")

            return "\n\n".join(formatted)

        except Exception as e:
            return f"Error retrieving documents: {str(e)}"


# Example 1: Basic document retrieval with Haystack
async def example_basic_retrieval():
    """Use Haystack for document retrieval with AgentMind agents"""
    print("\n=== Example 1: Basic Document Retrieval ===\n")

    try:
        from haystack import Document
        from haystack.document_stores.in_memory import InMemoryDocumentStore
        from haystack.components.retrievers.in_memory import InMemoryBM25Retriever

        # Create document store
        document_store = InMemoryDocumentStore()

        # Add documents
        documents = [
            Document(
                content="AgentMind is a lightweight multi - agent framework for Python with minimal dependencies."
            ),
            Document(
                content="The framework supports Ollama, OpenAI, Anthropic, and other LLM providers via LiteLLM."
            ),
            Document(
                content="AgentMind features async - first architecture for true concurrent agent collaboration."
            ),
            Document(
                content="Built - in memory management supports conversation history and context across sessions."
            ),
        ]

        document_store.write_documents(documents)

        # Create retriever
        retriever = InMemoryBM25Retriever(document_store=document_store)

        # Wrap as AgentMind tool
        retriever_tool = HaystackRetrieverTool(retriever)

        # Create AgentMind system
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # Create agent with retrieval capability
        qa_agent = Agent(
            name="QA_Agent",
            role="qa_specialist",
            system_prompt="You answer questions using retrieved documents. Provide accurate, well - sourced answers.",
            tools=[retriever_tool],
        )

        mind.add_agent(qa_agent)

        # Ask questions
        questions = [
            "What is AgentMind?",
            "What LLM providers are supported?",
            "Tell me about the architecture.",
        ]

        for question in questions:
            print(f"\nQ: {question}")
            answer = await mind.collaborate(question, max_rounds=2)
            print(f"A: {answer}\n")

    except ImportError:
        print("Haystack not installed. Install with: pip install haystack - ai")


# Example 2: Multi - agent pipeline with Haystack
async def example_multi_agent_pipeline():
    """Build a multi - agent system using Haystack for retrieval"""
    print("\n=== Example 2: Multi - Agent Pipeline ===\n")

    try:
        from haystack import Document
        from haystack.document_stores.in_memory import InMemoryDocumentStore
        from haystack.components.retrievers.in_memory import InMemoryBM25Retriever

        # Create knowledge base
        document_store = InMemoryDocumentStore()

        tech_docs = [
            Document(
                content="Python 3.12 introduces improved error messages and performance optimizations."
            ),
            Document(
                content="FastAPI is a modern web framework for building APIs with Python 3.7+ based on type hints."
            ),
            Document(
                content="Docker containers provide lightweight, portable application packaging and deployment."
            ),
            Document(
                content="Kubernetes orchestrates containerized applications across clusters of machines."
            ),
            Document(
                content="PostgreSQL is a powerful open - source relational database with advanced features."
            ),
        ]

        document_store.write_documents(tech_docs)

        # Create retriever
        retriever = InMemoryBM25Retriever(document_store=document_store)
        retriever_tool = HaystackRetrieverTool(retriever, name="search_tech_docs")

        # Create multi - agent system
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # Retriever agent
        retriever_agent = Agent(
            name="Retriever",
            role="information_retriever",
            system_prompt="You retrieve relevant technical documentation. Focus on finding accurate information.",
            tools=[retriever_tool],
        )

        # Technical expert
        tech_expert = Agent(
            name="Tech_Expert",
            role="technical_expert",
            system_prompt="You explain technical concepts clearly and provide practical insights.",
        )

        # Architect
        architect = Agent(
            name="Architect",
            role="solution_architect",
            system_prompt="You design solutions and recommend best practices based on technical requirements.",
        )

        mind.add_agent(retriever_agent)
        mind.add_agent(tech_expert)
        mind.add_agent(architect)

        # Complex query requiring multiple agents
        result = await mind.collaborate(
            "I need to build a scalable API service. What technologies should I use and how should I architect it?",
            max_rounds=3,
        )

        print(f"Recommendation: {result}")

    except ImportError:
        print("Haystack not installed. Install with: pip install haystack - ai")


# Example 3: Question answering pipeline
async def example_qa_pipeline():
    """Build a QA system combining Haystack retrieval and AgentMind reasoning"""
    print("\n=== Example 3: Question Answering Pipeline ===\n")

    try:
        from haystack import Document
        from haystack.document_stores.in_memory import InMemoryDocumentStore
        from haystack.components.retrievers.in_memory import InMemoryBM25Retriever

        # Create FAQ document store
        document_store = InMemoryDocumentStore()

        faqs = [
            Document(
                content="Q: How do I install AgentMind? A: Use pip install agentmind or clone from GitHub."
            ),
            Document(
                content="Q: What Python version is required? A: Python 3.8 or higher is required."
            ),
            Document(
                content="Q: Can I use local models? A: Yes, AgentMind supports Ollama for local LLM execution."
            ),
            Document(
                content="Q: How do I add custom tools? A: Extend the Tool base class and implement the execute method."
            ),
            Document(
                content="Q: Is AgentMind production - ready? A: Yes, it includes error handling, testing, and observability features."  # noqa: E501
            ),
        ]

        document_store.write_documents(faqs)

        # Create retriever
        retriever = InMemoryBM25Retriever(document_store=document_store)
        retriever_tool = HaystackRetrieverTool(retriever, name="search_faqs")

        # Create QA system
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # FAQ agent
        faq_agent = Agent(
            name="FAQ_Agent",
            role="support_specialist",
            system_prompt="You answer user questions using the FAQ database. Provide clear, helpful answers.",
            tools=[retriever_tool],
        )

        mind.add_agent(faq_agent)

        # User questions
        user_questions = [
            "How can I get started with AgentMind?",
            "Can I run models locally?",
            "What if I want to add my own tools?",
        ]

        for question in user_questions:
            print(f"\nUser: {question}")
            answer = await mind.collaborate(question, max_rounds=2)
            print(f"Agent: {answer}\n")

    except ImportError:
        print("Haystack not installed. Install with: pip install haystack - ai")


# Example 4: Document processing pipeline
async def example_document_processing():
    """Process and analyze documents using Haystack and AgentMind"""
    print("\n=== Example 4: Document Processing Pipeline ===\n")

    try:
        from haystack import Document
        from haystack.document_stores.in_memory import InMemoryDocumentStore
        from haystack.components.retrievers.in_memory import InMemoryBM25Retriever

        # Simulate customer feedback documents
        document_store = InMemoryDocumentStore()

        feedback = [
            Document(
                content="Customer feedback: The product is great but the UI could be more intuitive.",
                meta={"sentiment": "mixed", "category": "ui"},
            ),
            Document(
                content="Customer feedback: Excellent customer support, resolved my issue quickly.",
                meta={"sentiment": "positive", "category": "support"},
            ),
            Document(
                content="Customer feedback: Performance is slow when handling large datasets.",
                meta={"sentiment": "negative", "category": "performance"},
            ),
            Document(
                content="Customer feedback: Love the new features in the latest release!",
                meta={"sentiment": "positive", "category": "features"},
            ),
            Document(
                content="Customer feedback: Documentation needs improvement, hard to find examples.",
                meta={"sentiment": "negative", "category": "docs"},
            ),
        ]

        document_store.write_documents(feedback)

        # Create retriever
        retriever = InMemoryBM25Retriever(document_store=document_store)
        retriever_tool = HaystackRetrieverTool(retriever, name="search_feedback")

        # Create analysis team
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # Feedback analyzer
        analyzer = Agent(
            name="Analyzer",
            role="feedback_analyzer",
            system_prompt="You analyze customer feedback and identify patterns, issues, and opportunities.",
            tools=[retriever_tool],
        )

        # Product manager
        pm = Agent(
            name="Product_Manager",
            role="product_manager",
            system_prompt="You prioritize issues and create actionable product improvement plans.",
        )

        mind.add_agent(analyzer)
        mind.add_agent(pm)

        # Analyze feedback
        result = await mind.collaborate(
            "Analyze customer feedback and create a prioritized list of improvements.", max_rounds=3
        )

        print(f"Analysis & Recommendations:\n{result}")

    except ImportError:
        print("Haystack not installed. Install with: pip install haystack - ai")


async def main():
    """Run all Haystack integration examples"""
    print("=" * 60)
    print("AgentMind + Haystack Integration Examples")
    print("=" * 60)

    await example_basic_retrieval()
    await example_multi_agent_pipeline()
    await example_qa_pipeline()
    await example_document_processing()

    print("\n" + "=" * 60)
    print("Haystack integration examples completed!")
    print("=" * 60)
    print("\nNote: These examples require Haystack to be installed:")
    print("  pip install haystack - ai")


if __name__ == "__main__":
    asyncio.run(main())
