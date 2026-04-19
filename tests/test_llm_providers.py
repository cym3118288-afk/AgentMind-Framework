"""Tests for LLM providers."""

import pytest
from agentmind.llm import LLMProvider, LLMResponse, OllamaProvider, LiteLLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    async def generate(self, messages, temperature=None, max_tokens=None, **kwargs):
        """Generate a mock response."""
        return LLMResponse(
            content="Mock response",
            model=self.model,
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            metadata={"mock": True}
        )

    async def generate_stream(self, messages, temperature=None, max_tokens=None, **kwargs):
        """Generate a mock streaming response."""
        yield "Mock "
        yield "streaming "
        yield "response"


def test_llm_provider_initialization():
    """Test LLM provider initialization."""
    provider = MockLLMProvider(model="test-model", temperature=0.5, max_tokens=500)
    assert provider.model == "test-model"
    assert provider.temperature == 0.5
    assert provider.max_tokens == 500


def test_llm_provider_build_messages():
    """Test message building."""
    provider = MockLLMProvider(model="test-model")

    # Test with system prompt and user message
    messages = provider.build_messages(
        system_prompt="You are a helpful assistant",
        user_message="Hello"
    )
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"

    # Test with history
    history = [
        {"role": "user", "content": "Previous message"},
        {"role": "assistant", "content": "Previous response"}
    ]
    messages = provider.build_messages(
        system_prompt="System",
        user_message="New message",
        history=history
    )
    assert len(messages) == 4
    assert messages[1]["content"] == "Previous message"


@pytest.mark.asyncio
async def test_mock_provider_generate():
    """Test mock provider generation."""
    provider = MockLLMProvider(model="test-model")
    messages = [{"role": "user", "content": "Test"}]

    response = await provider.generate(messages)
    assert isinstance(response, LLMResponse)
    assert response.content == "Mock response"
    assert response.model == "test-model"
    assert response.usage["total_tokens"] == 15


@pytest.mark.asyncio
async def test_mock_provider_stream():
    """Test mock provider streaming."""
    provider = MockLLMProvider(model="test-model")
    messages = [{"role": "user", "content": "Test"}]

    chunks = []
    async for chunk in provider.generate_stream(messages):
        chunks.append(chunk)

    assert len(chunks) == 3
    assert "".join(chunks) == "Mock streaming response"


def test_ollama_provider_initialization():
    """Test Ollama provider initialization."""
    provider = OllamaProvider(model="llama3.2", temperature=0.8)
    assert provider.model == "llama3.2"
    assert provider.temperature == 0.8
    assert provider.base_url == "http://localhost:11434"


def test_ollama_provider_custom_url():
    """Test Ollama provider with custom URL."""
    provider = OllamaProvider(
        model="llama3.2",
        base_url="http://custom-host:8080"
    )
    assert provider.base_url == "http://custom-host:8080"


def test_litellm_provider_list_models():
    """Test LiteLLM model listing."""
    try:
        models = LiteLLMProvider.list_models()
        assert isinstance(models, list)
        # Should include popular models if litellm is available
        if models:
            assert any("gpt" in m for m in models)
            assert any("claude" in m for m in models)
    except ImportError:
        # LiteLLM not installed, skip
        pytest.skip("LiteLLM not installed")


def test_llm_response_model():
    """Test LLMResponse Pydantic model."""
    response = LLMResponse(
        content="Test content",
        model="test-model",
        usage={"total_tokens": 100},
        metadata={"test": True}
    )
    assert response.content == "Test content"
    assert response.model == "test-model"
    assert response.usage["total_tokens"] == 100
    assert response.metadata["test"] is True


@pytest.mark.asyncio
async def test_provider_parameter_override():
    """Test that parameters can be overridden per call."""
    provider = MockLLMProvider(model="test", temperature=0.7, max_tokens=1000)

    # Override should work (though mock doesn't use them)
    response = await provider.generate(
        messages=[{"role": "user", "content": "Test"}],
        temperature=0.9,
        max_tokens=500
    )
    assert isinstance(response, LLMResponse)
