from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

if TYPE_CHECKING:
    from labelvid.app import VideoClip


class ClipListWidgetItem(QtWidgets.QListWidgetItem):
    """List widget item for displaying a video clip."""

    def __init__(self, clip: VideoClip) -> None:
        super().__init__()
        self._clip = clip
        self._update_display()

    @property
    def clip(self) -> VideoClip:
        """Get the associated clip."""
        return self._clip

    def _update_display(self) -> None:
        """Update the display text and style."""
        r, g, b = self._clip.color
        duration = self._clip.end_frame - self._clip.start_frame

        # Set text with clip info
        text = (
            f"{self._clip.label}\n"
            f"  Frames: {self._clip.start_frame} → {self._clip.end_frame}\n"
            f"  Duration: {duration} frames"
        )
        self.setText(text)

        # Set color indicator
        self.setForeground(QtGui.QColor(r, g, b))

        # Set tooltip
        self.setToolTip(
            f"Label: {self._clip.label}\n"
            f"Start: {self._clip.start_frame}\n"
            f"End: {self._clip.end_frame}\n"
            f"Duration: {duration} frames"
        )


class ClipListWidget(QtWidgets.QListWidget):
    """List widget for displaying video clips."""
    
    # Signal emitted when delete key is pressed
    deleteRequested = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.setSpacing(2)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.deleteRequested.emit()
        else:
            super().keyPressEvent(event)

        # Set style
        self.setStyleSheet(
            """
            QListWidget {
                background-color: #16213e;
                border: none;
                font-size: 12px;
            }
            QListWidget::item {
                background-color: #1a1a2e;
                border: 1px solid #0f3460;
                border-radius: 4px;
                padding: 8px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #0f3460;
                border: 1px solid #e94560;
            }
            QListWidget::item:hover {
                background-color: #1f4068;
            }
            """
        )

    def addClip(self, clip: VideoClip) -> ClipListWidgetItem:
        """Add a clip to the list."""
        item = ClipListWidgetItem(clip)
        self.addItem(item)
        return item

    def selectedClips(self) -> list[VideoClip]:
        """Get selected clips."""
        return [item.clip for item in self.selectedItems()]

    def findItemByClip(self, clip: VideoClip) -> ClipListWidgetItem | None:
        """Find list item by clip."""
        for i in range(self.count()):
            item = self.item(i)
            if isinstance(item, ClipListWidgetItem) and item.clip is clip:
                return item
        return None
