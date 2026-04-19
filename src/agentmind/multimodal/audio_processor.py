"""Audio processing utilities for AgentMind."""

import base64
import io
from enum import Enum
from pathlib import Path
from typing import Optional, Union

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


class AudioFormat(str, Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"
    M4A = "m4a"


class AudioProcessor:
    """Process audio for multi-modal agent interactions."""

    def __init__(self):
        """Initialize audio processor."""
        if not SR_AVAILABLE:
            raise ImportError(
                "SpeechRecognition is required for audio processing. "
                "Install with: pip install SpeechRecognition"
            )
        self.recognizer = sr.Recognizer()

    def load_audio(self, path: Union[str, Path]) -> sr.AudioData:
        """Load audio from file.

        Args:
            path: Path to audio file

        Returns:
            AudioData object
        """
        with sr.AudioFile(str(path)) as source:
            audio = self.recognizer.record(source)
        return audio

    def speech_to_text(
        self,
        audio: Union[sr.AudioData, str, Path],
        language: str = "en-US",
        engine: str = "google"
    ) -> str:
        """Convert speech to text.

        Args:
            audio: AudioData object or path to audio file
            language: Language code (e.g., 'en-US', 'zh-CN')
            engine: Recognition engine ('google', 'sphinx', 'whisper')

        Returns:
            Transcribed text
        """
        if isinstance(audio, (str, Path)):
            audio = self.load_audio(audio)

        try:
            if engine == "google":
                text = self.recognizer.recognize_google(audio, language=language)
            elif engine == "sphinx":
                text = self.recognizer.recognize_sphinx(audio, language=language)
            elif engine == "whisper":
                text = self.recognizer.recognize_whisper(audio, language=language)
            else:
                raise ValueError(f"Unsupported engine: {engine}")
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            raise RuntimeError(f"Speech recognition error: {e}")

    def record_audio(
        self,
        duration: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> sr.AudioData:
        """Record audio from microphone.

        Args:
            duration: Recording duration in seconds (None for continuous)
            timeout: Timeout for waiting for speech in seconds

        Returns:
            AudioData object
        """
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            if duration:
                audio = self.recognizer.record(source, duration=duration)
            else:
                audio = self.recognizer.listen(source, timeout=timeout)
        return audio

    def audio_to_base64(self, audio: Union[sr.AudioData, str, Path]) -> str:
        """Convert audio to base64 string.

        Args:
            audio: AudioData object or path to audio file

        Returns:
            Base64 encoded string
        """
        if isinstance(audio, (str, Path)):
            with open(audio, "rb") as f:
                audio_bytes = f.read()
        else:
            audio_bytes = audio.get_wav_data()

        return base64.b64encode(audio_bytes).decode()

    def base64_to_audio(self, base64_str: str) -> sr.AudioData:
        """Convert base64 string to AudioData.

        Args:
            base64_str: Base64 encoded audio string

        Returns:
            AudioData object
        """
        audio_bytes = base64.b64decode(base64_str)
        audio_io = io.BytesIO(audio_bytes)

        with sr.AudioFile(audio_io) as source:
            audio = self.recognizer.record(source)
        return audio

    def convert_format(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        output_format: AudioFormat
    ) -> None:
        """Convert audio file format.

        Args:
            input_path: Input audio file path
            output_path: Output audio file path
            output_format: Target audio format
        """
        if not PYDUB_AVAILABLE:
            raise ImportError(
                "pydub is required for audio format conversion. "
                "Install with: pip install pydub"
            )

        audio = AudioSegment.from_file(str(input_path))
        audio.export(str(output_path), format=output_format.value)

    def get_audio_info(self, path: Union[str, Path]) -> dict:
        """Get information about an audio file.

        Args:
            path: Path to audio file

        Returns:
            Dictionary with audio metadata
        """
        if not PYDUB_AVAILABLE:
            raise ImportError(
                "pydub is required for audio info. "
                "Install with: pip install pydub"
            )

        audio = AudioSegment.from_file(str(path))
        return {
            "duration_seconds": len(audio) / 1000.0,
            "channels": audio.channels,
            "sample_width": audio.sample_width,
            "frame_rate": audio.frame_rate,
            "frame_width": audio.frame_width,
        }

    def text_to_speech(
        self,
        text: str,
        output_path: Union[str, Path],
        language: str = "en"
    ) -> None:
        """Convert text to speech (requires gTTS).

        Args:
            text: Text to convert
            output_path: Output audio file path
            language: Language code
        """
        try:
            from gtts import gTTS
        except ImportError:
            raise ImportError(
                "gTTS is required for text-to-speech. "
                "Install with: pip install gTTS"
            )

        tts = gTTS(text=text, lang=language)
        tts.save(str(output_path))

    def prepare_for_llm(
        self,
        audio: Union[sr.AudioData, str, Path],
        transcribe: bool = True,
        language: str = "en-US"
    ) -> dict:
        """Prepare audio for LLM input.

        Args:
            audio: AudioData object or path to audio file
            transcribe: Whether to transcribe audio to text
            language: Language code for transcription

        Returns:
            Dictionary with audio data for LLM
        """
        result = {
            "type": "audio",
            "source": {
                "type": "base64",
                "data": self.audio_to_base64(audio)
            }
        }

        if transcribe:
            result["transcription"] = self.speech_to_text(audio, language=language)

        return result
