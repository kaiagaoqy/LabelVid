"""AI automation support for labelvid."""

from __future__ import annotations

OsamSession = None

try:
    import osam  # noqa: F401

    from ._osam_session import OsamSession
except ImportError:
    pass

from . import polygon_from_mask

__all__ = ["OsamSession", "polygon_from_mask"]
