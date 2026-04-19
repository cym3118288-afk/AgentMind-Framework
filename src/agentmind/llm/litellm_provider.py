"""LiteLLM provider for cloud-based LLM inference.

This module provides integration with LiteLLM, supporting 100+ models
from OpenAI, Anthropic, Google, Azure, and more.
"""

from typing import Any, AsyncIterator, Dict, List, Optional

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

from .provider import LLMProvider, LLMResponse


class LiteLLMProvider(LLMProvider):
    """LiteLLM provider for cloud model inference.

    Supports 100+ models via LiteLLM including:
    - OpenAI: gpt-4, gpt-3.5-turbo
    - Anthropic: claude-3-opus, claude-3-sonnet
    - Google: gemini-pro
    - Azure OpenAI
    - And many more

    Example:
        >>> provider = LiteLLMProvider(model="gpt-4")
        >>> messages = [{"role": "user", "content": "Hello!"}]
        >>> response = await provider.generate(messages)
        >>> print(response.content)
    """

    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """Initialize LiteLLM provider.

        Args:
            model: Model identifier (e.g., "gpt-4", "claude-3-opus-20240229")
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            api_key: Optional API key (can also use environment variables)
            **kwargs: Additional LiteLLM parameters

        Raises:
            ImportError: If litellm is not installed
        """
        if not LITELLM_AVAILABLE:
            raise ImportError(
                "litellm is not installed. Install it with: pip install litellm"
            )

        super().__init__(model, temperature, max_tokens, **kwargs)
        self.api_key = api_key

        # Configure LiteLLM
        if api_key:
            litellm.api_key = api_key

        # Suppress verbose logging by default
        litellm.suppress_debug_info = True

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate a response using LiteLLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional LiteLLM parameters

        Returns:
            LLMResponse with generated content

        Raises:
            Exception: If generation fails
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        try:
            # Call LiteLLM's async completion
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
                **kwargs
            )

            # Extract content
            content = response.choices[0].message.content or ""

            # Extract usage information
            usage = {}
            if hasattr(response, "usage") and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                metadata={
                    "id": response.id,
                    "created": response.created,
                    "finish_reason": response.choices[0].finish_reason,
                }
            )

        except Exception as e:
            raise Exception(f"LiteLLM generation error: {str(e)}") from e

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        """Generate a streaming response using LiteLLM.

        Args:
            messages: List of message dicts
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional parameters

        Yields:
            Chunks of generated text
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
                stream=True,
                **kwargs
            )

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise Exception(f"LiteLLM streaming error: {str(e)}") from e

    @staticmethod
    def list_models() -> List[str]:
        """List all available models supported by LiteLLM.

        Returns:
            List of model identifiers
        """
        if not LITELLM_AVAILABLE:
            return []

        # Return a subset of popular models
        return [
            # OpenAI
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            # Anthropic
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            # Google
            "gemini-pro",
            "gemini-1.5-pro",
            # Azure
            "azure/gpt-4",
            "azure/gpt-35-turbo",
        ]
