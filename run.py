#!/usr/bin/env python
"""
直接运行脚本，用于测试开发。

使用方法:
    python run.py
    python run.py /path/to/video.mp4
    python run.py /path/to/video/folder

功能:
    - Video Mode: 视频剪辑，标记片段，导出帧
    - Image Mode: 图像标注 (polygon, bounding box, AI辅助)
    - 导出 labelme 兼容的 JSON 格式

快捷键:
    - Ctrl+M: 切换 Video/Image 模式
    - P: Polygon 绘制
    - R: Rectangle 绘制
    - A: AI Polygon (SAM)
    - E: 编辑模式
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from labelvid.__main__ import main

if __name__ == "__main__":
    main()
