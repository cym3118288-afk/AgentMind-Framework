"""Example: Multi - modal agent with audio processing.

This example demonstrates how to use AgentMind with audio capabilities
for speech - to - text, text - to - speech, and audio analysis.
"""

import asyncio
from pathlib import Path

from agentmind.multimodal import AudioProcessor, AudioFormat
from agentmind import Agent, AgentMind
from agentmind.llm import LiteLLMProvider


async def example_speech_to_text():
    """Convert speech to text."""
    print("=== Speech - to - Text Example ===\n")

    processor = AudioProcessor()

    audio_path = "path / to / audio.wav"
    if Path(audio_path).exists():
        # Transcribe audio
        text = processor.speech_to_text(audio_path, language="en - US")
        print(f"Transcription: {text}\n")
    else:
        print(f"Audio file not found: {audio_path}\n")


async def example_text_to_speech():
    """Convert text to speech."""
    print("=== Text - to - Speech Example ===\n")

    processor = AudioProcessor()

    text = "Hello! This is a test of the text - to - speech system."
    output_path = "output_speech.mp3"

    processor.text_to_speech(text, output_path, language="en")
    print(f"Generated speech saved to: {output_path}\n")


async def example_audio_transcription_agent():
    """Agent that transcribes and analyzes audio."""
    print("=== Audio Transcription Agent Example ===\n")

    # Initialize components
    audio_processor = AudioProcessor()
    llm = LiteLLMProvider(model="gpt - 4")
    mind = AgentMind(llm_provider=llm)

    # Create transcription agent
    transcriber = Agent(
        name="Transcriber",
        role="transcription",
        system_prompt="You analyze transcribed audio and provide insights.",
    )
    mind.add_agent(transcriber)

    audio_path = "path / to / meeting_recording.wav"
    if Path(audio_path).exists():
        # Transcribe audio
        transcription = audio_processor.speech_to_text(audio_path)
        print(f"Transcription:\n{transcription}\n")

        # Analyze with agent
        result = await mind.collaborate(
            f"Analyze this meeting transcription and provide key points:\n\n{transcription}",
            max_rounds=1,
        )
        print(f"Analysis:\n{result.final_output}\n")
    else:
        print(f"Audio file not found: {audio_path}\n")


async def example_audio_format_conversion():
    """Convert audio between formats."""
    print("=== Audio Format Conversion Example ===\n")

    processor = AudioProcessor()

    input_path = "path / to / audio.wav"
    output_path = "output_audio.mp3"

    if Path(input_path).exists():
        processor.convert_format(input_path, output_path, AudioFormat.MP3)
        print(f"Converted {input_path} to {output_path}\n")
    else:
        print(f"Audio file not found: {input_path}\n")


async def example_audio_info():
    """Get audio file information."""
    print("=== Audio Info Example ===\n")

    processor = AudioProcessor()

    audio_path = "path / to / audio.wav"
    if Path(audio_path).exists():
        info = processor.get_audio_info(audio_path)
        print("Audio information:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        print()
    else:
        print(f"Audio file not found: {audio_path}\n")


async def example_voice_assistant():
    """Create a voice - enabled assistant."""
    print("=== Voice Assistant Example ===\n")

    audio_processor = AudioProcessor()
    llm = LiteLLMProvider(model="gpt - 4")
    mind = AgentMind(llm_provider=llm)

    assistant = Agent(
        name="VoiceAssistant",
        role="assistant",
        system_prompt="You are a helpful voice assistant. Provide concise, clear responses.",
    )
    mind.add_agent(assistant)

    # Simulate voice interaction
    print("Voice Assistant: Ready to help!")
    print("(In a real scenario, this would record from microphone)\n")

    # Example: Process pre - recorded question
    question_audio = "path / to / question.wav"
    if Path(question_audio).exists():
        # Transcribe question
        question = audio_processor.speech_to_text(question_audio)
        print(f"User (transcribed): {question}")

        # Get response
        result = await mind.collaborate(question, max_rounds=1)
        response_text = result.final_output
        print(f"Assistant: {response_text}")

        # Convert response to speech
        response_audio = "response.mp3"
        audio_processor.text_to_speech(response_text, response_audio)
        print(f"Response audio saved to: {response_audio}\n")
    else:
        print(f"Question audio not found: {question_audio}\n")


async def example_multi_language_transcription():
    """Transcribe audio in multiple languages."""
    print("=== Multi - Language Transcription Example ===\n")

    processor = AudioProcessor()

    languages = {
        "english.wav": "en - US",
        "spanish.wav": "es - ES",
        "chinese.wav": "zh - CN",
    }

    for audio_file, language in languages.items():
        audio_path = f"path / to/{audio_file}"
        if Path(audio_path).exists():
            text = processor.speech_to_text(audio_path, language=language)
            print(f"{language}: {text}")
        else:
            print(f"Audio file not found: {audio_path}")
    print()


async def example_meeting_summarizer():
    """Transcribe and summarize a meeting recording."""
    print("=== Meeting Summarizer Example ===\n")

    audio_processor = AudioProcessor()
    llm = LiteLLMProvider(model="gpt - 4")
    mind = AgentMind(llm_provider=llm)

    # Create specialized agents
    transcriber = Agent(
        name="Transcriber",
        role="transcription",
        system_prompt="You format and clean up transcriptions.",
    )

    summarizer = Agent(
        name="Summarizer",
        role="summarization",
        system_prompt="You create concise meeting summaries with action items.",
    )

    mind.add_agent(transcriber)
    mind.add_agent(summarizer)

    meeting_audio = "path / to / meeting.wav"
    if Path(meeting_audio).exists():
        # Transcribe
        raw_transcription = audio_processor.speech_to_text(meeting_audio)

        # Process with agents
        result = await mind.collaborate(
            "Clean up and summarize this meeting transcription, "
            f"including key points and action items:\n\n{raw_transcription}",
            max_rounds=2,
        )

        print(f"Meeting Summary:\n{result.final_output}\n")
    else:
        print(f"Meeting audio not found: {meeting_audio}\n")


async def main():
    """Run all examples."""
    print("Audio Processing Examples\n")
    print("=" * 50 + "\n")

    print("Note: Update audio file paths and ensure required packages are installed.\n")
    print("Required packages: SpeechRecognition, pydub, gTTS\n")

    # Run examples that don't require audio files
    await example_text_to_speech()

    # Uncomment to run examples with audio files
    # await example_speech_to_text()
    # await example_audio_transcription_agent()
    # await example_audio_format_conversion()
    # await example_audio_info()
    # await example_voice_assistant()
    # await example_multi_language_transcription()
    # await example_meeting_summarizer()


if __name__ == "__main__":
    asyncio.run(main())
