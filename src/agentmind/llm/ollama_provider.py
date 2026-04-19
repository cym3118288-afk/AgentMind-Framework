"""Ollama provider for local LLM inference.

This module provides integration with Ollama for running local models
like llama3.2, mistral, etc.
"""

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from .provider import LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    """Ollama provider for local model inference.

    Connects to a local Ollama instance to run models like llama3.2, mistral, etc.

    Example:
        >>> provider = OllamaProvider(model="llama3.2")
        >>> messages = [{"role": "user", "content": "Hello!"}]
        >>> response = await provider.generate(messages)
        >>> print(response.content)
    """

    def __init__(
        self,
        model: str = "llama3.2",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
        **kwargs: Any
    ) -> None:
        """Initialize Ollama provider.

        Args:
            model: Ollama model name (e.g., "llama3.2", "mistral")
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            base_url: Ollama API base URL
            timeout: Request timeout in seconds (default: 120.0)
            **kwargs: Additional parameters
        """
        super().__init__(model, temperature, max_tokens, **kwargs)
        self.base_url = base_url.rstrip("/")

        # Optimized: Configure connection pooling for better performance
        # Try to enable HTTP/2 if available, fall back to HTTP/1.1
        try:
            import h2  # noqa
            http2_enabled = True
        except ImportError:
            http2_enabled = False

        self.client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            http2=http2_enabled
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate a response using Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional Ollama parameters

        Returns:
            LLMResponse with generated content

        Raises:
            httpx.HTTPError: If API request fails
        """
        # Optimized: Use ternary operator inline for better performance
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        # Optimized: Build payload more efficiently
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": max_tok,
                **kwargs  # Merge extra parameters directly
            }
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            # Extract content from Ollama response
            content = data.get("message", {}).get("content", "")

            # Optimized: Extract usage information more efficiently
            usage = {}
            prompt_tokens = data.get("prompt_eval_count")
            completion_tokens = data.get("eval_count")

            if prompt_tokens is not None:
                usage["prompt_tokens"] = prompt_tokens
            if completion_tokens is not None:
                usage["completion_tokens"] = completion_tokens
            if usage:
                usage["total_tokens"] = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)

            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                metadata={
                    "done": data.get("done", False),
                    "total_duration": data.get("total_duration"),
                    "load_duration": data.get("load_duration"),
                    "eval_duration": data.get("eval_duration"),
                }
            )

        except httpx.HTTPError as e:
            raise Exception(f"Ollama API error: {str(e)}") from e

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        """Generate a streaming response using Ollama.

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

        # Optimized: Build payload more efficiently
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temp,
                "num_predict": max_tok,
                **kwargs  # Merge extra parameters directly
            }
        }

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            # Optimized: Use get with default for safer access
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPError as e:
            raise Exception(f"Ollama streaming error: {str(e)}") from e

    async def check_model_available(self) -> bool:
        """Check if the specified model is available in Ollama.

        Returns:
            True if model is available, False otherwise
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            # Optimized: Use generator expression with any() for early exit
            models = data.get("models", [])
            return any(m.get("name") == self.model for m in models)
        except Exception:
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    def __del__(self) -> None:
        """Cleanup on deletion."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.client.aclose())
            else:
                loop.run_until_complete(self.client.aclose())
        except Exception:
            pass
