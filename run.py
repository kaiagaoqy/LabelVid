#!/usr/bin/env python
"""
Usage:
    python run.py
    python run.py /path/to/video.mp4
    python run.py /path/to/video/folder

Features:
    - Video Mode: Video clipping, marking clips, exporting frames
    - Image Mode: Image annotation (polygon, bounding box, AI assisted)
    - Export labelme compatible JSON format

Keyboard Shortcuts:
    - Ctrl+M: Toggle Video/Image mode
    - P: Polygon drawing
    - R: Rectangle drawing
    - A: AI Polygon (SAM)
    - E: Edit mode
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from labelvid.__main__ import main

if __name__ == "__main__":
    main()
