# Multi-Modal Support

AgentMind provides comprehensive multi-modal capabilities, allowing agents to process and generate various types of media including images, audio, and documents.

## Overview

The multi-modal module (`agentmind.multimodal`) includes:

- **Image Processing**: Load, resize, convert, and analyze images
- **Audio Processing**: Speech-to-text, text-to-speech, audio format conversion
- **Document Processing**: Extract text from PDF, DOCX, and other formats
- **Vision-Language Models**: Integration with GPT-4V, Claude 3, and other vision-capable LLMs

## Installation

Install the required dependencies for multi-modal support:

```bash
# Image processing
pip install Pillow

# Audio processing
pip install SpeechRecognition pydub gTTS

# Document processing
pip install PyPDF2 python-docx

# All multi-modal features
pip install Pillow SpeechRecognition pydub gTTS PyPDF2 python-docx
```

## Image Processing

### Basic Usage

```python
from agentmind.multimodal import ImageProcessor

processor = ImageProcessor(max_size=(1024, 1024))

# Load and process image
image = processor.load_image("photo.jpg")
resized = processor.resize_image(image, max_size=(512, 512))

# Convert to base64 for LLM
base64_str = processor.image_to_base64(image)

# Create thumbnail
thumb = processor.create_thumbnail(image, size=(128, 128))

# Save processed image
processor.save_image(resized, "output.jpg")
```

### Vision-Language Models

```python
from agentmind.multimodal import VisionLLMProvider, VisionAgent
from agentmind.llm import LiteLLMProvider

# Initialize vision provider
base_llm = LiteLLMProvider(model="gpt-4-vision-preview")
vision_llm = VisionLLMProvider(base_llm)

# Create vision agent
agent = VisionAgent(
    vision_provider=vision_llm,
    name="ImageAnalyzer",
    system_prompt="You are an expert at analyzing images."
)

# Analyze image
response = await agent.process_with_image(
    "What do you see in this image?",
    images=["photo.jpg"]
)
```

### Image Analysis Tasks

```python
# Extract text from image (OCR)
text = await vision_llm.extract_text_from_image("document.jpg")

# Compare images
comparison = await vision_llm.compare_images(
    ["image1.jpg", "image2.jpg"],
    prompt="What are the differences?"
)

# Answer questions about image
answer = await vision_llm.answer_about_image(
    "chart.jpg",
    "What is the trend shown in this chart?"
)
```

## Audio Processing

### Speech-to-Text

```python
from agentmind.multimodal import AudioProcessor

processor = AudioProcessor()

# Transcribe audio file
text = processor.speech_to_text("recording.wav", language="en-US")

# Record from microphone
audio = processor.record_audio(duration=5)
text = processor.speech_to_text(audio)

# Use different engines
text = processor.speech_to_text("audio.wav", engine="google")
text = processor.speech_to_text("audio.wav", engine="whisper")
```

### Text-to-Speech

```python
# Convert text to speech
processor.text_to_speech(
    "Hello, this is a test.",
    output_path="output.mp3",
    language="en"
)
```

### Audio Format Conversion

```python
from agentmind.multimodal import AudioFormat

# Convert audio format
processor.convert_format(
    "input.wav",
    "output.mp3",
    AudioFormat.MP3
)

# Get audio information
info = processor.get_audio_info("audio.wav")
print(f"Duration: {info['duration_seconds']} seconds")
```

### Voice-Enabled Agents

```python
from agentmind import Agent, AgentMind
from agentmind.llm import LiteLLMProvider

audio_processor = AudioProcessor()
llm = LiteLLMProvider(model="gpt-4")
mind = AgentMind(llm_provider=llm)

assistant = Agent(
    name="VoiceAssistant",
    role="assistant",
    system_prompt="You are a helpful voice assistant."
)
mind.add_agent(assistant)

# Process voice input
question = audio_processor.speech_to_text("question.wav")
result = await mind.collaborate(question, max_rounds=1)

# Generate voice response
audio_processor.text_to_speech(result.final_output, "response.mp3")
```

## Document Processing

### Extract Text from Documents

```python
from agentmind.multimodal import DocumentProcessor

processor = DocumentProcessor()

# Extract from PDF
text = processor.extract_text_from_pdf("document.pdf")

# Extract specific pages
text = processor.extract_text_from_pdf("document.pdf", pages=[0, 1, 2])

# Extract from DOCX
text = processor.extract_text_from_docx("document.docx")

# Auto-detect format
text = processor.extract_text("document.pdf")
```

### Document Metadata

```python
# Get PDF metadata
metadata = processor.get_pdf_metadata("document.pdf")
print(f"Title: {metadata['title']}")
print(f"Author: {metadata['author']}")
print(f"Pages: {metadata['num_pages']}")

# Get DOCX metadata
metadata = processor.get_docx_metadata("document.docx")
print(f"Created: {metadata['created']}")
print(f"Modified: {metadata['modified']}")
```

### Document Chunking

```python
# Split long documents into chunks
text = processor.extract_text("long_document.pdf")
chunks = processor.chunk_text(text, chunk_size=1000, overlap=100)

# Process each chunk
for i, chunk in enumerate(chunks):
    print(f"Processing chunk {i+1}/{len(chunks)}")
    # Process with LLM
```

### Document Analysis Agents

```python
from agentmind import Agent, AgentMind
from agentmind.llm import LiteLLMProvider

doc_processor = DocumentProcessor()
llm = LiteLLMProvider(model="gpt-4")
mind = AgentMind(llm_provider=llm)

analyzer = Agent(
    name="DocumentAnalyzer",
    role="analysis",
    system_prompt="You analyze documents and extract key information."
)
mind.add_agent(analyzer)

# Analyze document
text = doc_processor.extract_text("report.pdf")
result = await mind.collaborate(
    f"Analyze this document:\n\n{text}",
    max_rounds=1
)
```

## Advanced Use Cases

### Multi-Modal Research Assistant

```python
from agentmind.multimodal import (
    ImageProcessor, AudioProcessor, DocumentProcessor,
    VisionLLMProvider
)

# Initialize processors
image_proc = ImageProcessor()
audio_proc = AudioProcessor()
doc_proc = DocumentProcessor()

# Create multi-modal agent
base_llm = LiteLLMProvider(model="gpt-4-vision-preview")
vision_llm = VisionLLMProvider(base_llm, image_proc)

agent = VisionAgent(vision_provider=vision_llm, name="ResearchAssistant")

# Process research paper with figures
paper_text = doc_proc.extract_text("paper.pdf")
figure_analysis = await agent.process_with_image(
    "Analyze this figure from the paper",
    images=["figure1.png"]
)

# Transcribe presentation
presentation_text = audio_proc.speech_to_text("presentation.wav")

# Combine all information
combined_analysis = await agent.process_text(
    f"Synthesize insights from:\n"
    f"Paper: {paper_text[:1000]}\n"
    f"Figure: {figure_analysis}\n"
    f"Presentation: {presentation_text}"
)
```

### Meeting Transcription and Analysis

```python
# Transcribe meeting
audio_proc = AudioProcessor()
transcription = audio_proc.speech_to_text("meeting.wav")

# Extract slides
doc_proc = DocumentProcessor()
slides_text = doc_proc.extract_text("slides.pdf")

# Analyze with agents
llm = LiteLLMProvider(model="gpt-4")
mind = AgentMind(llm_provider=llm)

summarizer = Agent(name="Summarizer", role="summarization")
action_tracker = Agent(name="ActionTracker", role="action_items")

mind.add_agent(summarizer)
mind.add_agent(action_tracker)

result = await mind.collaborate(
    f"Meeting transcript:\n{transcription}\n\n"
    f"Slides:\n{slides_text}\n\n"
    f"Provide summary and action items.",
    max_rounds=2
)
```

### Document Comparison and Analysis

```python
# Compare multiple documents
doc_proc = DocumentProcessor()
docs = ["contract_v1.pdf", "contract_v2.pdf"]
texts = [doc_proc.extract_text(doc) for doc in docs]

llm = LiteLLMProvider(model="gpt-4")
mind = AgentMind(llm_provider=llm)

comparer = Agent(
    name="DocumentComparer",
    role="comparison",
    system_prompt="You identify differences between document versions."
)
mind.add_agent(comparer)

result = await mind.collaborate(
    f"Compare these documents:\n\n"
    f"Version 1:\n{texts[0]}\n\n"
    f"Version 2:\n{texts[1]}",
    max_rounds=1
)
```

## Supported Formats

### Images
- PNG
- JPEG/JPG
- WEBP
- GIF

### Audio
- WAV
- MP3
- OGG
- FLAC
- M4A

### Documents
- PDF
- DOCX
- TXT
- MD (Markdown)

## Vision-Capable Models

AgentMind supports various vision-language models:

- **GPT-4 Vision** (`gpt-4-vision-preview`)
- **Claude 3 Opus** (`claude-3-opus-20240229`)
- **Claude 3 Sonnet** (`claude-3-sonnet-20240229`)
- **Gemini Pro Vision** (`gemini-pro-vision`)

## Best Practices

### Image Processing
- Resize large images before sending to LLMs to reduce costs
- Use appropriate image formats (PNG for quality, JPEG for size)
- Create thumbnails for preview purposes

### Audio Processing
- Use WAV format for best transcription quality
- Adjust for ambient noise when recording from microphone
- Consider using Whisper for better accuracy with multiple languages

### Document Processing
- Chunk long documents to fit within LLM context limits
- Extract metadata for better document organization
- Use specific page extraction for large PDFs to reduce processing time

### Performance
- Process media files asynchronously for better performance
- Cache processed results to avoid redundant operations
- Use batch processing for multiple files

## Error Handling

```python
from agentmind.multimodal import ImageProcessor

processor = ImageProcessor()

try:
    image = processor.load_image("photo.jpg")
except FileNotFoundError:
    print("Image file not found")
except Exception as e:
    print(f"Error processing image: {e}")
```

## Examples

See the `examples/` directory for complete examples:

- `multimodal_image_example.py` - Image processing and vision agents
- `multimodal_audio_example.py` - Audio transcription and voice assistants
- `multimodal_document_example.py` - Document analysis and Q&A

## API Reference

### ImageProcessor

- `load_image(path)` - Load image from file
- `resize_image(image, max_size)` - Resize image
- `image_to_base64(image, format)` - Convert to base64
- `prepare_for_llm(image, format)` - Prepare for LLM input
- `save_image(image, path, format)` - Save image
- `create_thumbnail(image, size)` - Create thumbnail
- `get_image_info(image)` - Get image metadata

### AudioProcessor

- `speech_to_text(audio, language, engine)` - Transcribe audio
- `text_to_speech(text, output_path, language)` - Generate speech
- `record_audio(duration, timeout)` - Record from microphone
- `convert_format(input_path, output_path, format)` - Convert format
- `get_audio_info(path)` - Get audio metadata

### DocumentProcessor

- `extract_text(path, format)` - Extract text from document
- `extract_text_from_pdf(path, pages)` - Extract from PDF
- `extract_text_from_docx(path)` - Extract from DOCX
- `get_pdf_metadata(path)` - Get PDF metadata
- `get_docx_metadata(path)` - Get DOCX metadata
- `chunk_text(text, chunk_size, overlap)` - Split text into chunks

### VisionLLMProvider

- `analyze_image(image, prompt)` - Analyze single image
- `compare_images(images, prompt)` - Compare multiple images
- `extract_text_from_image(image)` - OCR
- `answer_about_image(image, question)` - Image Q&A
- `create_vision_message(text, images)` - Create multi-modal message

## Troubleshooting

### Import Errors

If you get import errors, ensure all dependencies are installed:

```bash
pip install Pillow SpeechRecognition pydub gTTS PyPDF2 python-docx
```

### Audio Issues

For audio processing on Linux, you may need additional system packages:

```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

### PDF Extraction Issues

If PDF text extraction fails, try alternative libraries:

```bash
pip install pdfplumber  # Alternative to PyPDF2
```

## Future Enhancements

Planned features for multi-modal support:

- Video processing (frame extraction, analysis)
- Real-time streaming for audio/video
- Advanced OCR with layout preservation
- Multi-modal embeddings for semantic search
- Support for more document formats (Excel, PowerPoint)
