"""Vision-language model integration for AgentMind."""

from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import asyncio

from ..llm.provider import LLMProvider
from .image_processor import ImageProcessor


class VisionLLMProvider(LLMProvider):
    """LLM provider with vision capabilities (GPT-4V, Claude 3, etc.)."""

    def __init__(
        self,
        base_provider: LLMProvider,
        image_processor: Optional[ImageProcessor] = None
    ):
        """Initialize vision LLM provider.

        Args:
            base_provider: Underlying LLM provider (must support vision)
            image_processor: Image processor instance
        """
        self.base_provider = base_provider
        self.image_processor = image_processor or ImageProcessor()
        self.supports_vision = True

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """Generate response with vision support.

        Args:
            messages: List of messages (can include images)
            **kwargs: Additional generation parameters

        Returns:
            Generated text response
        """
        # Process messages to handle images
        processed_messages = []
        for msg in messages:
            if isinstance(msg.get("content"), list):
                # Multi-modal message
                processed_content = []
                for item in msg["content"]:
                    if item.get("type") == "image":
                        # Image is already processed
                        processed_content.append(item)
                    elif item.get("type") == "image_path":
                        # Process image from path
                        image_data = self.image_processor.prepare_for_llm(
                            item["path"]
                        )
                        processed_content.append(image_data)
                    else:
                        processed_content.append(item)
                processed_messages.append({
                    "role": msg["role"],
                    "content": processed_content
                })
            else:
                processed_messages.append(msg)

        return await self.base_provider.generate(processed_messages, **kwargs)

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ):
        """Generate streaming response with vision support.

        Args:
            messages: List of messages (can include images)
            **kwargs: Additional generation parameters

        Yields:
            Generated text chunks
        """
        # Process messages similar to generate()
        processed_messages = []
        for msg in messages:
            if isinstance(msg.get("content"), list):
                processed_content = []
                for item in msg["content"]:
                    if item.get("type") == "image":
                        processed_content.append(item)
                    elif item.get("type") == "image_path":
                        image_data = self.image_processor.prepare_for_llm(
                            item["path"]
                        )
                        processed_content.append(image_data)
                    else:
                        processed_content.append(item)
                processed_messages.append({
                    "role": msg["role"],
                    "content": processed_content
                })
            else:
                processed_messages.append(msg)

        async for chunk in self.base_provider.generate_stream(
            processed_messages, **kwargs
        ):
            yield chunk

    def create_vision_message(
        self,
        text: str,
        images: List[Union[str, Path]],
        role: str = "user"
    ) -> Dict[str, Any]:
        """Create a multi-modal message with text and images.

        Args:
            text: Text content
            images: List of image paths
            role: Message role

        Returns:
            Multi-modal message dictionary
        """
        content = [{"type": "text", "text": text}]

        for image_path in images:
            image_data = self.image_processor.prepare_for_llm(image_path)
            content.append(image_data)

        return {
            "role": role,
            "content": content
        }

    async def analyze_image(
        self,
        image: Union[str, Path],
        prompt: str = "Describe this image in detail.",
        **kwargs
    ) -> str:
        """Analyze an image with a prompt.

        Args:
            image: Path to image
            prompt: Analysis prompt
            **kwargs: Additional generation parameters

        Returns:
            Analysis result
        """
        message = self.create_vision_message(prompt, [image])
        return await self.generate([message], **kwargs)

    async def compare_images(
        self,
        images: List[Union[str, Path]],
        prompt: str = "Compare these images and describe the differences.",
        **kwargs
    ) -> str:
        """Compare multiple images.

        Args:
            images: List of image paths
            prompt: Comparison prompt
            **kwargs: Additional generation parameters

        Returns:
            Comparison result
        """
        message = self.create_vision_message(prompt, images)
        return await self.generate([message], **kwargs)

    async def extract_text_from_image(
        self,
        image: Union[str, Path],
        **kwargs
    ) -> str:
        """Extract text from an image (OCR).

        Args:
            image: Path to image
            **kwargs: Additional generation parameters

        Returns:
            Extracted text
        """
        prompt = "Extract all text from this image. Return only the text content."
        return await self.analyze_image(image, prompt, **kwargs)

    async def answer_about_image(
        self,
        image: Union[str, Path],
        question: str,
        **kwargs
    ) -> str:
        """Answer a question about an image.

        Args:
            image: Path to image
            question: Question to answer
            **kwargs: Additional generation parameters

        Returns:
            Answer
        """
        return await self.analyze_image(image, question, **kwargs)

    def get_model_name(self) -> str:
        """Get the model name."""
        return self.base_provider.get_model_name()

    def supports_streaming(self) -> bool:
        """Check if streaming is supported."""
        return self.base_provider.supports_streaming()

    def supports_function_calling(self) -> bool:
        """Check if function calling is supported."""
        return self.base_provider.supports_function_calling()


class VisionAgent:
    """Agent with vision capabilities."""

    def __init__(
        self,
        vision_provider: VisionLLMProvider,
        name: str = "VisionAgent",
        system_prompt: Optional[str] = None
    ):
        """Initialize vision agent.

        Args:
            vision_provider: Vision LLM provider
            name: Agent name
            system_prompt: System prompt
        """
        self.vision_provider = vision_provider
        self.name = name
        self.system_prompt = system_prompt or (
            "You are a helpful AI assistant with vision capabilities. "
            "You can analyze images, extract text, and answer questions about visual content."
        )
        self.conversation_history: List[Dict[str, Any]] = []

    async def process_with_image(
        self,
        text: str,
        images: List[Union[str, Path]],
        **kwargs
    ) -> str:
        """Process a request with images.

        Args:
            text: Text prompt
            images: List of image paths
            **kwargs: Additional generation parameters

        Returns:
            Response
        """
        # Add system prompt if first message
        if not self.conversation_history:
            self.conversation_history.append({
                "role": "system",
                "content": self.system_prompt
            })

        # Create and add user message
        user_message = self.vision_provider.create_vision_message(text, images)
        self.conversation_history.append(user_message)

        # Generate response
        response = await self.vision_provider.generate(
            self.conversation_history,
            **kwargs
        )

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        return response

    async def process_text(self, text: str, **kwargs) -> str:
        """Process a text-only request.

        Args:
            text: Text prompt
            **kwargs: Additional generation parameters

        Returns:
            Response
        """
        # Add system prompt if first message
        if not self.conversation_history:
            self.conversation_history.append({
                "role": "system",
                "content": self.system_prompt
            })

        # Add user message
        self.conversation_history.append({
            "role": "user",
            "content": text
        })

        # Generate response
        response = await self.vision_provider.generate(
            self.conversation_history,
            **kwargs
        )

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        return response

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
