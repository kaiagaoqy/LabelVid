from __future__ import annotations

from labelvid.app import VideoClip
from labelvid.app import _format_time
from labelvid.app import _get_color_for_index


def test_video_clip_creation() -> None:
    """Test VideoClip dataclass creation."""
    clip = VideoClip(label="test", start_frame=10, end_frame=100)
    assert clip.label == "test"
    assert clip.start_frame == 10
    assert clip.end_frame == 100


def test_video_clip_swap_frames() -> None:
    """Test that VideoClip swaps start/end if end < start."""
    clip = VideoClip(label="test", start_frame=100, end_frame=10)
    assert clip.start_frame == 10
    assert clip.end_frame == 100


def test_format_time() -> None:
    """Test time formatting."""
    assert _format_time(0) == "00:00:00"
    assert _format_time(61) == "00:01:01"
    assert _format_time(3661) == "01:01:01"


def test_get_color_for_index() -> None:
    """Test color generation for clip indices."""
    color0 = _get_color_for_index(0)
    color1 = _get_color_for_index(1)
    assert color0 != color1
    assert len(color0) == 3
    assert all(0 <= c <= 255 for c in color0)
