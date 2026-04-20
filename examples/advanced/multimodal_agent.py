"""
Advanced Example: Multi - Modal Agent

This example demonstrates an agent that processes multiple modalities:
- Text understanding and generation
- Image analysis and description
- Audio processing and transcription
- Video analysis
- Document parsing
- Cross - modal reasoning

Estimated time: 30 minutes
Difficulty: Advanced
"""

import asyncio
from typing import Dict, List, Any, Optional
from enum import Enum
from agentmind import Agent, Message
from agentmind.llm import OllamaProvider


class ModalityType(str, Enum):
    """Types of modalities"""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"


class MultiModalContent:
    """Container for multi - modal content"""

    def __init__(
        self, modality: ModalityType, content: Any, metadata: Optional[Dict[str, Any]] = None
    ):
        self.modality = modality
        self.content = content
        self.metadata = metadata or {}

    def __repr__(self):
        return f"MultiModalContent(modality={self.modality}, metadata={self.metadata})"


class ImageProcessor:
    """Processes image content"""

    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze image and extract information"""
        # In production, use actual image processing libraries
        # like PIL, OpenCV, or vision models
        return {
            "type": "image",
            "path": image_path,
            "description": f"Image analysis of {image_path}",
            "objects_detected": ["person", "laptop", "desk"],
            "scene": "office workspace",
            "colors": ["blue", "white", "gray"],
            "text_detected": "Welcome to AgentMind",
        }

    async def generate_caption(self, image_path: str) -> str:
        """Generate natural language caption for image"""
        analysis = await self.analyze_image(image_path)
        return f"An {analysis['scene']} containing {', '.join(analysis['objects_detected'])}"


class AudioProcessor:
    """Processes audio content"""

    async def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio to text"""
        # In production, use speech recognition like Whisper
        return {
            "type": "audio",
            "path": audio_path,
            "transcript": "This is a sample audio transcription.",
            "language": "en",
            "duration": 30.5,
            "speaker_count": 1,
            "confidence": 0.95,
        }

    async def analyze_audio(self, audio_path: str) -> Dict[str, Any]:
        """Analyze audio characteristics"""
        return {
            "sentiment": "neutral",
            "emotion": "calm",
            "speech_rate": "normal",
            "background_noise": "low",
        }


class VideoProcessor:
    """Processes video content"""

    async def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """Analyze video content"""
        # In production, use video processing libraries
        return {
            "type": "video",
            "path": video_path,
            "duration": 120.0,
            "fps": 30,
            "resolution": "1920x1080",
            "scenes": [
                {"timestamp": 0, "description": "Introduction scene"},
                {"timestamp": 30, "description": "Main content"},
                {"timestamp": 90, "description": "Conclusion"},
            ],
            "audio_track": True,
            "subtitles": True,
        }

    async def extract_keyframes(self, video_path: str) -> List[str]:
        """Extract key frames from video"""
        return [
            f"{video_path}_frame_001.jpg",
            f"{video_path}_frame_030.jpg",
            f"{video_path}_frame_090.jpg",
        ]


class DocumentProcessor:
    """Processes document content"""

    async def parse_document(self, doc_path: str) -> Dict[str, Any]:
        """Parse document and extract structure"""
        # In production, use document parsing libraries
        return {
            "type": "document",
            "path": doc_path,
            "format": "pd",
            "pages": 10,
            "title": "AgentMind Documentation",
            "sections": [
                {"title": "Introduction", "page": 1},
                {"title": "Architecture", "page": 3},
                {"title": "Examples", "page": 7},
            ],
            "images": 5,
            "tables": 3,
        }

    async def extract_text(self, doc_path: str) -> str:
        """Extract text from document"""
        return f"Extracted text content from {doc_path}"


class MultiModalAgent(Agent):
    """Agent with multi - modal processing capabilities"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_processor = ImageProcessor()
        self.audio_processor = AudioProcessor()
        self.video_processor = VideoProcessor()
        self.document_processor = DocumentProcessor()
        self.processed_modalities: List[MultiModalContent] = []

    async def process_image(self, image_path: str) -> Dict[str, Any]:
        """Process image input"""
        analysis = await self.image_processor.analyze_image(image_path)
        caption = await self.image_processor.generate_caption(image_path)

        content = MultiModalContent(
            modality=ModalityType.IMAGE, content=analysis, metadata={"caption": caption}
        )
        self.processed_modalities.append(content)

        return {"modality": "image", "analysis": analysis, "caption": caption}

    async def process_audio(self, audio_path: str) -> Dict[str, Any]:
        """Process audio input"""
        transcription = await self.audio_processor.transcribe_audio(audio_path)
        analysis = await self.audio_processor.analyze_audio(audio_path)

        content = MultiModalContent(
            modality=ModalityType.AUDIO, content=transcription, metadata={"analysis": analysis}
        )
        self.processed_modalities.append(content)

        return {"modality": "audio", "transcription": transcription, "analysis": analysis}

    async def process_video(self, video_path: str) -> Dict[str, Any]:
        """Process video input"""
        analysis = await self.video_processor.analyze_video(video_path)
        keyframes = await self.video_processor.extract_keyframes(video_path)

        content = MultiModalContent(
            modality=ModalityType.VIDEO, content=analysis, metadata={"keyframes": keyframes}
        )
        self.processed_modalities.append(content)

        return {"modality": "video", "analysis": analysis, "keyframes": keyframes}

    async def process_document(self, doc_path: str) -> Dict[str, Any]:
        """Process document input"""
        structure = await self.document_processor.parse_document(doc_path)
        text = await self.document_processor.extract_text(doc_path)

        content = MultiModalContent(
            modality=ModalityType.DOCUMENT, content=structure, metadata={"text": text}
        )
        self.processed_modalities.append(content)

        return {"modality": "document", "structure": structure, "text": text}

    async def cross_modal_reasoning(self, query: str) -> str:
        """Perform reasoning across multiple modalities"""
        # Gather information from all processed modalities
        context = []

        for content in self.processed_modalities:
            if content.modality == ModalityType.IMAGE:
                context.append(f"Image: {content.metadata.get('caption')}")
            elif content.modality == ModalityType.AUDIO:
                transcript = content.content.get("transcript")
                context.append(f"Audio: {transcript}")
            elif content.modality == ModalityType.VIDEO:
                scenes = content.content.get("scenes", [])
                context.append(f"Video: {len(scenes)} scenes")
            elif content.modality == ModalityType.DOCUMENT:
                title = content.content.get("title")
                context.append(f"Document: {title}")

        # Create enhanced query with multi - modal context
        enhanced_query = f"{query}\n\nContext from multiple sources:\n" + "\n".join(context)

        # Process with LLM
        message = Message(content=enhanced_query, sender="system", role="user")
        response = await self.process_message(message)

        return response.content

    def get_modality_summary(self) -> Dict[str, Any]:
        """Get summary of processed modalities"""
        summary = {"total_processed": len(self.processed_modalities), "by_type": {}}

        for modality_type in ModalityType:
            count = sum(1 for c in self.processed_modalities if c.modality == modality_type)
            if count > 0:
                summary["by_type"][modality_type.value] = count

        return summary


async def example_1_image_processing():
    """Example 1: Image processing"""
    print("\n=== Example 1: Image Processing ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = MultiModalAgent(name="vision_agent", role="analyst", llm_provider=llm)

    # Process image
    result = await agent.process_image("workspace.jpg")
    print("Image Analysis:")
    print(f"  Objects: {result['analysis']['objects_detected']}")
    print(f"  Scene: {result['analysis']['scene']}")
    print(f"  Caption: {result['caption']}\n")


async def example_2_audio_processing():
    """Example 2: Audio processing"""
    print("\n=== Example 2: Audio Processing ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = MultiModalAgent(name="audio_agent", role="analyst", llm_provider=llm)

    # Process audio
    result = await agent.process_audio("meeting.mp3")
    print("Audio Analysis:")
    print(f"  Transcript: {result['transcription']['transcript']}")
    print(f"  Duration: {result['transcription']['duration']}s")
    print(f"  Sentiment: {result['analysis']['sentiment']}\n")


async def example_3_video_processing():
    """Example 3: Video processing"""
    print("\n=== Example 3: Video Processing ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = MultiModalAgent(name="video_agent", role="analyst", llm_provider=llm)

    # Process video
    result = await agent.process_video("presentation.mp4")
    print("Video Analysis:")
    print(f"  Duration: {result['analysis']['duration']}s")
    print(f"  Scenes: {len(result['analysis']['scenes'])}")
    print(f"  Keyframes: {len(result['keyframes'])}\n")


async def example_4_document_processing():
    """Example 4: Document processing"""
    print("\n=== Example 4: Document Processing ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = MultiModalAgent(name="doc_agent", role="analyst", llm_provider=llm)

    # Process document
    result = await agent.process_document("report.pd")
    print("Document Analysis:")
    print(f"  Title: {result['structure']['title']}")
    print(f"  Pages: {result['structure']['pages']}")
    print(f"  Sections: {len(result['structure']['sections'])}\n")


async def example_5_cross_modal_reasoning():
    """Example 5: Cross - modal reasoning"""
    print("\n=== Example 5: Cross - Modal Reasoning ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = MultiModalAgent(name="multimodal_agent", role="analyst", llm_provider=llm)

    # Process multiple modalities
    await agent.process_image("product.jpg")
    await agent.process_audio("review.mp3")
    await agent.process_document("specs.pd")

    # Perform cross - modal reasoning
    response = await agent.cross_modal_reasoning(
        "Provide a comprehensive analysis of this product based on all available information."
    )

    print("Cross - Modal Analysis:")
    print(f"{response[:300]}...\n")

    # Show modality summary
    summary = agent.get_modality_summary()
    print(f"Processed Modalities: {summary['total_processed']}")
    print(f"By Type: {summary['by_type']}\n")


async def example_6_multimodal_workflow():
    """Example 6: Complete multi - modal workflow"""
    print("\n=== Example 6: Multi - Modal Workflow ===\n")

    llm = OllamaProvider(model="llama3.2:3b")
    agent = MultiModalAgent(name="workflow_agent", role="analyst", llm_provider=llm)

    print("Processing multi - modal content pipeline:\n")

    # Step 1: Process video
    print("1. Processing video presentation...")
    await agent.process_video("training.mp4")

    # Step 2: Process slides
    print("2. Processing presentation slides...")
    await agent.process_document("slides.pd")

    # Step 3: Process audio feedback
    print("3. Processing audio feedback...")
    await agent.process_audio("feedback.mp3")

    # Step 4: Generate comprehensive report
    print("4. Generating comprehensive report...\n")
    report = await agent.cross_modal_reasoning(
        "Create a summary report of the training session including key points, "
        "visual content, and participant feedback."
    )

    print("Report Generated:")
    print(f"{report[:200]}...\n")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("Advanced Example: Multi - Modal Agent")
    print("=" * 60)

    await example_1_image_processing()
    await example_2_audio_processing()
    await example_3_video_processing()
    await example_4_document_processing()
    await example_5_cross_modal_reasoning()
    await example_6_multimodal_workflow()

    print("\n" + "=" * 60)
    print("Example Complete!")
    print("=" * 60)
    print("\nKey Concepts:")
    print("1. Multi - modal agents process diverse input types")
    print("2. Each modality requires specialized processing")
    print("3. Cross - modal reasoning combines insights")
    print("4. Multi - modal workflows enable rich applications")
    print("5. Context from multiple sources improves understanding")


if __name__ == "__main__":
    asyncio.run(main())
