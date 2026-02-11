"""Whisper integration for caption extraction."""

from __future__ import annotations

from ._transcriber import WhisperTranscriber
from ._transcriber import WHISPER_MODELS

__all__ = ["WhisperTranscriber", "WHISPER_MODELS"]
