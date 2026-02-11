"""Whisper transcriber for video caption extraction."""

from __future__ import annotations

import os
import os.path as osp
import tempfile
from dataclasses import dataclass
from typing import Callable

from loguru import logger

# Available Whisper models
# Reference: https://github.com/openai/whisper
WHISPER_MODELS = [
    "tiny",      # ~1 GB VRAM, fastest
    "tiny.en",   # English-only tiny
    "base",      # ~1 GB VRAM
    "base.en",   # English-only base
    "small",     # ~2 GB VRAM
    "small.en",  # English-only small
    "medium",    # ~5 GB VRAM
    "medium.en", # English-only medium
    "large",     # ~10 GB VRAM, most accurate
    "large-v2",  # Large v2
    "large-v3",  # Large v3
    "turbo",     # ~6 GB VRAM, optimized large-v3
]


@dataclass
class TranscriptSegment:
    """A segment of transcribed text with timing information."""

    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str     # Transcribed text

    @property
    def start_ms(self) -> int:
        """Start time in milliseconds."""
        return int(self.start * 1000)

    @property
    def end_ms(self) -> int:
        """End time in milliseconds."""
        return int(self.end * 1000)


class WhisperTranscriber:
    """Whisper-based transcriber for extracting captions from video."""

    def __init__(self, model_name: str = "turbo"):
        self._model_name = model_name
        self._model = None
        self._segments: list[TranscriptSegment] = []

    @property
    def model_name(self) -> str:
        return self._model_name

    @model_name.setter
    def model_name(self, value: str) -> None:
        if value != self._model_name:
            self._model_name = value
            self._model = None  # Reset model to reload with new name

    @property
    def segments(self) -> list[TranscriptSegment]:
        return self._segments

    @property
    def is_available(self) -> bool:
        """Check if Whisper is available."""
        try:
            import whisper  # noqa: F401
            return True
        except ImportError:
            return False

    def _load_model(self):
        """Load Whisper model."""
        if self._model is None:
            try:
                import whisper
                logger.info("Loading Whisper model: {}", self._model_name)
                self._model = whisper.load_model(self._model_name)
                logger.info("Whisper model loaded successfully")
            except ImportError:
                logger.error("Whisper not installed. Run: pip install openai-whisper")
                raise
            except Exception as e:
                logger.error("Failed to load Whisper model: {}", e)
                raise
        return self._model

    def has_audio_stream(self, video_path: str) -> bool:
        """Check if video file has an audio stream.

        Args:
            video_path: Path to video file

        Returns:
            True if video has audio stream, False otherwise
        """
        try:
            import subprocess

            # Use ffprobe to check for audio streams
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "a",  # Select audio streams only
                "-show_entries", "stream=codec_type",
                "-of", "csv=p=0",
                video_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            has_audio = "audio" in result.stdout
            logger.debug("Video {} audio stream: {}", video_path, has_audio)
            return has_audio
        except Exception as e:
            logger.warning("Could not check audio stream: {}", e)
            return True  # Assume has audio if check fails

    def extract_audio(self, video_path: str, output_path: str | None = None) -> str:
        """Extract audio from video file.

        Args:
            video_path: Path to video file
            output_path: Optional output path for audio file

        Returns:
            Path to extracted audio file

        Raises:
            ValueError: If video has no audio stream
            subprocess.CalledProcessError: If ffmpeg fails
            FileNotFoundError: If ffmpeg is not installed
        """
        # Check if video has audio stream first
        if not self.has_audio_stream(video_path):
            raise ValueError(
                f"Video file has no audio stream: {video_path}\n"
                "Cannot extract captions from a video without audio."
            )

        if output_path is None:
            # Create temp file
            fd, output_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)

        try:
            import subprocess

            # Use ffmpeg to extract audio
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # PCM 16-bit
                "-ar", "16000",  # 16kHz sample rate (Whisper requirement)
                "-ac", "1",  # Mono
                "-y",  # Overwrite
                output_path,
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            logger.info("Extracted audio to: {}", output_path)
            return output_path
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            if "does not contain any stream" in error_msg:
                raise ValueError(
                    f"Video file has no audio stream: {video_path}\n"
                    "Cannot extract captions from a video without audio."
                ) from e
            logger.error("Failed to extract audio: {}", error_msg)
            raise
        except FileNotFoundError:
            logger.error("ffmpeg not found. Please install ffmpeg.")
            raise

    def transcribe(
        self,
        video_path: str,
        language: str | None = None,
        task: str = "transcribe",
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> list[TranscriptSegment]:
        """Transcribe video and extract captions.

        Args:
            video_path: Path to video file
            language: Language code (e.g., 'en', 'zh', 'ja') or None for auto-detect
            task: 'transcribe' or 'translate' (translate to English)
            progress_callback: Optional callback for progress updates (progress, message)

        Returns:
            List of transcript segments with timing information
        """
        if progress_callback:
            progress_callback(0.0, "Extracting audio...")

        # Extract audio
        audio_path = self.extract_audio(video_path)

        try:
            if progress_callback:
                progress_callback(0.2, "Loading Whisper model...")

            model = self._load_model()

            if progress_callback:
                progress_callback(0.3, "Transcribing audio...")

            # Transcribe
            options = {
                "task": task,
                "verbose": False,
            }
            if language:
                options["language"] = language

            result = model.transcribe(audio_path, **options)

            if progress_callback:
                progress_callback(0.9, "Processing results...")

            # Convert to TranscriptSegment objects
            self._segments = []
            for segment in result.get("segments", []):
                self._segments.append(
                    TranscriptSegment(
                        start=segment["start"],
                        end=segment["end"],
                        text=segment["text"].strip(),
                    )
                )

            if progress_callback:
                progress_callback(1.0, f"Done! {len(self._segments)} segments extracted")

            logger.info(
                "Transcribed {} segments from {}",
                len(self._segments),
                video_path,
            )
            return self._segments

        finally:
            # Clean up temp audio file
            if osp.exists(audio_path) and audio_path.startswith(tempfile.gettempdir()):
                os.remove(audio_path)

    def get_caption_at_time(self, time_seconds: float) -> str | None:
        """Get caption text at a specific time.

        Args:
            time_seconds: Time in seconds

        Returns:
            Caption text or None if no caption at this time
        """
        for segment in self._segments:
            if segment.start <= time_seconds <= segment.end:
                return segment.text
        return None

    def get_captions_in_range(
        self, start_seconds: float, end_seconds: float
    ) -> list[TranscriptSegment]:
        """Get all captions within a time range.

        Args:
            start_seconds: Start time in seconds
            end_seconds: End time in seconds

        Returns:
            List of transcript segments in the range
        """
        return [
            seg for seg in self._segments
            if seg.end >= start_seconds and seg.start <= end_seconds
        ]

    def export_srt(self, output_path: str) -> None:
        """Export captions to SRT format.

        Args:
            output_path: Path to output SRT file
        """
        with open(output_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(self._segments, 1):
                # SRT format: index, timecode, text, blank line
                start_time = self._format_srt_time(segment.start)
                end_time = self._format_srt_time(segment.end)
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{segment.text}\n")
                f.write("\n")
        logger.info("Exported SRT to: {}", output_path)

    def export_vtt(self, output_path: str) -> None:
        """Export captions to WebVTT format.

        Args:
            output_path: Path to output VTT file
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            for segment in self._segments:
                start_time = self._format_vtt_time(segment.start)
                end_time = self._format_vtt_time(segment.end)
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{segment.text}\n")
                f.write("\n")
        logger.info("Exported VTT to: {}", output_path)

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format time for SRT (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _format_vtt_time(seconds: float) -> str:
        """Format time for WebVTT (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    def clear(self) -> None:
        """Clear loaded segments."""
        self._segments = []
