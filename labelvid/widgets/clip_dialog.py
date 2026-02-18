"""Dialog for editing video clip information."""

from __future__ import annotations

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt


class ObjectInfo:
    """Container for object list information."""
    
    def __init__(self):
        self.objects = []  # List of {category_id, instance_id, label_name}
    
    def get_display_items(self) -> list[str]:
        """Get list of formatted display strings (label [cat:X, inst:Y])."""
        return [
            f"{obj['label_name']} [cat:{obj['category_id']}, inst:{obj['instance_id']}]"
            for obj in self.objects
        ]
    
    def get_labels(self) -> list[str]:
        """Get list of label names only."""
        return [obj["label_name"] for obj in self.objects]
    
    def get_object_by_display(self, display_text: str) -> dict | None:
        """Get object info by display text.
        
        Args:
            display_text: Either "label [cat:X, inst:Y]" or just "label"
        
        Returns:
            Object dict or None
        """
        # Try to extract label and IDs from display text
        if " [cat:" in display_text and ", inst:" in display_text:
            try:
                # Extract: "label [cat:X, inst:Y]"
                label = display_text.split(" [cat:")[0]
                id_part = display_text.split(" [cat:")[1].rstrip("]")
                cat_str, inst_str = id_part.split(", inst:")
                category_id = int(cat_str)
                instance_id = int(inst_str)
                
                # Find exact match by label, category, and instance
                for obj in self.objects:
                    if (obj["label_name"] == label and 
                        obj["category_id"] == category_id and 
                        obj["instance_id"] == instance_id):
                        return obj
            except (ValueError, IndexError):
                pass
        
        # Fallback: try to match by label only
        if " [cat:" in display_text:
            label = display_text.split(" [cat:")[0]
        else:
            label = display_text
        
        return self.get_object_by_label(label)
    
    def get_object_by_label(self, label: str) -> dict | None:
        """Get object info by label name."""
        for obj in self.objects:
            if obj["label_name"] == label:
                return obj
        return None


# Global object list
_object_info = ObjectInfo()


def set_object_list(objects: list[dict]) -> None:
    """Set the global object list.
    
    Args:
        objects: List of dicts with keys: category_id, instance_id, label_name
    """
    _object_info.objects = objects


def get_object_list() -> list[dict]:
    """Get the global object list.
    
    Returns:
        List of dicts with keys: category_id, instance_id, label_name
    """
    return _object_info.objects


class ClipDialog(QtWidgets.QDialog):
    """Dialog for creating or editing a video clip."""
    
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        label: str = "",
        detection_score: float | None = None,
        recognition_score: float | None = None,
        is_hazard: bool | None = None,
        description: str = "",
        recognition: str = "",
        scene: str = "",
        category_id: int = 0,
        instance_id: int = 0,
        title: str = "Edit Clip",
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        
        self._init_ui(label, detection_score, recognition_score, is_hazard, description, recognition, scene, category_id, instance_id)
    
    def _init_ui(
        self,
        label: str,
        detection_score: float | None,
        recognition_score: float | None,
        is_hazard: bool | None,
        description: str,
        recognition: str,
        scene: str,
        category_id: int,
        instance_id: int,
    ) -> None:
        """Initialize the UI."""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Form layout
        form_layout = QtWidgets.QFormLayout()
        
        # Label (required) - ComboBox if object list available, otherwise LineEdit
        label_layout = QtWidgets.QHBoxLayout()
        
        if _object_info.objects:
            # Use ComboBox with object list
            self.label_combo = QtWidgets.QComboBox()
            self.label_combo.setEditable(True)
            
            # Add formatted items: "label [cat:X, inst:Y]"
            display_items = _object_info.get_display_items()
            self.label_combo.addItems(display_items)
            
            # Set current label if it exists
            if label:
                # Try to find exact match with current category/instance
                if category_id != 0 or instance_id != 0:
                    target_text = f"{label} [cat:{category_id}, inst:{instance_id}]"
                    index = self.label_combo.findText(target_text)
                    if index >= 0:
                        self.label_combo.setCurrentIndex(index)
                    else:
                        # Try to find by label only
                        for i, item in enumerate(display_items):
                            if item.startswith(label + " ["):
                                self.label_combo.setCurrentIndex(i)
                                break
                        else:
                            # Not found, set as plain text
                            self.label_combo.setEditText(label)
                else:
                    # Try to find by label name
                    found = False
                    for i, item in enumerate(display_items):
                        if item.startswith(label + " ["):
                            self.label_combo.setCurrentIndex(i)
                            found = True
                            break
                    if not found:
                        self.label_combo.setEditText(label)
            
            # Connect to update category/instance IDs
            self.label_combo.currentTextChanged.connect(self._on_label_changed)
            
            label_layout.addWidget(self.label_combo)
            self.label_input = None  # Not used when combo is available
        else:
            # Use LineEdit (fallback)
            self.label_input = QtWidgets.QLineEdit(label)
            self.label_input.setPlaceholderText("Required")
            label_layout.addWidget(self.label_input)
            self.label_combo = None
        
        form_layout.addRow("Label *:", label_layout)
        
        # Category ID and Instance ID
        id_layout = QtWidgets.QHBoxLayout()
        
        self.category_spin = QtWidgets.QSpinBox()
        self.category_spin.setRange(0, 9999)
        self.category_spin.setValue(category_id)
        id_layout.addWidget(QtWidgets.QLabel("Category:"))
        id_layout.addWidget(self.category_spin)
        
        self.instance_spin = QtWidgets.QSpinBox()
        self.instance_spin.setRange(0, 9999)
        self.instance_spin.setValue(instance_id)
        id_layout.addWidget(QtWidgets.QLabel("Instance:"))
        id_layout.addWidget(self.instance_spin)
        
        form_layout.addRow("IDs:", id_layout)
        
        # Recognition (optional)
        self.recognition_input = QtWidgets.QLineEdit(recognition)
        self.recognition_input.setPlaceholderText("Optional")
        form_layout.addRow("Recognition:", self.recognition_input)
        
        # Scene (optional)
        self.scene_input = QtWidgets.QLineEdit(scene)
        self.scene_input.setPlaceholderText("Optional")
        form_layout.addRow("Scene:", self.scene_input)
        
        # Detection Score (optional, 0-5)
        det_layout = QtWidgets.QHBoxLayout()
        self.det_score_spin = QtWidgets.QDoubleSpinBox()
        self.det_score_spin.setRange(0.0, 5.0)
        self.det_score_spin.setSingleStep(0.1)
        self.det_score_spin.setDecimals(1)
        self.det_score_spin.setSpecialValueText("Not set")
        if detection_score is not None:
            self.det_score_spin.setValue(detection_score)
        else:
            self.det_score_spin.setValue(0.0)
        det_layout.addWidget(self.det_score_spin)
        
        self.det_clear_btn = QtWidgets.QPushButton("Clear")
        self.det_clear_btn.setMaximumWidth(60)
        self.det_clear_btn.clicked.connect(lambda: self.det_score_spin.setValue(0.0))
        det_layout.addWidget(self.det_clear_btn)
        
        form_layout.addRow("Detection Score (0-5):", det_layout)
        
        # Recognition Score (optional, 0-5)
        rec_layout = QtWidgets.QHBoxLayout()
        self.rec_score_spin = QtWidgets.QDoubleSpinBox()
        self.rec_score_spin.setRange(0.0, 5.0)
        self.rec_score_spin.setSingleStep(0.1)
        self.rec_score_spin.setDecimals(1)
        self.rec_score_spin.setSpecialValueText("Not set")
        if recognition_score is not None:
            self.rec_score_spin.setValue(recognition_score)
        else:
            self.rec_score_spin.setValue(0.0)
        rec_layout.addWidget(self.rec_score_spin)
        
        self.rec_clear_btn = QtWidgets.QPushButton("Clear")
        self.rec_clear_btn.setMaximumWidth(60)
        self.rec_clear_btn.clicked.connect(lambda: self.rec_score_spin.setValue(0.0))
        rec_layout.addWidget(self.rec_clear_btn)
        
        form_layout.addRow("Recognition Score (0-5):", rec_layout)
        
        # Is Hazard (optional)
        hazard_layout = QtWidgets.QHBoxLayout()
        self.hazard_combo = QtWidgets.QComboBox()
        self.hazard_combo.addItems(["Not set", "No (Safe)", "Yes (Hazard)"])
        if is_hazard is None:
            self.hazard_combo.setCurrentIndex(0)
        elif is_hazard:
            self.hazard_combo.setCurrentIndex(2)
        else:
            self.hazard_combo.setCurrentIndex(1)
        hazard_layout.addWidget(self.hazard_combo)
        hazard_layout.addStretch()
        
        form_layout.addRow("Is Hazard:", hazard_layout)
        
        # Description (optional)
        self.description_input = QtWidgets.QPlainTextEdit(description)
        self.description_input.setPlaceholderText("Optional description...")
        self.description_input.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set focus to label
        if self.label_combo:
            self.label_combo.setFocus()
        elif self.label_input:
            self.label_input.setFocus()
            self.label_input.selectAll()
    
    def _on_label_changed(self, display_text: str) -> None:
        """Update category and instance IDs when label changes.
        
        Args:
            display_text: Either "label [cat:X, inst:Y]" or just "label"
        """
        obj = _object_info.get_object_by_display(display_text)
        if obj:
            self.category_spin.setValue(obj["category_id"])
            self.instance_spin.setValue(obj["instance_id"])
    
    def _validate_and_accept(self) -> None:
        """Validate input and accept dialog."""
        if self.label_combo:
            text = self.label_combo.currentText().strip()
            # Extract label name (remove " [cat:X, inst:Y]" if present)
            if " [cat:" in text:
                label = text.split(" [cat:")[0]
            else:
                label = text
        else:
            label = self.label_input.text().strip()
        
        if not label:
            QtWidgets.QMessageBox.warning(
                self,
                "Validation Error",
                "Label is required. Please enter a label for this clip.",
            )
            if self.label_combo:
                self.label_combo.setFocus()
            else:
                self.label_input.setFocus()
            return
        
        self.accept()
    
    def get_values(self) -> tuple[str, float | None, float | None, bool | None, str, str, str, int, int]:
        """Get the entered values.
        
        Returns:
            Tuple of (label, detection_score, recognition_score, is_hazard, description, recognition, scene, category_id, instance_id)
        """
        if self.label_combo:
            text = self.label_combo.currentText().strip()
            # Extract label name (remove " [cat:X, inst:Y]" if present)
            if " [cat:" in text:
                label = text.split(" [cat:")[0]
            else:
                label = text
        else:
            label = self.label_input.text().strip()
        
        # Detection score (0.0 means not set)
        det_score = self.det_score_spin.value()
        detection_score = det_score if det_score > 0.0 else None
        
        # Recognition score (0.0 means not set)
        rec_score = self.rec_score_spin.value()
        recognition_score = rec_score if rec_score > 0.0 else None
        
        # Is hazard
        hazard_index = self.hazard_combo.currentIndex()
        if hazard_index == 0:
            is_hazard = None
        elif hazard_index == 1:
            is_hazard = False
        else:
            is_hazard = True
        
        # Description
        description = self.description_input.toPlainText().strip()
        
        # Recognition and Scene
        recognition = self.recognition_input.text().strip()
        scene = self.scene_input.text().strip()
        
        # Category and Instance IDs
        category_id = self.category_spin.value()
        instance_id = self.instance_spin.value()
        
        return label, detection_score, recognition_score, is_hazard, description, recognition, scene, category_id, instance_id
