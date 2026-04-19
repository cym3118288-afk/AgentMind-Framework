"""Example: Multi-modal agent with image processing.

This example demonstrates how to use AgentMind with vision capabilities
to analyze images, extract text, and answer questions about visual content.
"""

import asyncio
from pathlib import Path

from agentmind.multimodal import ImageProcessor, VisionLLMProvider, VisionAgent
from agentmind.llm import LiteLLMProvider


async def example_image_analysis():
    """Analyze an image with a vision-capable agent."""
    print("=== Image Analysis Example ===\n")

    # Initialize image processor
    image_processor = ImageProcessor(max_size=(1024, 1024))

    # Initialize vision LLM (using GPT-4V or Claude 3)
    base_llm = LiteLLMProvider(model="gpt-4-vision-preview")
    vision_llm = VisionLLMProvider(base_llm, image_processor)

    # Create vision agent
    agent = VisionAgent(
        vision_provider=vision_llm,
        name="ImageAnalyzer",
        system_prompt="You are an expert at analyzing images and providing detailed descriptions.",
    )

    # Analyze an image
    image_path = "path/to/your/image.jpg"
    if Path(image_path).exists():
        response = await agent.process_with_image(
            "What do you see in this image? Provide a detailed description.", images=[image_path]
        )
        print(f"Analysis: {response}\n")
    else:
        print(f"Image not found: {image_path}\n")


async def example_ocr():
    """Extract text from an image using OCR."""
    print("=== OCR Example ===\n")

    image_processor = ImageProcessor()
    base_llm = LiteLLMProvider(model="gpt-4-vision-preview")
    vision_llm = VisionLLMProvider(base_llm, image_processor)

    image_path = "path/to/document.jpg"
    if Path(image_path).exists():
        text = await vision_llm.extract_text_from_image(image_path)
        print(f"Extracted text:\n{text}\n")
    else:
        print(f"Image not found: {image_path}\n")


async def example_image_comparison():
    """Compare multiple images."""
    print("=== Image Comparison Example ===\n")

    image_processor = ImageProcessor()
    base_llm = LiteLLMProvider(model="gpt-4-vision-preview")
    vision_llm = VisionLLMProvider(base_llm, image_processor)

    images = ["path/to/image1.jpg", "path/to/image2.jpg"]
    if all(Path(img).exists() for img in images):
        comparison = await vision_llm.compare_images(
            images, prompt="Compare these two images. What are the main differences?"
        )
        print(f"Comparison:\n{comparison}\n")
    else:
        print("One or more images not found\n")


async def example_image_qa():
    """Answer questions about an image."""
    print("=== Image Q&A Example ===\n")

    image_processor = ImageProcessor()
    base_llm = LiteLLMProvider(model="gpt-4-vision-preview")
    vision_llm = VisionLLMProvider(base_llm, image_processor)

    agent = VisionAgent(vision_provider=vision_llm, name="ImageQA")

    image_path = "path/to/chart.jpg"
    if Path(image_path).exists():
        # Ask multiple questions about the same image
        questions = [
            "What type of chart is this?",
            "What are the main trends shown?",
            "What is the highest value in the chart?",
        ]

        for question in questions:
            answer = await agent.process_with_image(question, images=[image_path])
            print(f"Q: {question}")
            print(f"A: {answer}\n")
    else:
        print(f"Image not found: {image_path}\n")


async def example_image_processing():
    """Demonstrate image processing utilities."""
    print("=== Image Processing Example ===\n")

    processor = ImageProcessor()

    image_path = "path/to/image.jpg"
    if Path(image_path).exists():
        # Load and get info
        image = processor.load_image(image_path)
        info = processor.get_image_info(image)
        print(f"Image info: {info}")

        # Resize
        resized = processor.resize_image(image, max_size=(512, 512))
        print(f"Resized to: {resized.size}")

        # Create thumbnail
        thumb = processor.create_thumbnail(image, size=(128, 128))
        print(f"Thumbnail size: {thumb.size}")

        # Convert to base64
        base64_str = processor.image_to_base64(image)
        print(f"Base64 length: {len(base64_str)} characters")

        # Save processed image
        processor.save_image(resized, "output_resized.jpg")
        print("Saved resized image to output_resized.jpg\n")
    else:
        print(f"Image not found: {image_path}\n")


async def example_multi_agent_vision():
    """Multiple agents collaborating with vision capabilities."""
    print("=== Multi-Agent Vision Example ===\n")

    image_processor = ImageProcessor()
    base_llm = LiteLLMProvider(model="gpt-4-vision-preview")
    vision_llm = VisionLLMProvider(base_llm, image_processor)

    # Create specialized vision agents
    describer = VisionAgent(
        vision_provider=vision_llm,
        name="Describer",
        system_prompt="You describe images in detail, focusing on visual elements.",
    )

    analyzer = VisionAgent(
        vision_provider=vision_llm,
        name="Analyzer",
        system_prompt="You analyze images for patterns, trends, and insights.",
    )

    image_path = "path/to/data_visualization.jpg"
    if Path(image_path).exists():
        # First agent describes
        description = await describer.process_with_image(
            "Describe what you see in this image.", images=[image_path]
        )
        print(f"Describer: {description}\n")

        # Second agent analyzes based on description
        analysis = await analyzer.process_text(
            f"Based on this description: '{description}', " "what insights can you provide?"
        )
        print(f"Analyzer: {analysis}\n")
    else:
        print(f"Image not found: {image_path}\n")


async def main():
    """Run all examples."""
    print("Multi-Modal Agent Examples\n")
    print("=" * 50 + "\n")

    # Note: These examples require actual image files and API keys
    print("Note: Update image paths and ensure you have API keys configured.\n")

    await example_image_processing()
    # Uncomment to run vision examples (requires API keys)
    # await example_image_analysis()
    # await example_ocr()
    # await example_image_comparison()
    # await example_image_qa()
    # await example_multi_agent_vision()


if __name__ == "__main__":
    asyncio.run(main())
