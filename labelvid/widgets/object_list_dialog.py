"""Dialog for managing object list."""

from __future__ import annotations

import json
from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt


class ObjectListDialog(QtWidgets.QDialog):
    """Dialog for importing and managing object list."""
    
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Object List Manager")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.objects = []  # List of {category_id, instance_id, label_name}
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Info label
        info_label = QtWidgets.QLabel(
            "Import a JSON file containing object definitions.\n"
            "Format: [{\"category_id\": 1, \"instance_id\": 1, \"label_name\": \"backpack\"}, ...]"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Import button
        import_btn = QtWidgets.QPushButton("📂 Import JSON")
        import_btn.clicked.connect(self._import_json)
        layout.addWidget(import_btn)
        
        # Object list table
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Category ID", "Instance ID", "Label Name"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        add_btn = QtWidgets.QPushButton("➕ Add")
        add_btn.clicked.connect(self._add_object)
        button_layout.addWidget(add_btn)
        
        remove_btn = QtWidgets.QPushButton("➖ Remove")
        remove_btn.clicked.connect(self._remove_object)
        button_layout.addWidget(remove_btn)
        
        clear_btn = QtWidgets.QPushButton("🗑️ Clear All")
        clear_btn.clicked.connect(self._clear_all)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Dialog buttons
        dialog_buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(dialog_buttons)
    
    def _import_json(self) -> None:
        """Import object list from JSON file."""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Import Object List",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("JSON must be a list of objects")
            
            # Validate and load objects
            loaded_objects = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                category_id = item.get("category_id", 0)
                instance_id = item.get("instance_id", 0)
                label_name = item.get("label_name", "")
                
                if label_name:
                    loaded_objects.append({
                        "category_id": int(category_id),
                        "instance_id": int(instance_id),
                        "label_name": str(label_name)
                    })
            
            if loaded_objects:
                self.objects = loaded_objects
                self._update_table()
                QtWidgets.QMessageBox.information(
                    self,
                    "Success",
                    f"Loaded {len(loaded_objects)} objects from {Path(filename).name}"
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "No Objects",
                    "No valid objects found in the JSON file."
                )
        
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import JSON:\n{str(e)}"
            )
    
    def _add_object(self) -> None:
        """Add a new object manually."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add Object")
        
        layout = QtWidgets.QFormLayout(dialog)
        
        category_spin = QtWidgets.QSpinBox()
        category_spin.setRange(0, 9999)
        layout.addRow("Category ID:", category_spin)
        
        instance_spin = QtWidgets.QSpinBox()
        instance_spin.setRange(0, 9999)
        layout.addRow("Instance ID:", instance_spin)
        
        label_input = QtWidgets.QLineEdit()
        layout.addRow("Label Name:", label_input)
        
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            label_name = label_input.text().strip()
            if label_name:
                self.objects.append({
                    "category_id": category_spin.value(),
                    "instance_id": instance_spin.value(),
                    "label_name": label_name
                })
                self._update_table()
    
    def _remove_object(self) -> None:
        """Remove selected object."""
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            return
        
        # Remove in reverse order to maintain indices
        for row in sorted(selected_rows, reverse=True):
            if 0 <= row < len(self.objects):
                del self.objects[row]
        
        self._update_table()
    
    def _clear_all(self) -> None:
        """Clear all objects."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Clear All",
            "Are you sure you want to clear all objects?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.objects.clear()
            self._update_table()
    
    def _update_table(self) -> None:
        """Update the table with current objects."""
        self.table.setRowCount(len(self.objects))
        
        for i, obj in enumerate(self.objects):
            # Category ID
            cat_item = QtWidgets.QTableWidgetItem(str(obj["category_id"]))
            cat_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, cat_item)
            
            # Instance ID
            inst_item = QtWidgets.QTableWidgetItem(str(obj["instance_id"]))
            inst_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, inst_item)
            
            # Label Name
            label_item = QtWidgets.QTableWidgetItem(obj["label_name"])
            self.table.setItem(i, 2, label_item)
    
    def get_objects(self) -> list[dict]:
        """Get the list of objects.
        
        Returns:
            List of dicts with keys: category_id, instance_id, label_name
        """
        return self.objects
    
    def set_objects(self, objects: list[dict]) -> None:
        """Set the list of objects.
        
        Args:
            objects: List of dicts with keys: category_id, instance_id, label_name
        """
        self.objects = objects
        self._update_table()
