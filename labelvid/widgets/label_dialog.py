"""Label dialog for shape annotation."""

from __future__ import annotations

import re
from typing import cast

from loguru import logger
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from labelvid import utils

# Global object list info (same as in clip_dialog.py)
_label_dialog_object_info = None


def set_label_dialog_object_list(objects: list[dict] | None) -> None:
    """Set the global object list for label dialog."""
    global _label_dialog_object_info
    if objects:
        _label_dialog_object_info = {
            'objects': objects,
            'display_items': [
                f"{obj['label_name']} [cat:{obj['category_id']}, inst:{obj['instance_id']}]"
                for obj in objects
            ]
        }
    else:
        _label_dialog_object_info = None


def get_label_dialog_object_list() -> list[dict] | None:
    """Get the global object list for label dialog."""
    if _label_dialog_object_info:
        return _label_dialog_object_info['objects']
    return None


class LabelQLineEdit(QtWidgets.QLineEdit):
    """Line edit with list widget navigation support."""

    def setListWidget(self, list_widget):
        self.list_widget = list_widget

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.key() in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Down]:
            self.list_widget.keyPressEvent(a0)
        else:
            super().keyPressEvent(a0)


class LabelDialog(QtWidgets.QDialog):
    """Dialog for entering shape labels."""

    def __init__(
        self,
        text="Enter object label",
        parent=None,
        labels=None,
        sort_labels=True,
        show_text_field=True,
        completion="startswith",
        fit_to_content=None,
        flags=None,
    ):
        if fit_to_content is None:
            fit_to_content = {"row": False, "column": True}
        self._fit_to_content = fit_to_content

        super().__init__(parent)
        
        # Always create both widgets (will choose which one to show in popUp)
        # LineEdit for label input (traditional mode)
        self.edit = LabelQLineEdit()
        self.edit.setPlaceholderText(text)
        self.edit.setValidator(utils.labelValidator())
        self.edit.editingFinished.connect(self.postProcess)
        if flags:
            self.edit.textChanged.connect(self.updateFlags)
        
        # ComboBox for object list mode (will be created when needed)
        self.edit_combo = None
        self._use_object_list = False
        
        # ID fields: group_id, category_id, instance_id
        self.edit_group_id = QtWidgets.QLineEdit()
        self.edit_group_id.setPlaceholderText("Group ID")
        self.edit_group_id.setValidator(
            QtGui.QRegExpValidator(QtCore.QRegExp(r"\d*"), None)
        )
        
        self.edit_category_id = QtWidgets.QLineEdit()
        self.edit_category_id.setPlaceholderText("Category ID")
        self.edit_category_id.setValidator(
            QtGui.QRegExpValidator(QtCore.QRegExp(r"\d*"), None)
        )
        
        self.edit_instance_id = QtWidgets.QLineEdit()
        self.edit_instance_id.setPlaceholderText("Instance ID")
        self.edit_instance_id.setValidator(
            QtGui.QRegExpValidator(QtCore.QRegExp(r"\d*"), None)
        )
        
        layout = QtWidgets.QVBoxLayout()
        if show_text_field:
            # Store the layout for label input (will add widget dynamically in popUp)
            self.layout_edit = QtWidgets.QHBoxLayout()
            self.layout_edit.addWidget(self.edit, 6)
            self.layout_edit.addWidget(self.edit_group_id, 2)
            layout.addLayout(self.layout_edit)
            
            # Add category_id and instance_id row
            layout_ids = QtWidgets.QHBoxLayout()
            layout_ids.addWidget(QtWidgets.QLabel("Cat:"))
            layout_ids.addWidget(self.edit_category_id, 1)
            layout_ids.addWidget(QtWidgets.QLabel("Inst:"))
            layout_ids.addWidget(self.edit_instance_id, 1)
            layout.addLayout(layout_ids)
        # buttons
        self.buttonBox = bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self,
        )
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
        # label_list
        self.labelList = QtWidgets.QListWidget()
        if self._fit_to_content["row"]:
            self.labelList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        if self._fit_to_content["column"]:
            self.labelList.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._sort_labels = sort_labels
        self._initial_labels = labels  # Store initial labels
        if labels:
            self.labelList.addItems(labels)
        if self._sort_labels:
            self.labelList.sortItems()
        else:
            self.labelList.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.labelList.currentItemChanged.connect(self.labelSelected)
        self.labelList.itemDoubleClicked.connect(self.labelDoubleClicked)
        self.labelList.setFixedHeight(150)
        self.edit.setListWidget(self.labelList)
        layout.addWidget(self.labelList)
        # label_flags
        if flags is None:
            flags = {}
        self._flags = flags
        self.flagsLayout = QtWidgets.QVBoxLayout()
        self.resetFlags()
        layout.addItem(self.flagsLayout)
        self.edit.textChanged.connect(self.updateFlags)
        # text edit
        self.editDescription = QtWidgets.QTextEdit()
        self.editDescription.setPlaceholderText("Label description")
        self.editDescription.setFixedHeight(50)
        layout.addWidget(self.editDescription)
        self.setLayout(layout)
        # completion
        completer = QtWidgets.QCompleter()
        if completion == "startswith":
            completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
            # Default settings.
            # completer.setFilterMode(QtCore.Qt.MatchStartsWith)
        elif completion == "contains":
            completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
            completer.setFilterMode(QtCore.Qt.MatchContains)
        else:
            raise ValueError(f"Unsupported completion: {completion}")
        completer.setModel(self.labelList.model())
        self.edit.setCompleter(completer)

    def _on_label_combo_changed(self, display_text: str) -> None:
        """Handle label combo box selection change - auto-fill category and instance ID."""
        if not display_text or not _label_dialog_object_info:
            return
        
        # Parse display text to get label, category_id, and instance_id
        if " [cat:" in display_text and ", inst:" in display_text:
            try:
                label = display_text.split(" [cat:")[0]
                id_part = display_text.split(" [cat:")[1].rstrip("]")
                cat_str, inst_str = id_part.split(", inst:")
                category_id = int(cat_str)
                instance_id = int(inst_str)
                
                # Update ID fields
                self.edit_category_id.setText(str(category_id))
                self.edit_instance_id.setText(str(instance_id))
                
            except (ValueError, IndexError):
                pass
    
    def addLabelHistory(self, label):
        if self.labelList.findItems(label, QtCore.Qt.MatchExactly):
            return
        self.labelList.addItem(label)
        if self._sort_labels:
            self.labelList.sortItems()

    def labelSelected(self, item):
        if self.edit:
            self.edit.setText(item.text())

    def validate(self):
        widget = self.edit_combo if self._use_object_list else self.edit
        if not widget.isEnabled():
            self.accept()
            return

        if self._get_stripped_text():
            self.accept()

    def _get_stripped_text(self) -> str:
        """Get the label text, extracting plain label from formatted display if needed."""
        if self._use_object_list:
            text = self.edit_combo.currentText()
            # Extract plain label from "label [cat:X, inst:Y]" format
            if " [cat:" in text:
                text = text.split(" [cat:")[0]
        else:
            text = self.edit.text()
        
        if hasattr(text, "strip"):
            return str(text.strip())
        if hasattr(text, "trimmed"):
            return str(text.trimmed())
        return str(text)

    def labelDoubleClicked(self, item):
        self.validate()

    def postProcess(self):
        if self.edit:
            self.edit.setText(self._get_stripped_text())

    def updateFlags(self, label_new):
        # keep state of shared flags
        flags_old = self.getFlags()

        flags_new = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label_new):
                for key in keys:
                    flags_new[key] = flags_old.get(key, False)
        self.setFlags(flags_new)

    def deleteFlags(self):
        for i in reversed(range(self.flagsLayout.count())):
            item = self.flagsLayout.itemAt(i).widget()
            self.flagsLayout.removeWidget(item)
            item.setParent(QtWidgets.QWidget())

    def resetFlags(self, label=""):
        flags = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label):
                for key in keys:
                    flags[key] = False
        self.setFlags(flags)

    def setFlags(self, flags):
        self.deleteFlags()
        for key in flags:
            item = QtWidgets.QCheckBox(key, self)
            item.setChecked(flags[key])
            self.flagsLayout.addWidget(item)
            item.show()

    def getFlags(self):
        flags = {}
        for i in range(self.flagsLayout.count()):
            item = self.flagsLayout.itemAt(i).widget()
            item = cast(QtWidgets.QCheckBox, item)
            flags[item.text()] = item.isChecked()
        return flags

    def getGroupId(self):
        group_id = self.edit_group_id.text()
        if group_id:
            return int(group_id)
        return None
    
    def getCategoryId(self):
        """Get category ID from input field."""
        category_id = self.edit_category_id.text()
        if category_id:
            return int(category_id)
        return 0  # Default to 0
    
    def getInstanceId(self):
        """Get instance ID from input field."""
        instance_id = self.edit_instance_id.text()
        if instance_id:
            return int(instance_id)
        return 0  # Default to 0

    def popUp(
        self,
        text=None,
        move=True,
        flags=None,
        group_id=None,
        description=None,
        flags_disabled: bool = False,
        category_id=None,
        instance_id=None,
    ):
        # Check if we have object list NOW (dynamically)
        has_object_list = _label_dialog_object_info is not None
        
        # Switch between ComboBox and LineEdit based on object list availability
        if has_object_list and not self._use_object_list:
            # Need to switch to ComboBox mode
            self._use_object_list = True
            # Create ComboBox if not exists
            if self.edit_combo is None:
                self.edit_combo = QtWidgets.QComboBox()
                self.edit_combo.setEditable(True)
                self.edit_combo.currentTextChanged.connect(self._on_label_combo_changed)
            # Update items
            self.edit_combo.clear()
            self.edit_combo.addItems(_label_dialog_object_info['display_items'])
            self.edit_combo.setCurrentIndex(-1)
            # Switch widgets in layout
            self.layout_edit.removeWidget(self.edit)
            self.edit.hide()
            self.layout_edit.insertWidget(0, self.edit_combo, 6)
            self.edit_combo.show()
            # Update label list with plain label names from object list
            self.labelList.clear()
            plain_labels = [obj['label_name'] for obj in _label_dialog_object_info['objects']]
            self.labelList.addItems(plain_labels)
            if self._sort_labels:
                self.labelList.sortItems()
        elif not has_object_list and self._use_object_list:
            # Need to switch back to LineEdit mode
            self._use_object_list = False
            if self.edit_combo:
                self.layout_edit.removeWidget(self.edit_combo)
                self.edit_combo.hide()
            self.layout_edit.insertWidget(0, self.edit, 6)
            self.edit.show()
            # Restore original label list
            self.labelList.clear()
            if self._initial_labels:
                self.labelList.addItems(self._initial_labels)
            if self._sort_labels:
                self.labelList.sortItems()
        
        if self._fit_to_content["row"]:
            self.labelList.setMinimumHeight(
                self.labelList.sizeHintForRow(0) * self.labelList.count() + 2
            )
        if self._fit_to_content["column"]:
            self.labelList.setMinimumWidth(self.labelList.sizeHintForColumn(0) + 2)
        # if text is None, the previous label in self.edit is kept
        if text is None:
            text = self.edit.text() if not self._use_object_list else ""
        # description is always initialized by empty text c.f., self.edit.text
        if description is None:
            description = ""
        self.editDescription.setPlainText(description)
        if flags:
            self.setFlags(flags)
        else:
            self.resetFlags(text)
        if flags_disabled:
            for i in range(self.flagsLayout.count()):
                self.flagsLayout.itemAt(i).widget().setDisabled(True)
        # Set label text
        if self._use_object_list:
            # Try to find matching item in combo box
            if text and category_id is not None and instance_id is not None:
                # Try to match by full display format
                display_text = f"{text} [cat:{category_id}, inst:{instance_id}]"
                idx = self.edit_combo.findText(display_text)
                if idx >= 0:
                    self.edit_combo.setCurrentIndex(idx)
                else:
                    # Set as plain text (allows custom entry)
                    self.edit_combo.setEditText(text)
            else:
                self.edit_combo.setEditText(text)
        else:
            self.edit.setText(text)
            self.edit.setSelection(0, len(text))
        
        # Set group_id
        if group_id is None:
            self.edit_group_id.clear()
        else:
            self.edit_group_id.setText(str(group_id))
        
        # Set category_id
        if category_id is None:
            self.edit_category_id.clear()
        else:
            self.edit_category_id.setText(str(category_id))
        
        # Set instance_id
        if instance_id is None:
            self.edit_instance_id.clear()
        else:
            self.edit_instance_id.setText(str(instance_id))
        
        # Update label list (only for non-object-list mode)
        if not self._use_object_list:
            items = self.labelList.findItems(text, QtCore.Qt.MatchFixedString)
            if items:
                if len(items) != 1:
                    logger.warning(f"Label list has duplicate '{text}'")
                self.labelList.setCurrentItem(items[0])
                row = self.labelList.row(items[0])
                self.edit.completer().setCurrentRow(row)
        
        # Set focus
        widget = self.edit_combo if self._use_object_list else self.edit
        widget.setFocus(QtCore.Qt.PopupFocusReason)
        
        if move:
            self.move(QtGui.QCursor.pos())
        
        if self.exec_():
            return (
                self._get_stripped_text(),
                self.getFlags(),
                self.getGroupId(),
                self.editDescription.toPlainText(),
                self.getCategoryId(),
                self.getInstanceId(),
            )
        else:
            return None, None, None, None, None, None
