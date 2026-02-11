from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt


class VideoPlayerWidget(QtWidgets.QWidget):
    """Widget for displaying video frames."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QtGui.QPixmap | None = None
        self._scale: float = 1.0
        self.setMinimumSize(320, 240)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.setStyleSheet("background-color: #1a1a2e;")

    def display_frame(self, frame: NDArray[np.uint8]) -> None:
        """Display a video frame (BGR format from OpenCV)."""
        if frame is None:
            return

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb_frame.shape
        bytes_per_line = channels * width

        # Create QImage from numpy array
        qimage = QtGui.QImage(
            rgb_frame.data,
            width,
            height,
            bytes_per_line,
            QtGui.QImage.Format_RGB888,
        )

        # Convert to QPixmap
        self._pixmap = QtGui.QPixmap.fromImage(qimage)
        self.update()

    def clear(self) -> None:
        """Clear the displayed frame."""
        self._pixmap = None
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """Paint the video frame."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

        # Fill background
        painter.fillRect(self.rect(), QtGui.QColor("#1a1a2e"))

        if self._pixmap is not None:
            # Calculate scaled size maintaining aspect ratio
            widget_size = self.size()
            pixmap_size = self._pixmap.size()

            # Calculate scale to fit widget while maintaining aspect ratio
            scale_x = widget_size.width() / pixmap_size.width()
            scale_y = widget_size.height() / pixmap_size.height()
            self._scale = min(scale_x, scale_y)

            # Calculate scaled dimensions
            scaled_width = int(pixmap_size.width() * self._scale)
            scaled_height = int(pixmap_size.height() * self._scale)

            # Calculate position to center the image
            x = (widget_size.width() - scaled_width) // 2
            y = (widget_size.height() - scaled_height) // 2

            # Draw the scaled pixmap
            target_rect = QtCore.QRect(x, y, scaled_width, scaled_height)
            painter.drawPixmap(target_rect, self._pixmap)
        else:
            # Draw placeholder text
            painter.setPen(QtGui.QColor("#666666"))
            painter.setFont(QtGui.QFont("Arial", 16))
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                "No video loaded\n\nOpen a video file to start",
            )

        painter.end()

    def sizeHint(self) -> QtCore.QSize:
        """Return the preferred size."""
        return QtCore.QSize(800, 600)
