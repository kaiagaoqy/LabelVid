"""Clip timeline widget for visualizing and editing clip markers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

if TYPE_CHECKING:
    from labelvid.app import VideoClip


# Predefined colors for clips (cycle through these)
CLIP_COLORS = [
    (76, 175, 80),    # Green
    (33, 150, 243),   # Blue
    (255, 152, 0),    # Orange
    (156, 39, 176),   # Purple
    (0, 188, 212),    # Cyan
    (255, 87, 34),    # Deep Orange
    (233, 30, 99),    # Pink
    (139, 195, 74),   # Light Green
    (103, 58, 183),   # Deep Purple
    (255, 193, 7),    # Amber
]


class ClipTimelineWidget(QtWidgets.QWidget):
    """Widget displaying clip markers on a timeline.
    
    Shows vertical bars for start (green) and end (red) of each clip.
    Bars can be dragged to adjust clip boundaries.
    """
    
    # Signal emitted when a clip marker is being dragged
    # (clip_index, is_start, frame_number)
    markerDragging = QtCore.pyqtSignal(int, bool, int)
    
    # Signal emitted when a clip marker drag is finished
    # (clip_index, is_start, frame_number)
    markerDragFinished = QtCore.pyqtSignal(int, bool, int)
    
    # Signal emitted when a marker is clicked (to select the clip)
    markerClicked = QtCore.pyqtSignal(int)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._clips: list[VideoClip] = []
        self._total_frames: int = 0
        self._current_frame: int = 0
        
        # Dragging state
        self._dragging: bool = False
        self._drag_clip_index: int = -1
        self._drag_is_start: bool = True
        self._hover_clip_index: int = -1
        self._hover_is_start: bool = True
        
        # Search results (frame numbers where keywords found)
        self._search_results: list[int] = []
        
        # Pending clip start frame (before marking end)
        self._pending_start_frame: int | None = None
        
        # Appearance
        self._marker_width: int = 6
        self._bar_height: int = 20
        
        self.setMinimumHeight(self._bar_height + 4)
        self.setMaximumHeight(self._bar_height + 4)
        self.setMouseTracking(True)
        self.setCursor(Qt.ArrowCursor)
        
        # Tooltip
        self.setToolTip("Drag markers to adjust clip boundaries")

    def setClips(self, clips: list[VideoClip]) -> None:
        """Set the clips to display."""
        self._clips = clips
        self.update()

    def setTotalFrames(self, total: int) -> None:
        """Set total number of frames."""
        self._total_frames = total
        self.update()

    def setCurrentFrame(self, frame: int) -> None:
        """Set current frame position."""
        self._current_frame = frame
        self.update()

    def setSearchResults(self, frames: list[int]) -> None:
        """Set search result frames to highlight.
        
        Args:
            frames: List of frame numbers where keywords were found
        """
        self._search_results = frames
        self.update()

    def setPendingStartFrame(self, frame: int | None) -> None:
        """Set pending clip start frame to display.
        
        Args:
            frame: Frame number where clip start was marked, or None to clear
        """
        self._pending_start_frame = frame
        self.update()

    def _frame_to_x(self, frame: int) -> int:
        """Convert frame number to x coordinate."""
        if self._total_frames <= 0:
            return 0
        width = self.width() - self._marker_width
        return int((frame / self._total_frames) * width) + self._marker_width // 2

    def _x_to_frame(self, x: int) -> int:
        """Convert x coordinate to frame number."""
        if self._total_frames <= 0:
            return 0
        width = self.width() - self._marker_width
        x = max(0, min(x - self._marker_width // 2, width))
        return int((x / width) * self._total_frames)

    def _get_marker_at(self, pos: QtCore.QPoint) -> tuple[int, bool] | None:
        """Get the clip marker at the given position.
        
        Returns:
            (clip_index, is_start) or None if no marker at position
        """
        x = pos.x()
        
        for i, clip in enumerate(self._clips):
            # Check start marker
            start_x = self._frame_to_x(clip.start_frame)
            if abs(x - start_x) <= self._marker_width:
                return (i, True)
            
            # Check end marker
            end_x = self._frame_to_x(clip.end_frame)
            if abs(x - end_x) <= self._marker_width:
                return (i, False)
        
        return None

    def _get_clip_color(self, index: int) -> tuple[int, int, int]:
        """Get color for a clip by index."""
        return CLIP_COLORS[index % len(CLIP_COLORS)]

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """Paint the timeline with clip markers."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QtGui.QColor(30, 30, 40))
        
        if self._total_frames <= 0:
            return
        
        # Draw clip regions (semi-transparent fill between start and end)
        for i, clip in enumerate(self._clips):
            color = self._get_clip_color(i)
            start_x = self._frame_to_x(clip.start_frame)
            end_x = self._frame_to_x(clip.end_frame)
            
            # Fill region
            fill_color = QtGui.QColor(color[0], color[1], color[2], 60)
            painter.fillRect(
                start_x, 2,
                end_x - start_x, self._bar_height,
                fill_color
            )
        
        # Draw markers
        for i, clip in enumerate(self._clips):
            color = self._get_clip_color(i)
            start_x = self._frame_to_x(clip.start_frame)
            end_x = self._frame_to_x(clip.end_frame)
            
            # Start marker (brighter/highlighted if hovering)
            if self._hover_clip_index == i and self._hover_is_start:
                start_color = QtGui.QColor(255, 255, 255)
            else:
                start_color = QtGui.QColor(color[0], color[1], color[2])
            
            painter.fillRect(
                start_x - self._marker_width // 2, 0,
                self._marker_width, self._bar_height + 4,
                start_color
            )
            
            # End marker
            if self._hover_clip_index == i and not self._hover_is_start:
                end_color = QtGui.QColor(255, 255, 255)
            else:
                # Make end marker slightly darker
                end_color = QtGui.QColor(
                    max(0, color[0] - 40),
                    max(0, color[1] - 40),
                    max(0, color[2] - 40)
                )
            
            painter.fillRect(
                end_x - self._marker_width // 2, 0,
                self._marker_width, self._bar_height + 4,
                end_color
            )
            
            # Draw label if there's enough space
            label_width = end_x - start_x
            if label_width > 30:
                painter.setPen(QtGui.QColor(255, 255, 255, 180))
                font = painter.font()
                font.setPointSize(8)
                painter.setFont(font)
                text_rect = QtCore.QRect(
                    start_x + 2, 2,
                    label_width - 4, self._bar_height
                )
                painter.drawText(
                    text_rect,
                    Qt.AlignCenter | Qt.TextSingleLine,
                    clip.label[:10] + "..." if len(clip.label) > 10 else clip.label
                )
        
        # Draw search result markers (before current frame indicator)
        if self._search_results:
            # Group consecutive frames to avoid drawing too many lines
            search_ranges = self._group_consecutive_frames(self._search_results)
            
            for start_frame, end_frame in search_ranges:
                start_x = self._frame_to_x(start_frame)
                end_x = self._frame_to_x(end_frame)
                
                # Draw as a filled region if range is wide enough
                if end_x - start_x > 2:
                    # Cyan/blue highlight for search results
                    search_color = QtGui.QColor(0, 255, 255, 100)  # Cyan, semi-transparent
                    painter.fillRect(
                        start_x, 0,
                        end_x - start_x, self._bar_height + 4,
                        search_color
                    )
                else:
                    # Draw as a thin line for single frames
                    painter.setPen(QtGui.QPen(QtGui.QColor(0, 255, 255), 2))
                    painter.drawLine(start_x, 0, start_x, self._bar_height + 4)
        
        # Draw pending clip start marker (green dashed line)
        if self._pending_start_frame is not None:
            pending_x = self._frame_to_x(self._pending_start_frame)
            pen = QtGui.QPen(QtGui.QColor(76, 175, 80), 3)  # Green
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(pending_x, 0, pending_x, self._bar_height + 4)
            
            # Draw small label
            painter.setPen(QtGui.QColor(76, 175, 80))
            font = painter.font()
            font.setPointSize(7)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(pending_x + 2, 10, "START")
        
        # Draw current frame indicator (on top of everything)
        current_x = self._frame_to_x(self._current_frame)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 0), 2))
        painter.drawLine(current_x, 0, current_x, self._bar_height + 4)

    def _group_consecutive_frames(self, frames: list[int]) -> list[tuple[int, int]]:
        """Group consecutive frames into ranges.
        
        Args:
            frames: List of frame numbers
            
        Returns:
            List of (start_frame, end_frame) tuples
        """
        if not frames:
            return []
        
        ranges = []
        start = frames[0]
        prev = frames[0]
        
        for frame in frames[1:]:
            if frame - prev > 1:
                # Gap found, end current range
                ranges.append((start, prev))
                start = frame
            prev = frame
        
        # Add last range
        ranges.append((start, prev))
        return ranges

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle mouse press - start dragging if on a marker."""
        if event.button() == Qt.LeftButton:
            marker = self._get_marker_at(event.pos())
            if marker is not None:
                self._dragging = True
                self._drag_clip_index, self._drag_is_start = marker
                self.setCursor(Qt.SizeHorCursor)
                
                # Emit signal to select this clip and show the frame
                self.markerClicked.emit(self._drag_clip_index)
                
                # Emit dragging signal with current frame
                clip = self._clips[self._drag_clip_index]
                frame = clip.start_frame if self._drag_is_start else clip.end_frame
                self.markerDragging.emit(self._drag_clip_index, self._drag_is_start, frame)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle mouse move - drag marker or update hover state."""
        if self._dragging and self._drag_clip_index >= 0:
            # Calculate new frame position
            new_frame = self._x_to_frame(event.pos().x())
            new_frame = max(0, min(new_frame, self._total_frames - 1))
            
            # Get the clip being edited
            clip = self._clips[self._drag_clip_index]
            
            # Validate: start must be before end
            if self._drag_is_start:
                new_frame = min(new_frame, clip.end_frame - 1)
            else:
                new_frame = max(new_frame, clip.start_frame + 1)
            
            # Emit signal
            self.markerDragging.emit(self._drag_clip_index, self._drag_is_start, new_frame)
            self.update()
        else:
            # Update hover state
            marker = self._get_marker_at(event.pos())
            if marker is not None:
                self._hover_clip_index, self._hover_is_start = marker
                self.setCursor(Qt.SizeHorCursor)
            else:
                self._hover_clip_index = -1
                self.setCursor(Qt.ArrowCursor)
            self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle mouse release - finish dragging."""
        if event.button() == Qt.LeftButton and self._dragging:
            # Calculate final frame position
            new_frame = self._x_to_frame(event.pos().x())
            new_frame = max(0, min(new_frame, self._total_frames - 1))
            
            # Get the clip being edited
            clip = self._clips[self._drag_clip_index]
            
            # Validate: start must be before end
            if self._drag_is_start:
                new_frame = min(new_frame, clip.end_frame - 1)
            else:
                new_frame = max(new_frame, clip.start_frame + 1)
            
            # Emit finished signal
            self.markerDragFinished.emit(
                self._drag_clip_index, self._drag_is_start, new_frame
            )
            
            self._dragging = False
            self._drag_clip_index = -1
            self.setCursor(Qt.ArrowCursor)
            self.update()

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        """Handle mouse leave - clear hover state."""
        self._hover_clip_index = -1
        self.update()
