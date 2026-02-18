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

        # Build display text
        text_lines = [f"{self._clip.label}"]
        text_lines.append(f"  Frames: {self._clip.start_frame} → {self._clip.end_frame} ({duration})")
        
        # Add category and instance IDs if not default
        if self._clip.category_id != 0 or self._clip.instance_id != 0:
            text_lines.append(f"  Cat: {self._clip.category_id} | Inst: {self._clip.instance_id}")
        
        # Add scores if present
        if self._clip.detection_score is not None or self._clip.recognition_score is not None:
            det_str = f"{self._clip.detection_score:.1f}" if self._clip.detection_score is not None else "—"
            rec_str = f"{self._clip.recognition_score:.1f}" if self._clip.recognition_score is not None else "—"
            text_lines.append(f"  Det: {det_str} | Rec: {rec_str}")
        
        # Add hazard indicator
        if self._clip.is_hazard is not None:
            hazard_icon = "Hazard" if self._clip.is_hazard else "No Hazard"
            text_lines.append(f"  {hazard_icon}")
        
        # Add recognition if present
        if self._clip.recognition:
            text_lines.append(f"  Recognition: {self._clip.recognition}")
        
        # Add scene if present
        if self._clip.scene:
            text_lines.append(f"  Scene: {self._clip.scene}")
        
        # Add description preview if present
        if self._clip.description:
            desc_preview = self._clip.description[:40] + "..." if len(self._clip.description) > 40 else self._clip.description
            text_lines.append(f"  {desc_preview}")
        
        self.setText("\n".join(text_lines))

        # Set color indicator
        self.setForeground(QtGui.QColor(r, g, b))

        # Build tooltip
        tooltip_lines = [
            f"Label: {self._clip.label}",
            f"Start: {self._clip.start_frame}",
            f"End: {self._clip.end_frame}",
            f"Duration: {duration} frames",
        ]
        
        # Add IDs
        tooltip_lines.append(f"Category ID: {self._clip.category_id}")
        tooltip_lines.append(f"Instance ID: {self._clip.instance_id}")
        
        if self._clip.detection_score is not None:
            tooltip_lines.append(f"Detection Score: {self._clip.detection_score:.2f}")
        if self._clip.recognition_score is not None:
            tooltip_lines.append(f"Recognition Score: {self._clip.recognition_score:.2f}")
        if self._clip.is_hazard is not None:
            tooltip_lines.append(f"Hazard: {'Yes' if self._clip.is_hazard else 'No'}")
        if self._clip.recognition:
            tooltip_lines.append(f"Recognition: {self._clip.recognition}")
        if self._clip.scene:
            tooltip_lines.append(f"Scene: {self._clip.scene}")
        if self._clip.description:
            tooltip_lines.append(f"Description: {self._clip.description}")
        
        self.setToolTip("\n".join(tooltip_lines))


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
