"""
LangChain Integration Example

This example demonstrates how to use AgentMind agents with LangChain chains,
combining the strengths of both frameworks:
- AgentMind: Multi - agent orchestration and collaboration
- LangChain: Rich ecosystem of chains, tools, and integrations
"""

import asyncio
from typing import Any, Dict, List

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


# LangChain integration wrapper
class LangChainToolWrapper(Tool):
    """Wraps a LangChain tool for use in AgentMind"""

    def __init__(self, langchain_tool):
        self.lc_tool = langchain_tool
        super().__init__(
            name=langchain_tool.name,
            description=langchain_tool.description,
            parameters=self._extract_parameters(langchain_tool),
        )

    def _extract_parameters(self, tool) -> Dict[str, Any]:
        """Extract parameter schema from LangChain tool"""
        if hasattr(tool, "args_schema") and tool.args_schema:
            schema = tool.args_schema.schema()
            return schema.get("properties", {})
        return {"input": {"type": "string", "description": "Tool input"}}

    async def execute(self, **kwargs) -> str:
        """Execute the LangChain tool"""
        try:
            # LangChain tools typically expect 'input' parameter
            if len(kwargs) == 1 and "input" not in kwargs:
                input_value = list(kwargs.values())[0]
            else:
                input_value = kwargs.get("input", str(kwargs))

            # Run synchronous LangChain tool
            result = await asyncio.to_thread(self.lc_tool.run, input_value)
            return str(result)
        except Exception as e:
            return f"Error executing LangChain tool: {str(e)}"


class AgentMindChain:
    """
    A LangChain - compatible chain that uses AgentMind for multi - agent collaboration.
    Can be used within LangChain pipelines.
    """

    def __init__(self, mind: AgentMind, max_rounds: int = 3):
        self.mind = mind
        self.max_rounds = max_rounds

    async def arun(self, input_text: str) -> str:
        """Async run compatible with LangChain"""
        result = await self.mind.collaborate(input_text, max_rounds=self.max_rounds)
        return result

    def run(self, input_text: str) -> str:
        """Sync run compatible with LangChain"""
        return asyncio.run(self.arun(input_text))

    async def __call__(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Make it callable like a LangChain chain"""
        input_text = inputs.get("input", inputs.get("question", str(inputs)))
        result = await self.arun(input_text)
        return {"output": result}


# Example 1: Using LangChain tools in AgentMind
async def example_langchain_tools_in_agentmind():
    """Use LangChain's rich tool ecosystem within AgentMind agents"""
    print("\n=== Example 1: LangChain Tools in AgentMind ===\n")

    try:
        # Import LangChain tools (optional dependency)
        from langchain.tools import DuckDuckGoSearchRun, WikipediaQueryRun
        from langchain.utilities import WikipediaAPIWrapper

        # Create LangChain tools
        search_tool = DuckDuckGoSearchRun()
        wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

        # Wrap them for AgentMind
        am_search = LangChainToolWrapper(search_tool)
        am_wiki = LangChainToolWrapper(wiki_tool)

        # Create AgentMind setup
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # Create researcher agent with LangChain tools
        researcher = Agent(
            name="Researcher",
            role="research",
            system_prompt="You are a thorough researcher. Use search and Wikipedia tools to find accurate information.",
            tools=[am_search, am_wiki],
        )

        mind.add_agent(researcher)

        # Collaborate using LangChain tools
        result = await mind.collaborate(
            "What are the latest developments in quantum computing?", max_rounds=2
        )

        print(f"Result: {result}")

    except ImportError:
        print("LangChain not installed. Install with: pip install langchain langchain - community")


# Example 2: Using AgentMind within LangChain chains
async def example_agentmind_in_langchain():
    """Use AgentMind as a component in LangChain pipelines"""
    print("\n=== Example 2: AgentMind in LangChain Chains ===\n")

    try:
        pass

        # Create AgentMind multi - agent system
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # Add specialized agents
        analyst = Agent(
            name="Analyst",
            role="analyst",
            system_prompt="You analyze problems and break them down into components.",
        )

        solver = Agent(
            name="Solver",
            role="solver",
            system_prompt="You provide practical solutions to problems.",
        )

        mind.add_agent(analyst)
        mind.add_agent(solver)

        # Create AgentMind chain
        agentmind_chain = AgentMindChain(mind, max_rounds=2)

        # Use in LangChain pipeline
        result = await agentmind_chain.arun("How can I improve my Python code performance?")

        print(f"AgentMind Chain Result: {result}")

    except ImportError:
        print("LangChain not installed. Install with: pip install langchain")


# Example 3: Hybrid approach - LangChain for retrieval, AgentMind for reasoning
async def example_hybrid_rag():
    """Combine LangChain's RAG capabilities with AgentMind's multi - agent reasoning"""
    print("\n=== Example 3: Hybrid RAG System ===\n")

    try:
        from langchain.schema import Document

        # Simulate document retrieval (in real scenario, use vector store)
        documents = [
            Document(
                page_content="AgentMind is a lightweight multi - agent framework.",
                metadata={"source": "docs"},
            ),
            Document(
                page_content="It supports Ollama, OpenAI, and Anthropic models.",
                metadata={"source": "docs"},
            ),
            Document(
                page_content="AgentMind has built - in memory and tool systems.",
                metadata={"source": "docs"},
            ),
        ]

        # Create retrieval tool for AgentMind
        class DocumentRetriever(Tool):
            def __init__(self, docs: List[Document]):
                self.docs = docs
                super().__init__(
                    name="retrieve_documents",
                    description="Retrieve relevant documents based on a query",
                    parameters={"query": {"type": "string", "description": "Search query"}},
                )

            async def execute(self, query: str) -> str:
                # Simple keyword matching (use vector search in production)
                relevant = [
                    doc.page_content
                    for doc in self.docs
                    if query.lower() in doc.page_content.lower()
                ]
                return "\n".join(relevant) if relevant else "No relevant documents found."

        # Create AgentMind with retrieval
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        retriever_tool = DocumentRetriever(documents)

        rag_agent = Agent(
            name="RAG_Agent",
            role="rag_specialist",
            system_prompt="You answer questions using retrieved documents. Always cite your sources.",
            tools=[retriever_tool],
        )

        mind.add_agent(rag_agent)

        result = await mind.collaborate("What LLM providers does AgentMind support?", max_rounds=2)

        print(f"RAG Result: {result}")

    except ImportError:
        print("LangChain not installed. Install with: pip install langchain")


# Example 4: Sequential chain with AgentMind
async def example_sequential_processing():
    """Use AgentMind for complex multi - step processing within LangChain"""
    print("\n=== Example 4: Sequential Processing ===\n")

    # Create specialized AgentMind systems for each step
    llm = OllamaProvider(model="llama3.2")

    # Step 1: Research team
    research_mind = AgentMind(llm_provider=llm)
    researcher = Agent(
        name="Researcher",
        role="research",
        system_prompt="You gather information and facts about topics.",
    )
    research_mind.add_agent(researcher)

    # Step 2: Analysis team
    analysis_mind = AgentMind(llm_provider=llm)
    analyst = Agent(
        name="Analyst",
        role="analyst",
        system_prompt="You analyze information and identify key insights.",
    )
    analysis_mind.add_agent(analyst)

    # Step 3: Writing team
    writing_mind = AgentMind(llm_provider=llm)
    writer = Agent(
        name="Writer",
        role="writer",
        system_prompt="You write clear, engaging content based on analysis.",
    )
    writing_mind.add_agent(writer)

    # Execute sequential pipeline
    topic = "The future of AI agents"

    print(f"Processing topic: {topic}\n")

    # Step 1: Research
    research_result = await research_mind.collaborate(
        f"Research key facts about: {topic}", max_rounds=1
    )
    print(f"Research: {research_result[:200]}...\n")

    # Step 2: Analysis
    analysis_result = await analysis_mind.collaborate(
        f"Analyze this research and identify key insights: {research_result}", max_rounds=1
    )
    print(f"Analysis: {analysis_result[:200]}...\n")

    # Step 3: Writing
    final_result = await writing_mind.collaborate(
        f"Write a brief article based on this analysis: {analysis_result}", max_rounds=1
    )
    print(f"Final Article: {final_result}")


async def main():
    """Run all integration examples"""
    print("=" * 60)
    print("AgentMind + LangChain Integration Examples")
    print("=" * 60)

    await example_langchain_tools_in_agentmind()
    await example_agentmind_in_langchain()
    await example_hybrid_rag()
    await example_sequential_processing()

    print("\n" + "=" * 60)
    print("Integration examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
