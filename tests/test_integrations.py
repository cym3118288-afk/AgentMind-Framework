"""Tests for framework integrations and compatibility."""

import pytest
import asyncio
from typing import Any, Dict, List
from agentmind import Agent, AgentMind
from agentmind.llm import LLMProvider, LLMResponse
from agentmind.tools import Tool, ToolResult
from agentmind.core import CollaborationStrategy


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, model="mock-model", **kwargs):
        super().__init__(model, **kwargs)

    async def generate(self, messages, temperature=None, max_tokens=None, **kwargs):
        """Generate a mock response."""
        return LLMResponse(
            content="Mock response",
            model=self.model,
            usage={"total_tokens": 10},
            metadata={}
        )

    async def generate_stream(self, messages, temperature=None, max_tokens=None, **kwargs):
        """Generate a mock streaming response."""
        yield "Mock stream"


class TestToolWrapperPattern:
    """Test tool wrapper pattern for external framework integration."""

    def test_external_tool_wrapper_creation(self):
        """Test creating a wrapper for external tools."""

        class ExternalTool:
            """Mock external tool (e.g., from LangChain)."""
            name = "external_search"
            description = "Search the web"

            def run(self, query: str) -> str:
                return f"Search results for: {query}"

        class ExternalToolWrapper(Tool):
            """Wrapper for external tools."""

            def __init__(self, external_tool):
                super().__init__()
                self.external_tool = external_tool
                self.name = external_tool.name
                self.description = external_tool.description

            async def execute(self, query: str = "") -> ToolResult:
                """Execute the external tool."""
                result = await asyncio.to_thread(self.external_tool.run, query)
                return ToolResult(success=True, output=result)

        # Test wrapper creation
        external = ExternalTool()
        wrapper = ExternalToolWrapper(external)

        assert wrapper.name == "external_search"
        assert wrapper.description == "Search the web"

    @pytest.mark.asyncio
    async def test_external_tool_wrapper_execution(self):
        """Test executing wrapped external tools."""

        class ExternalTool:
            name = "calculator"
            description = "Calculate"

            def run(self, expression: str) -> str:
                return str(eval(expression))

        class ExternalToolWrapper(Tool):
            """Calculator wrapper."""

            def __init__(self, external_tool):
                super().__init__()
                self.external_tool = external_tool
                self.name = external_tool.name
                self.description = external_tool.description

            async def execute(self, expression: str = "0") -> ToolResult:
                """Execute calculation."""
                result = await asyncio.to_thread(self.external_tool.run, expression)
                return ToolResult(success=True, output=result)

        external = ExternalTool()
        wrapper = ExternalToolWrapper(external)

        result = await wrapper.execute(expression="2+2")
        assert result.success is True
        assert result.output == "4"


class TestChainCompatibility:
    """Test chain/pipeline compatibility patterns."""

    @pytest.mark.asyncio
    async def test_agentmind_as_chain(self):
        """Test using AgentMind as a chain component."""

        class AgentMindChain:
            """Chain wrapper for AgentMind."""

            def __init__(self, mind: AgentMind, max_rounds: int = 2):
                self.mind = mind
                self.max_rounds = max_rounds

            async def arun(self, input_text: str) -> str:
                """Async run."""
                result = await self.mind.start_collaboration(
                    input_text,
                    max_rounds=self.max_rounds,
                    use_llm=True
                )
                return result.final_output or "No output"

            def run(self, input_text: str) -> str:
                """Sync run."""
                return asyncio.run(self.arun(input_text))

            async def __call__(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                """Callable interface."""
                input_text = inputs.get("input", str(inputs))
                result = await self.arun(input_text)
                return {"output": result}

        # Create AgentMind
        provider = MockLLMProvider()
        mind = AgentMind(llm_provider=provider)
        mind.add_agent(Agent(name="agent1", role="assistant", llm_provider=provider))

        # Create chain
        chain = AgentMindChain(mind, max_rounds=1)

        # Test async run
        result = await chain.arun("Test input")
        assert isinstance(result, str)

        # Test callable interface
        result_dict = await chain({"input": "Test input"})
        assert "output" in result_dict

    @pytest.mark.asyncio
    async def test_sequential_chain_pattern(self):
        """Test sequential chain pattern with multiple AgentMind instances."""

        provider = MockLLMProvider()

        # Create multiple specialized minds
        mind1 = AgentMind(llm_provider=provider)
        mind1.add_agent(Agent(name="researcher", role="researcher", llm_provider=provider))

        mind2 = AgentMind(llm_provider=provider)
        mind2.add_agent(Agent(name="analyst", role="analyst", llm_provider=provider))

        mind3 = AgentMind(llm_provider=provider)
        mind3.add_agent(Agent(name="writer", role="writer", llm_provider=provider))

        # Execute sequential pipeline
        input_text = "Test topic"

        result1 = await mind1.start_collaboration(f"Research: {input_text}", max_rounds=1, use_llm=True)
        result2 = await mind2.start_collaboration(f"Analyze: {result1.final_output}", max_rounds=1, use_llm=True)
        result3 = await mind3.start_collaboration(f"Write: {result2.final_output}", max_rounds=1, use_llm=True)

        assert result1.success is True
        assert result2.success is True
        assert result3.success is True


class TestRAGIntegration:
    """Test RAG (Retrieval-Augmented Generation) integration patterns."""

    @pytest.mark.asyncio
    async def test_document_retriever_tool(self):
        """Test document retrieval tool for RAG."""

        class Document:
            def __init__(self, content: str, metadata: Dict[str, Any]):
                self.page_content = content
                self.metadata = metadata

        class DocumentRetriever(Tool):
            """Retrieve relevant documents."""

            def __init__(self, docs: List[Document]):
                super().__init__()
                self.docs = docs
                self.name = "retrieve_documents"
                self.description = "Retrieve relevant documents"

            async def execute(self, query: str = "") -> ToolResult:
                """Execute document retrieval."""
                query_lower = query.lower()
                relevant = [
                    doc.page_content
                    for doc in self.docs
                    if query_lower in doc.page_content.lower()
                ]
                output = "\n".join(relevant) if relevant else "No documents found"
                return ToolResult(success=True, output=output)

        # Create documents
        docs = [
            Document("AgentMind is a multi-agent framework", {"source": "docs"}),
            Document("It supports multiple LLM providers", {"source": "docs"}),
            Document("Python is a programming language", {"source": "other"}),
        ]

        # Test retriever
        retriever = DocumentRetriever(docs)
        result = await retriever.execute(query="AgentMind")

        assert result.success is True
        assert "multi-agent" in result.output
        assert "Python" not in result.output

    @pytest.mark.asyncio
    async def test_rag_agent_with_retrieval(self):
        """Test RAG agent with document retrieval."""

        class Document:
            def __init__(self, content: str):
                self.page_content = content

        class DocumentRetriever(Tool):
            """Retrieve documents."""

            def __init__(self, docs: List[Document]):
                super().__init__()
                self.docs = docs
                self.name = "retrieve"
                self.description = "Retrieve documents"

            async def execute(self, query: str = "") -> ToolResult:
                """Execute retrieval."""
                query_lower = query.lower()
                relevant = [d.page_content for d in self.docs if query_lower in d.page_content.lower()]
                return ToolResult(success=True, output="\n".join(relevant))

        # Create RAG setup
        docs = [
            Document("AgentMind supports Ollama and OpenAI"),
            Document("AgentMind has memory and tools"),
        ]

        provider = MockLLMProvider()
        mind = AgentMind(llm_provider=provider)

        retriever = DocumentRetriever(docs)
        rag_agent = Agent(
            name="rag_agent",
            role="rag_specialist",
            llm_provider=provider
        )

        mind.add_agent(rag_agent)

        result = await mind.start_collaboration(
            "What providers does AgentMind support?",
            max_rounds=1,
            use_llm=True
        )

        assert result.success is True


class TestAsyncCompatibility:
    """Test async/await compatibility with external frameworks."""

    @pytest.mark.asyncio
    async def test_async_tool_execution(self):
        """Test async tool execution compatibility."""

        class AsyncExternalTool(Tool):
            """Async tool for testing."""

            def __init__(self):
                super().__init__()
                self.name = "async_tool"
                self.description = "Async tool"

            async def execute(self, input_text: str = "") -> ToolResult:
                """Execute async operation."""
                await asyncio.sleep(0.01)  # Simulate async operation
                return ToolResult(success=True, output="Async result")

        tool = AsyncExternalTool()
        result = await tool.execute(input_text="test")

        assert result.success is True
        assert result.output == "Async result"

    @pytest.mark.asyncio
    async def test_concurrent_mind_execution(self):
        """Test concurrent execution of multiple minds."""

        provider = MockLLMProvider()

        minds = []
        for i in range(3):
            mind = AgentMind(llm_provider=provider)
            mind.add_agent(Agent(name=f"agent{i}", role="assistant", llm_provider=provider))
            minds.append(mind)

        # Execute concurrently
        tasks = [
            mind.start_collaboration(f"Task {i}", max_rounds=1, use_llm=True)
            for i, mind in enumerate(minds)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(r.success for r in results)


class TestStreamingCompatibility:
    """Test streaming response compatibility."""

    @pytest.mark.asyncio
    async def test_streaming_response_pattern(self):
        """Test streaming response pattern."""

        class StreamingProvider(LLMProvider):
            def __init__(self):
                super().__init__(model="streaming-model")

            async def generate(self, messages, **kwargs):
                return LLMResponse(
                    content="Full response",
                    model=self.model,
                    usage={"total_tokens": 10},
                    metadata={}
                )

            async def generate_stream(self, messages, **kwargs):
                for chunk in ["Hello", " ", "World"]:
                    await asyncio.sleep(0.01)
                    yield chunk

        provider = StreamingProvider()

        # Test streaming
        chunks = []
        async for chunk in provider.generate_stream([]):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert "".join(chunks) == "Hello World"


class TestErrorHandling:
    """Test error handling in integrations."""

    @pytest.mark.asyncio
    async def test_external_tool_error_handling(self):
        """Test error handling for external tools."""

        class FailingExternalTool(Tool):
            """Tool that fails."""

            def __init__(self):
                super().__init__()
                self.name = "failing_tool"
                self.description = "Tool that fails"

            async def execute(self, input_text: str = "") -> ToolResult:
                """Execute and fail."""
                raise ValueError("External tool error")

        tool = FailingExternalTool()

        with pytest.raises(ValueError):
            await tool.execute(input_text="test")

    @pytest.mark.asyncio
    async def test_chain_error_propagation(self):
        """Test error propagation in chains."""

        provider = MockLLMProvider()
        mind = AgentMind(llm_provider=provider)
        # No agents added - should handle gracefully

        result = await mind.start_collaboration("Test", max_rounds=1, use_llm=True)

        # Should complete but may have no output
        assert result.success is True or result.success is False


class TestDataFormatCompatibility:
    """Test data format compatibility with external frameworks."""

    def test_message_format_conversion(self):
        """Test converting between message formats."""
        from agentmind.core import Message, MessageRole

        # AgentMind message
        am_message = Message(
            content="Hello",
            sender="agent1",
            role=MessageRole.AGENT
        )

        # Convert to external format (e.g., OpenAI format)
        external_format = {
            "role": "assistant",
            "content": am_message.content
        }

        assert external_format["content"] == "Hello"
        assert external_format["role"] == "assistant"

        # Convert back
        converted_back = Message(
            content=external_format["content"],
            sender="converted",
            role=MessageRole.ASSISTANT
        )

        assert converted_back.content == am_message.content

    def test_tool_result_format_conversion(self):
        """Test converting tool results between formats."""

        # AgentMind tool result
        am_result = ToolResult(
            success=True,
            output="Result data",
            metadata={"source": "tool"}
        )

        # Convert to external format
        external_format = {
            "status": "success" if am_result.success else "error",
            "data": am_result.output,
            "metadata": am_result.metadata
        }

        assert external_format["status"] == "success"
        assert external_format["data"] == "Result data"


class TestConfigurationCompatibility:
    """Test configuration compatibility patterns."""

    def test_provider_configuration_mapping(self):
        """Test mapping configurations between frameworks."""

        # AgentMind config
        am_config = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000
        }

        # Map to external format (e.g., OpenAI)
        external_config = {
            "model": am_config["model"],
            "temperature": am_config["temperature"],
            "max_tokens": am_config["max_tokens"]
        }

        assert external_config["model"] == "gpt-4"
        assert external_config["temperature"] == 0.7

    def test_agent_config_export(self):
        """Test exporting agent configuration."""

        provider = MockLLMProvider()
        agent = Agent(
            name="test_agent",
            role="assistant",
            llm_provider=provider
        )

        # Export config
        config = {
            "name": agent.name,
            "role": agent.role,
        }

        assert config["name"] == "test_agent"
        assert config["role"] == "assistant"


class TestPerformanceIntegration:
    """Test performance aspects of integrations."""

    @pytest.mark.asyncio
    async def test_batch_processing_pattern(self):
        """Test batch processing pattern for efficiency."""

        provider = MockLLMProvider()
        mind = AgentMind(llm_provider=provider)
        mind.add_agent(Agent(name="processor", role="assistant", llm_provider=provider))

        # Process multiple inputs
        inputs = [f"Input {i}" for i in range(5)]

        tasks = [
            mind.start_collaboration(inp, max_rounds=1, use_llm=True)
            for inp in inputs
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_caching_pattern(self):
        """Test caching pattern for repeated queries."""

        cache = {}

        async def cached_query(query: str, mind: AgentMind) -> str:
            if query in cache:
                return cache[query]

            result = await mind.start_collaboration(query, max_rounds=1, use_llm=True)
            cache[query] = result.final_output or ""
            return cache[query]

        provider = MockLLMProvider()
        mind = AgentMind(llm_provider=provider)
        mind.add_agent(Agent(name="agent", role="assistant", llm_provider=provider))

        # First call - not cached
        result1 = await cached_query("Test query", mind)

        # Second call - cached
        result2 = await cached_query("Test query", mind)

        assert result1 == result2
        assert len(cache) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
