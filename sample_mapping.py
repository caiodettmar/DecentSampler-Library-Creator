"""
Advanced Sample Mapping Interface for DecentSampler Preset Creator

This module provides a comprehensive sample mapping interface with:
- QTableView for precise editing of sample properties
- Visual piano keyboard for intuitive sample assignment
- Auto-mapping feature for extracting root notes from filenames
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QAbstractItemView, QLabel, QPushButton, QGroupBox, QSplitter,
    QMessageBox, QApplication, QSizePolicy, QProgressDialog,
    QComboBox, QSpinBox, QStyledItemDelegate, QCheckBox,
    QDialog, QDialogButtonBox, QLineEdit, QDoubleSpinBox,
    QListWidget, QListWidgetItem, QRadioButton, QButtonGroup,
    QSlider, QTreeWidget, QTreeWidgetItem, QFrame, QStyle
)
from PySide6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, Signal, QMimeData,
    QRectF, QPointF, QSize, QRect, QUrl
)
from PySide6.QtGui import QFont, QPainterPath, QDrag, QPixmap, QPainter, QColor, QBrush, QPen, QDragEnterEvent, QDropEvent

from decent_sampler import DecentPreset, SampleGroup, Sample


class GroupEditDialog(QDialog):
    """Dialog for editing group attributes."""
    
    def __init__(self, group: SampleGroup = None, parent=None):
        super().__init__(parent)
        self.group = group
        self.setWindowTitle("Edit Group" if group else "Create Group")
        self.setModal(True)
        self.resize(400, 300)
        
        self.init_ui()
        
        if group:
            self.load_group_data()
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Group name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Group Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter group name...")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Enabled checkbox
        self.enabled_checkbox = QCheckBox("Enabled")
        self.enabled_checkbox.setChecked(True)
        layout.addWidget(self.enabled_checkbox)
        
        # Volume
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_edit = QLineEdit()
        self.volume_edit.setPlaceholderText("1.0 or 3dB")
        self.volume_edit.setText("1.0")
        volume_layout.addWidget(self.volume_edit)
        layout.addLayout(volume_layout)
        
        # Amp Vel Track
        amp_vel_layout = QHBoxLayout()
        amp_vel_layout.addWidget(QLabel("Velocity Tracking:"))
        self.amp_vel_spinbox = QDoubleSpinBox()
        self.amp_vel_spinbox.setRange(0.0, 1.0)
        self.amp_vel_spinbox.setSingleStep(0.1)
        self.amp_vel_spinbox.setValue(0.0)
        amp_vel_layout.addWidget(self.amp_vel_spinbox)
        layout.addLayout(amp_vel_layout)
        
        # Group Tuning
        tuning_layout = QHBoxLayout()
        tuning_layout.addWidget(QLabel("Group Tuning (semitones):"))
        self.tuning_spinbox = QDoubleSpinBox()
        self.tuning_spinbox.setRange(-12.0, 12.0)
        self.tuning_spinbox.setSingleStep(0.1)
        self.tuning_spinbox.setValue(0.0)
        tuning_layout.addWidget(self.tuning_spinbox)
        layout.addLayout(tuning_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_group_data(self):
        """Load data from the group."""
        if self.group:
            self.name_edit.setText(self.group.name)
            self.enabled_checkbox.setChecked(self.group.enabled)
            self.volume_edit.setText(self.group.volume)
            self.amp_vel_spinbox.setValue(self.group.amp_vel_track)
            self.tuning_spinbox.setValue(self.group.group_tuning)
    
    def get_group_data(self):
        """Get the group data from the dialog."""
        return {
            'name': self.name_edit.text().strip() or "New Group",
            'enabled': self.enabled_checkbox.isChecked(),
            'volume': self.volume_edit.text().strip() or "1.0",
            'amp_vel_track': self.amp_vel_spinbox.value(),
            'group_tuning': self.tuning_spinbox.value()
        }


class SampleGroupModel(QAbstractTableModel):
    """Table model for managing SampleGroup objects with editable properties."""
    
    # Column definitions
    COLUMNS = [
        ("", "selected", True),                 # Checkbox for selection
        ("File", "file_path", False),           # Sample file name
        ("", "play", False),                    # Play button
        ("Group", "group_name", True),          # Group name (editable dropdown)
        ("Root Note", "root_note", True),       # Editable
        ("Low Note", "low_note", True),         # Editable
        ("High Note", "high_note", True),       # Editable
        ("Low Velocity", "low_velocity", True), # Editable
        ("High Velocity", "high_velocity", True), # Editable
        ("Round Robin", "has_round_robin", False) # Round robin indicator (read-only)
    ]
    
    dataChanged = Signal(QModelIndex, QModelIndex, list)
    
    def __init__(self, sample_groups: List[SampleGroup] = None, parent=None):
        super().__init__(parent)
        self.sample_groups = sample_groups or []
        self.samples = []  # Flattened list of all samples
        self.sample_to_group = {}  # Map sample to group
        self._build_sample_list()
    
    def _build_sample_list(self):
        """Build flattened list of samples from groups and ungrouped samples."""
        # Start with ungrouped samples that are already in self.samples
        ungrouped_samples = []
        for sample in self.samples:
            if sample not in self.sample_to_group:
                ungrouped_samples.append(sample)
        
        # Clear and rebuild
        self.samples = []
        self.sample_to_group = {}
        
        # Add samples from groups
        for group in self.sample_groups:
            for sample in group.samples:
                self.samples.append(sample)
                self.sample_to_group[sample] = group
        
        # Add ungrouped samples
        for sample in ungrouped_samples:
            self.samples.append(sample)
            # Don't add to sample_to_group, so it remains ungrouped
    
    def rowCount(self, parent=QModelIndex()):
        """Return the number of rows (samples)."""
        return len(self.samples)
    
    def columnCount(self, parent=QModelIndex()):
        """Return the number of columns."""
        return len(self.COLUMNS)
    
    def data(self, index, role=Qt.DisplayRole):
        """Return data for the given index and role."""
        if not index.isValid() or index.row() >= len(self.samples):
            return None
        
        sample = self.samples[index.row()]
        column_name, attribute, editable = self.COLUMNS[index.column()]
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if attribute == "file_path":
                return sample.file_path.name  # Show only filename
            elif attribute == "group_name":
                # Get group name for this sample
                group = self.sample_to_group.get(sample)
                return group.name if group else "Ungrouped"
            elif attribute in ["root_note", "low_note", "high_note"]:
                # Show note name instead of MIDI number
                return self.get_note_name(getattr(sample, attribute))
            elif attribute == "play":
                return ""  # Play button column doesn't need data
            elif attribute == "has_round_robin":
                # Check if sample is in a round robin group or has individual round robin settings
                group = self.sample_to_group.get(sample)
                if group and hasattr(group, 'seq_mode') and group.seq_mode in ['random', 'true_random', 'round_robin']:
                    return "Yes (Group)"
                else:
                    seq_mode = getattr(sample, 'seq_mode', 'always')
                    return "Yes" if seq_mode in ['random', 'true_random', 'round_robin'] else "No"
            else:
                return getattr(sample, attribute)
        elif role == Qt.TextAlignmentRole:
            if attribute == "file_path":
                return Qt.AlignLeft | Qt.AlignVCenter
            else:
                return Qt.AlignCenter
        elif role == Qt.BackgroundRole:
            # Highlight ungrouped samples in red
            group = self.sample_to_group.get(sample)
            if not group:
                return QColor(255, 200, 200)  # Light red for ungrouped
            elif not editable:
                return QColor(240, 240, 240)  # Light gray for read-only columns
            # Highlight round robin samples
            elif attribute == 'has_round_robin':
                group = self.sample_to_group.get(sample)
                if group and hasattr(group, 'seq_mode') and group.seq_mode in ['random', 'true_random', 'round_robin']:
                    return QColor(255, 240, 200)  # Light orange for round robin group
                elif hasattr(sample, 'seq_mode') and sample.seq_mode in ['random', 'true_random', 'round_robin']:
                    return QColor(255, 240, 200)  # Light orange for individual round robin
        elif role == Qt.ForegroundRole:
            if attribute == "file_path":
                return QColor(0, 0, 0)  # Black text for better readability
            elif attribute == "has_round_robin":
                return QColor(0, 0, 0)  # Black text for better readability
        elif role == Qt.ToolTipRole:
            if attribute == "has_round_robin":
                group = self.sample_to_group.get(sample)
                if group and hasattr(group, 'seq_mode') and group.seq_mode in ['random', 'true_random', 'round_robin']:
                    length = getattr(group, 'seq_length', 0)
                    length_str = str(length) if length > 0 else "Auto"
                    position = getattr(sample, 'seq_position', 1)
                    return f"Round Robin Group: {group.name}\nMode: {group.seq_mode}\nPosition: {position}\nLength: {length_str}\n\nConfigure in Round Robin by Group tab"
                else:
                    seq_mode = getattr(sample, 'seq_mode', 'always')
                    if seq_mode in ['random', 'true_random', 'round_robin']:
                        position = getattr(sample, 'seq_position', 1)
                        length = getattr(sample, 'seq_length', 0)
                        length_str = str(length) if length > 0 else "Auto"
                        return f"Individual Round Robin: {seq_mode}\nPosition: {position}\nLength: {length_str}\n\nConfigure in Round Robin tab or dialog"
                    else:
                        return "No Round Robin\nConfigure in Round Robin tab or dialog"
        
        return None
    
    def setData(self, index, value, role=Qt.EditRole):
        """Set data at the given index."""
        if not index.isValid() or index.row() >= len(self.samples):
            return False
        
        if role != Qt.EditRole:
            return False
        
        sample = self.samples[index.row()]
        column_name, attribute, editable = self.COLUMNS[index.column()]
        
        if not editable:
            return False
        
        # Handle special cases
        if attribute == "selected":
            # Handle checkbox boolean value
            setattr(sample, attribute, bool(value))
            self.dataChanged.emit(index, index, [role])
            return True
        elif attribute == "group_name":
            # Handle group assignment
            group_name = str(value)
            if group_name == "Ungrouped":
                # Remove from current group
                self.remove_sample_from_group(sample)
            else:
                # Find the group by name
                target_group = None
                for group in self.sample_groups:
                    if group.name == group_name:
                        target_group = group
                        break
                
                if target_group:
                    self.add_sample_to_group(sample, target_group)
                else:
                    QMessageBox.warning(None, "Group Not Found", 
                                      f"Group '{group_name}' not found")
                    return False
            
            self.dataChanged.emit(index, index, [role])
            return True
        elif attribute in ["root_note", "low_note", "high_note", "low_velocity", "high_velocity"]:
            if attribute in ["root_note", "low_note", "high_note"]:
                # Convert note name to MIDI number if it's a string
                if isinstance(value, str):
                    numeric_value = self.parse_note_name(value)
                    if numeric_value is None:
                        QMessageBox.warning(None, "Invalid Note Name", 
                                          f"Invalid note name: {value}. Use format like 'C4', 'A#3', etc.")
                        return False
                else:
                    numeric_value = int(value)
            else:
                # Validate numeric values for velocity attributes
                try:
                    numeric_value = int(value)
                except (ValueError, TypeError):
                    QMessageBox.warning(None, "Invalid Value", 
                                      f"Please enter a valid number for {column_name}")
                    return False
            
            # Validate range
            if attribute in ["root_note", "low_note", "high_note", "low_velocity", "high_velocity"]:
                if not (0 <= numeric_value <= 127):
                    QMessageBox.warning(None, "Invalid Value", 
                                      f"Value must be between 0 and 127 for {column_name}")
                    return False
            
            # Set the value
            setattr(sample, attribute, numeric_value)
            self.dataChanged.emit(index, index, [role])
            return True
        
        return False
    
    def add_sample_group(self, sample_group: SampleGroup):
        """Add a new sample group and rebuild sample list."""
        self.sample_groups.append(sample_group)
        self._build_sample_list()
        self.beginResetModel()
        self.endResetModel()
    
    def remove_sample_group(self, sample_group: SampleGroup):
        """Remove a sample group and rebuild sample list."""
        if sample_group in self.sample_groups:
            self.sample_groups.remove(sample_group)
            self._build_sample_list()
            self.beginResetModel()
            self.endResetModel()
    
    def create_group(self, name: str, samples: List[Sample] = None):
        """Create a new group with given samples."""
        group = SampleGroup(name=name, samples=samples or [])
        self.add_sample_group(group)
        return group
    
    def remove_group(self, group: SampleGroup):
        """Remove a group, making its samples ungrouped."""
        self.remove_sample_group(group)
    
    def add_sample_to_group(self, sample: Sample, group: SampleGroup):
        """Add a sample to a group."""
        # Remove from current group if any
        current_group = self.sample_to_group.get(sample)
        if current_group:
            current_group.remove_sample(sample)
        
        # Add to new group
        group.add_sample(sample)
        self.sample_to_group[sample] = group
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount() - 1, self.columnCount() - 1), [])
    
    def remove_sample_from_group(self, sample: Sample):
        """Remove a sample from its group, making it ungrouped."""
        group = self.sample_to_group.get(sample)
        if group:
            group.remove_sample(sample)
            del self.sample_to_group[sample]
            self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount() - 1, self.columnCount() - 1), [])
    
    def get_selected_samples(self) -> List[Sample]:
        """Get all selected samples."""
        return [sample for sample in self.samples if sample.selected]
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return header data for the given section and orientation."""
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.COLUMNS[section][0]
            else:
                return str(section + 1)
        return None
    
    def sort(self, column, order=Qt.AscendingOrder):
        """Sort the model by the given column."""
        if column < 0 or column >= len(self.COLUMNS):
            return
        
        column_name, attribute, editable = self.COLUMNS[column]
        
        # Define sorting key function
        def sort_key(sample):
            if attribute == "file_path":
                return sample.file_path.name.lower()
            elif attribute in ["root_note", "low_note", "high_note"]:
                return getattr(sample, attribute)
            elif attribute == "selected":
                return getattr(sample, attribute)
            elif attribute == "group_name":
                group = self.sample_to_group.get(sample)
                return group.name if group else "Ungrouped"
            else:
                return getattr(sample, attribute, "")
        
        # Sort the samples
        self.beginResetModel()
        self.samples.sort(key=sort_key, reverse=(order == Qt.DescendingOrder))
        self.endResetModel()
    
    def get_note_name(self, note_num: int) -> str:
        """Convert MIDI note number to note name (e.g., 60 -> C4)."""
        # Note names in order starting from C
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Calculate octave and note within octave
        octave = (note_num - 12) // 12
        note_in_octave = (note_num - 12) % 12
        
        # Get note name
        note_name = note_names[note_in_octave]
        
        # Return formatted note name
        return f"{note_name}{octave}"
    
    def parse_note_name(self, note_name: str) -> Optional[int]:
        """Convert note name to MIDI number (e.g., 'C4' -> 60)."""
        import re
        
        # Clean up the input
        note_name = note_name.strip().upper()
        
        # Pattern to match note names like C4, A#3, Bb2, etc.
        pattern = r'^([A-G])([#B]?)(\d+)$'
        match = re.match(pattern, note_name)
        
        if not match:
            return None
        
        note_letter = match.group(1)
        accidental = match.group(2) or ''
        octave = int(match.group(3))
        
        # Map note letters to semitones from C
        note_map = {
            'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11
        }
        
        if note_letter not in note_map:
            return None
        
        # Calculate semitone offset
        semitone = note_map[note_letter]
        
        # Handle accidentals
        if accidental == '#':
            semitone += 1
        elif accidental == 'B':
            semitone -= 1
        
        # Calculate MIDI note number
        midi_note = 12 + (octave * 12) + semitone
        
        # Validate range
        if 0 <= midi_note <= 127:
            return midi_note
        
        return None
    
    def flags(self, index):
        """Return item flags for the given index."""
        if not index.isValid():
            return Qt.NoItemFlags
        
        column_name, attribute, editable = self.COLUMNS[index.column()]
        
        if editable:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def add_sample_group(self, sample_group: SampleGroup):
        """Add a new sample group and rebuild sample list."""
        self.sample_groups.append(sample_group)
        self._build_sample_list()
        self.beginResetModel()
        self.endResetModel()
    
    def remove_sample_group(self, row: int):
        """Remove a sample group from the model."""
        if 0 <= row < len(self.sample_groups):
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.sample_groups[row]
            self.endRemoveRows()
    
    def get_sample_group(self, row: int) -> Optional[SampleGroup]:
        """Get the sample group at the given row."""
        if 0 <= row < len(self.sample_groups):
            return self.sample_groups[row]
        return None
    
    def update_sample_group_range(self, row: int, root_note: int, low_note: int, high_note: int):
        """Update the note range for a sample group."""
        if 0 <= row < len(self.sample_groups):
            sample_group = self.sample_groups[row]
            sample_group.root_note = root_note
            sample_group.low_note = low_note
            sample_group.high_note = high_note
            
            # Emit data changed for the affected columns
            root_index = self.index(row, 1)  # Root note column
            low_index = self.index(row, 2)   # Low note column
            high_index = self.index(row, 3)  # High note column
            
            self.dataChanged.emit(root_index, root_index, [Qt.EditRole])
            self.dataChanged.emit(low_index, low_index, [Qt.EditRole])
            self.dataChanged.emit(high_index, high_index, [Qt.EditRole])


class NoteNameDelegate(QStyledItemDelegate):
    """Delegate for root note column with dropdown."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.note_names = self.generate_note_names()
    
    def generate_note_names(self):
        """Generate list of note names from A0 to C8, sorted by pitch (MIDI number)."""
        note_names = []
        note_letters = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Generate all notes with their MIDI numbers
        notes_with_midi = []
        for octave in range(9):  # 0 to 8
            for note_letter in note_letters:
                note_name = f"{note_letter}{octave}"
                midi_number = self.parse_note_name(note_name)
                if midi_number is not None:
                    notes_with_midi.append((midi_number, note_name))
        
        # Sort by MIDI number (pitch) and return note names
        notes_with_midi.sort(key=lambda x: x[0])
        return [note_name for _, note_name in notes_with_midi]
    
    def createEditor(self, parent, option, index):
        """Create a combo box editor."""
        combo = QComboBox(parent)
        combo.addItems(self.note_names)
        combo.setEditable(True)  # Allow typing
        return combo
    
    def setEditorData(self, editor, index):
        """Set the current value in the editor."""
        value = index.model().data(index, Qt.EditRole)
        if value:
            editor.setCurrentText(str(value))
    
    def setModelData(self, editor, model, index):
        """Set the model data from the editor."""
        text = editor.currentText()
        # Convert note name to MIDI number
        midi_note = self.parse_note_name(text)
        if midi_note is not None:
            model.setData(index, midi_note, Qt.EditRole)
    
    def parse_note_name(self, note_name: str) -> Optional[int]:
        """Convert note name to MIDI number."""
        import re
        
        note_name = note_name.strip().upper()
        pattern = r'^([A-G])([#B]?)(\d+)$'
        match = re.match(pattern, note_name)
        
        if not match:
            return None
        
        note_letter = match.group(1)
        accidental = match.group(2) or ''
        octave = int(match.group(3))
        
        note_map = {
            'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11
        }
        
        if note_letter not in note_map:
            return None
        
        semitone = note_map[note_letter]
        
        if accidental == '#':
            semitone += 1
        elif accidental == 'B':
            semitone -= 1
        
        midi_note = 12 + (octave * 12) + semitone
        
        if 0 <= midi_note <= 127:
            return midi_note
        
        return None


class NumericDelegate(QStyledItemDelegate):
    """Delegate for numeric columns with spinbox."""
    
    def __init__(self, min_val=0, max_val=127, parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
    
    def createEditor(self, parent, option, index):
        """Create a spinbox editor."""
        spinbox = QSpinBox(parent)
        spinbox.setRange(self.min_val, self.max_val)
        spinbox.setButtonSymbols(QSpinBox.PlusMinus)  # Use + and - symbols
        spinbox.setStyleSheet("""
            QSpinBox {
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                padding: 2px;
                background: white;
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: right;
                width: 20px;
                border-left: 1px solid #c0c0c0;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f0f0f0, stop: 1 #d0d0d0);
            }
            QSpinBox::up-button:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e0e0e0, stop: 1 #c0c0c0);
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: left;
                width: 20px;
                border-right: 1px solid #c0c0c0;
                border-top-left-radius: 3px;
                border-bottom-left-radius: 3px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f0f0f0, stop: 1 #d0d0d0);
            }
            QSpinBox::down-button:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e0e0e0, stop: 1 #c0c0c0);
            }
        """)
        return spinbox
    
    def paint(self, painter, option, index):
        """Custom paint method to show spinbox-like appearance."""
        # Get the current value
        value = index.model().data(index, Qt.EditRole)
        if value is None:
            value = 0
        
        # Set up the painter
        painter.save()
        
        # Draw the cell background
        rect = option.rect
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawRect(rect)
        
        # Draw the value text
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawText(rect, Qt.AlignCenter, str(value))
        
        # Draw plus/minus buttons with rounded edges and colors
        button_width = 20
        button_height = rect.height() - 2
        
        # Plus button (right side) - Green color
        plus_rect = QRect(rect.right() - button_width - 1, rect.top() + 1, button_width, button_height)
        painter.setPen(QPen(QColor(34, 139, 34), 1))  # Forest green border
        painter.setBrush(QBrush(QColor(144, 238, 144)))  # Light green background
        painter.drawRoundedRect(plus_rect, 4, 4)  # Rounded rectangle with 4px radius
        
        # Plus symbol - Dark green
        painter.setPen(QPen(QColor(0, 100, 0), 2))  # Dark green symbol
        center_x = plus_rect.center().x()
        center_y = plus_rect.center().y()
        painter.drawLine(center_x - 4, center_y, center_x + 4, center_y)
        painter.drawLine(center_x, center_y - 4, center_x, center_y + 4)
        
        # Minus button (left side) - Red color
        minus_rect = QRect(rect.left() + 1, rect.top() + 1, button_width, button_height)
        painter.setPen(QPen(QColor(220, 20, 60), 1))  # Crimson border
        painter.setBrush(QBrush(QColor(255, 182, 193)))  # Light pink background
        painter.drawRoundedRect(minus_rect, 4, 4)  # Rounded rectangle with 4px radius
        
        # Minus symbol - Dark red
        painter.setPen(QPen(QColor(139, 0, 0), 2))  # Dark red symbol
        center_x = minus_rect.center().x()
        center_y = minus_rect.center().y()
        painter.drawLine(center_x - 4, center_y, center_x + 4, center_y)
        
        painter.restore()
    
    def setEditorData(self, editor, index):
        """Set the current value in the editor."""
        value = index.model().data(index, Qt.EditRole)
        if value is not None:
            editor.setValue(int(value))
    
    def setModelData(self, editor, model, index):
        """Set the model data from the editor."""
        model.setData(index, editor.value(), Qt.EditRole)
    
    def editorEvent(self, event, model, option, index):
        """Handle mouse clicks on plus/minus buttons."""
        if event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                # Get the current value
                value = model.data(index, Qt.EditRole)
                if value is None:
                    value = 0
                else:
                    value = int(value)
                
                # Calculate button areas
                rect = option.rect
                button_width = 20
                button_height = rect.height() - 2
                
                # Plus button (right side)
                plus_rect = QRect(rect.right() - button_width - 1, rect.top() + 1, button_width, button_height)
                # Minus button (left side)
                minus_rect = QRect(rect.left() + 1, rect.top() + 1, button_width, button_height)
                
                # Check which button was clicked
                if plus_rect.contains(event.pos()):
                    # Increment value
                    new_value = min(value + 1, self.max_val)
                    model.setData(index, new_value, Qt.EditRole)
                    return True
                elif minus_rect.contains(event.pos()):
                    # Decrement value
                    new_value = max(value - 1, self.min_val)
                    model.setData(index, new_value, Qt.EditRole)
                    return True
        
        return super().editorEvent(event, model, option, index)


class CheckBoxDelegate(QStyledItemDelegate):
    """Delegate for checkbox column."""
    
    def createEditor(self, parent, option, index):
        """Create a checkbox editor."""
        checkbox = QCheckBox(parent)
        checkbox.setStyleSheet("QCheckBox { margin-left: 50%; margin-right: 50%; }")
        return checkbox
    
    def setEditorData(self, editor, index):
        """Set the current value in the editor."""
        value = index.model().data(index, Qt.EditRole)
        editor.setChecked(bool(value))
    
    def setModelData(self, editor, model, index):
        """Set the model data from the editor."""
        model.setData(index, editor.isChecked(), Qt.EditRole)
    
    def paint(self, painter, option, index):
        """Custom paint method for checkboxes."""
        # Get the checkbox state
        is_checked = bool(index.data(Qt.EditRole))
        
        # Set up the painter
        painter.save()
        
        # Draw a simple checkbox
        rect = option.rect
        checkbox_rect = QRect(rect.x() + (rect.width() - 16) // 2, 
                             rect.y() + (rect.height() - 16) // 2, 
                             16, 16)
        
        # Draw checkbox border
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawRect(checkbox_rect)
        
        # Draw checkmark if checked
        if is_checked:
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            # Simple checkmark
            check_points = [
                QPointF(checkbox_rect.x() + 4, checkbox_rect.y() + 8),
                QPointF(checkbox_rect.x() + 7, checkbox_rect.y() + 11),
                QPointF(checkbox_rect.x() + 12, checkbox_rect.y() + 4)
            ]
            painter.drawPolyline(check_points)
        
        painter.restore()
    
    def editorEvent(self, event, model, option, index):
        """Handle editor events (mouse clicks)."""
        if event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                # Toggle the checkbox state
                current_value = bool(model.data(index, Qt.EditRole))
                new_value = not current_value
                model.setData(index, new_value, Qt.EditRole)
                return True
        return super().editorEvent(event, model, option, index)


class StringDelegate(QStyledItemDelegate):
    """Custom delegate for string input columns."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def createEditor(self, parent, option, index):
        """Create a line edit for string input."""
        from PySide6.QtWidgets import QLineEdit
        editor = QLineEdit(parent)
        return editor
    
    def setEditorData(self, editor, index):
        """Set the editor data from the model."""
        value = index.model().data(index, Qt.EditRole)
        editor.setText(str(value) if value is not None else "")
    
    def setModelData(self, editor, model, index):
        """Set the model data from the editor."""
        model.setData(index, editor.text(), Qt.EditRole)


class GroupDelegate(QStyledItemDelegate):
    """Delegate for group selection using QComboBox."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def createEditor(self, parent, option, index):
        """Create a combo box for group selection."""
        from PySide6.QtWidgets import QComboBox
        editor = QComboBox(parent)
        editor.setEditable(False)
        
        # Add available groups
        model = index.model()
        if hasattr(model, 'sample_groups'):
            editor.addItem("Ungrouped")
            for group in model.sample_groups:
                editor.addItem(group.name)
        
        return editor
    
    def updateEditorGeometry(self, editor, option, index):
        """Update editor geometry."""
        editor.setGeometry(option.rect)
    
    def setEditorData(self, editor, index):
        """Set the editor data from the model."""
        value = index.model().data(index, Qt.EditRole)
        if value:
            # Find the index of the current group name
            current_text = str(value)
            index_found = editor.findText(current_text)
            if index_found >= 0:
                editor.setCurrentIndex(index_found)
            else:
                editor.setCurrentIndex(0)  # Default to "Ungrouped"
        else:
            editor.setCurrentIndex(0)  # Default to "Ungrouped"
    
    def setModelData(self, editor, model, index):
        """Set the model data from the editor."""
        selected_text = editor.currentText()
        model.setData(index, selected_text, Qt.EditRole)




class PlayButtonDelegate(QStyledItemDelegate):
    """Delegate for play button column."""
    
    def __init__(self, parent=None, sample_mapping=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.sample_mapping = sample_mapping
    
    def paint(self, painter, option, index):
        """Custom paint method for play button."""
        # Set up the painter
        painter.save()
        
        # Draw a play button
        rect = option.rect
        button_rect = QRect(rect.x() + 2, rect.y() + 2, rect.width() - 4, rect.height() - 4)
        
        # Check if button is pressed (option.state & QStyle.State_Sunken)
        is_pressed = option.state & QStyle.State_Sunken
        
        if is_pressed:
            # Draw pressed background with darker border
            painter.setPen(QPen(QColor(0, 100, 0), 3))
            painter.setBrush(QBrush(QColor(200, 255, 200)))
            painter.drawRect(button_rect)
            # Draw darker triangle for pressed state
            painter.setPen(QPen(QColor(0, 100, 0), 4))
        else:
            # No background - transparent
            # Draw play triangle in green
            painter.setPen(QPen(QColor(0, 150, 0), 2))
        
        center_x = button_rect.center().x()
        center_y = button_rect.center().y()
        triangle_size = min(button_rect.width(), button_rect.height()) // 3
        
        # Play triangle points
        triangle_points = [
            QPointF(center_x - triangle_size, center_y - triangle_size),
            QPointF(center_x - triangle_size, center_y + triangle_size),
            QPointF(center_x + triangle_size, center_y)
        ]
        painter.drawPolygon(triangle_points)
        
        painter.restore()
    
    def editorEvent(self, event, model, option, index):
        """Handle editor events (mouse clicks)."""
        if event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                # Get the sample for this row from the model
                if self.sample_mapping and hasattr(model, 'samples'):
                    row = index.row()
                    if 0 <= row < len(model.samples):
                        sample = model.samples[row]
                        # Play the sample
                        self.sample_mapping.play_sample_file(sample)
                return True
        return super().editorEvent(event, model, option, index)


class VisualKeyboard(QWidget):
    """Visual piano keyboard widget with drag-drop support and sample highlighting."""
    
    # Piano key layout: white and black keys
    WHITE_KEYS = [0, 2, 4, 5, 7, 9, 11]  # C, D, E, F, G, A, B
    BLACK_KEYS = [1, 3, 6, 8, 10]        # C#, D#, F#, G#, A#
    
    # Key colors
    WHITE_KEY_COLOR = QColor(255, 255, 255)
    BLACK_KEY_COLOR = QColor(0, 0, 0)
    WHITE_KEY_PRESSED = QColor(200, 200, 255)
    BLACK_KEY_PRESSED = QColor(100, 100, 200)
    SAMPLE_ASSIGNED = QColor(255, 200, 100)
    SAMPLE_SELECTED = QColor(100, 255, 100)
    ROUND_ROBIN_ASSIGNED = QColor(255, 150, 50)  # Orange for round robin
    ROUND_ROBIN_SELECTED = QColor(50, 255, 150)  # Light green for selected round robin
    
    sampleDropped = Signal(int, int, int)  # root_note, low_note, high_note
    keyClicked = Signal(int)  # note_number
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFixedHeight(94)  # 25% larger than 75px (75 * 1.25 = 93.75)
        self.setMinimumWidth(1000)  # 25% larger than 800px (800 * 1.25 = 1000)
        
        # Piano key data: note number -> key info
        self.keys = {}
        self.assigned_samples = {}  # note_number -> sample_group
        self.round_robin_samples = {}  # note_number -> round_robin_info
        self.selected_sample_row = -1
        self.pressed_keys = set()  # Track which keys are currently pressed
        
        self.init_keys()
    
    def init_keys(self):
        """Initialize the piano key layout."""
        # Create 88 keys from A0 (21) to C8 (108)
        for note_num in range(21, 109):  # A0 to C8
            octave = (note_num - 12) // 12
            note_in_octave = (note_num - 12) % 12
            
            is_white = note_in_octave in self.WHITE_KEYS
            is_black = note_in_octave in self.BLACK_KEYS
            
            self.keys[note_num] = {
                'note_num': note_num,
                'octave': octave,
                'note_in_octave': note_in_octave,
                'is_white': is_white,
                'is_black': is_black,
                'rect': QRectF(),  # Will be set in paintEvent
                'pressed': False
            }
    
    def get_note_name(self, note_num: int) -> str:
        """Convert MIDI note number to note name (e.g., 60 -> C4)."""
        # Note names in order starting from C
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Calculate octave and note within octave
        octave = (note_num - 12) // 12
        note_in_octave = (note_num - 12) % 12
        
        # Get note name
        note_name = note_names[note_in_octave]
        
        # Return formatted note name
        return f"{note_name}{octave}"
    
    def paintEvent(self, event):
        """Paint the piano keyboard."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        key_height = rect.height()
        
        # Calculate key dimensions
        white_key_width = rect.width() / 52  # 52 white keys in 88-key piano
        black_key_width = white_key_width * 0.6
        black_key_height = key_height * 0.6
        
        # Set up font for note names
        font = painter.font()
        font.setPointSize(5)  # 25% larger than 4pt (4 * 1.25 = 5)
        font.setBold(True)
        painter.setFont(font)
        
        # Draw white keys first
        white_key_index = 0
        for note_num in range(21, 109):
            key_info = self.keys[note_num]
            if key_info['is_white']:
                x = white_key_index * white_key_width
                key_rect = QRectF(x, 0, white_key_width, key_height)
                key_info['rect'] = key_rect
                
                # Choose color based on state
                if note_num in self.round_robin_samples:
                    if note_num in self.pressed_keys:
                        color = self.ROUND_ROBIN_SELECTED
                    else:
                        color = self.ROUND_ROBIN_ASSIGNED
                elif note_num in self.assigned_samples:
                    if note_num in self.pressed_keys:
                        color = self.SAMPLE_SELECTED
                    else:
                        color = self.SAMPLE_ASSIGNED
                elif note_num in self.pressed_keys:
                    color = self.WHITE_KEY_PRESSED
                else:
                    color = self.WHITE_KEY_COLOR
                
                painter.fillRect(key_rect, QBrush(color))
                painter.setPen(QPen(Qt.black, 1))
                painter.drawRect(key_rect)
                
                # Draw note name on white key
                note_name = self.get_note_name(note_num)
                text_rect = QRectF(x + 2, key_height - 20, white_key_width - 4, 18)
                painter.setPen(QPen(Qt.black, 1))
                painter.drawText(text_rect, Qt.AlignCenter, note_name)
                
                white_key_index += 1
        
        # Draw black keys
        for note_num in range(21, 109):
            key_info = self.keys[note_num]
            if key_info['is_black']:
                # Find the white key to the left
                left_white_note = note_num - 1
                while left_white_note >= 21 and not self.keys[left_white_note]['is_white']:
                    left_white_note -= 1
                
                if left_white_note >= 21:
                    left_white_rect = self.keys[left_white_note]['rect']
                    x = left_white_rect.x() + left_white_rect.width() - black_key_width / 2
                    key_rect = QRectF(x, 0, black_key_width, black_key_height)
                    key_info['rect'] = key_rect
                    
                    # Choose color based on state
                    if note_num in self.round_robin_samples:
                        if note_num in self.pressed_keys:
                            color = self.ROUND_ROBIN_SELECTED
                        else:
                            color = self.ROUND_ROBIN_ASSIGNED
                    elif note_num in self.assigned_samples:
                        if note_num in self.pressed_keys:
                            color = self.SAMPLE_SELECTED
                        else:
                            color = self.SAMPLE_ASSIGNED
                    elif note_num in self.pressed_keys:
                        color = self.BLACK_KEY_PRESSED
                    else:
                        color = self.BLACK_KEY_COLOR
                    
                    painter.fillRect(key_rect, QBrush(color))
                    painter.setPen(QPen(Qt.black, 1))
                    painter.drawRect(key_rect)
                    
                    # Draw note name on black key
                    note_name = self.get_note_name(note_num)
                    text_rect = QRectF(x + 1, black_key_height - 15, black_key_width - 2, 14)
                    painter.setPen(QPen(Qt.white, 1))
                    painter.drawText(text_rect, Qt.AlignCenter, note_name)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            note_num = self.get_note_at_position(event.pos())
            if note_num is not None:
                self.pressed_keys.add(note_num)
                self.update()  # Trigger repaint
                self.keyClicked.emit(note_num)
                
                # If there's a sample assigned to this key, highlight it in the table
                if note_num in self.assigned_samples:
                    sample_group = self.assigned_samples[note_num]
                    # Find the row in the table and select it
                    if hasattr(self.parent(), 'table'):
                        table = self.parent().table
                        model = table.model()
                        for row in range(model.rowCount()):
                            if model.sample_groups[row] == sample_group:
                                table.selectRow(row)
                                break
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.LeftButton:
            note_num = self.get_note_at_position(event.pos())
            if note_num is not None and note_num in self.pressed_keys:
                self.pressed_keys.discard(note_num)
                self.update()  # Trigger repaint
    
    def get_note_at_position(self, pos: QPointF) -> Optional[int]:
        """Get the note number at the given position."""
        for note_num, key_info in self.keys.items():
            if key_info['rect'].contains(pos):
                return note_num
        return None
    
    def dragEnterEvent(self, event):
        """Handle drag enter events."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop events."""
        if event.mimeData().hasText():
            note_num = self.get_note_at_position(event.pos())
            if note_num is not None:
                # Emit signal with note range (single note for now)
                self.sampleDropped.emit(note_num, note_num, note_num)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def set_assigned_samples(self, assigned_samples: Dict[int, Any]):
        """Set the assigned samples mapping (note_number -> sample_group)."""
        self.assigned_samples = assigned_samples
        self.update()
    
    def set_round_robin_samples(self, round_robin_samples: Dict[int, Any]):
        """Set the round robin samples mapping (note_number -> round_robin_info)."""
        self.round_robin_samples = round_robin_samples
        self.update()
    
    def set_selected_sample(self, sample_row: int):
        """Set the currently selected sample row."""
        self.selected_sample_row = sample_row
        self.update()
    
    def highlight_sample_range(self, low_note: int, high_note: int, sample_group):
        """Highlight a range of keys for a sample."""
        for note_num in range(low_note, high_note + 1):
            if note_num in self.keys:
                self.assigned_samples[note_num] = sample_group
        self.update()


class SampleMappingWidget(QWidget):
    """Main widget containing the table view and visual keyboard."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sample_groups = []
        self.setAcceptDrops(True)  # Enable drag and drop
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create splitter for table and keyboard
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Create table view
        self.table_view = self.create_table_view()
        splitter.addWidget(self.table_view)
        
        # Create visual keyboard
        self.visual_keyboard = VisualKeyboard()
        splitter.addWidget(self.visual_keyboard)
        
        # Set splitter proportions
        splitter.setSizes([400, 150])
        
        # Connect signals
        self.connect_signals()
    
    def create_table_view(self) -> QWidget:
        """Create the table view widget."""
        group_box = QGroupBox("Sample Groups")
        layout = QVBoxLayout()
        group_box.setLayout(layout)
        
        # Create table view
        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        # Set up model
        self.model = SampleGroupModel(self.sample_groups)
        self.table.setModel(self.model)
        
        # Enable sorting
        self.table.setSortingEnabled(True)
        
        # Set up delegates
        self.table.setItemDelegateForColumn(0, CheckBoxDelegate(self.table))  # Checkbox
        # Column 1 (File) is read-only, no delegate needed
        self.table.setItemDelegateForColumn(2, PlayButtonDelegate(self, self))  # Play button
        self.table.setItemDelegateForColumn(3, GroupDelegate(self.table))  # Group dropdown
        self.table.setItemDelegateForColumn(4, NoteNameDelegate(self.table))  # Root note
        self.table.setItemDelegateForColumn(5, NoteNameDelegate(self.table))  # Low note
        self.table.setItemDelegateForColumn(6, NoteNameDelegate(self.table))  # High note
        self.table.setItemDelegateForColumn(7, NumericDelegate(0, 127, self.table))  # Low velocity
        self.table.setItemDelegateForColumn(8, NumericDelegate(0, 127, self.table))  # High velocity
        # Column 9 (Round Robin) is read-only, no delegate needed
        
        # Configure columns
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)  # Don't stretch last section
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Checkbox column
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # File column - resizable
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Play button column
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Group column
        for i in range(4, self.model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        # Disable horizontal scrolling - panel should resize to fit
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Connect header resize signal to update panel size
        header.sectionResized.connect(self.on_column_resized)
        
        # Set column widths
        self.table.setColumnWidth(0, 30)   # Checkbox
        self.table.setColumnWidth(1, 200)  # File
        self.table.setColumnWidth(2, 50)   # Play button
        self.table.setColumnWidth(3, 100)  # Group
        self.table.setColumnWidth(4, 80)   # Root Note
        self.table.setColumnWidth(5, 80)   # Low Note
        self.table.setColumnWidth(6, 80)   # High Note
        self.table.setColumnWidth(7, 80)   # Low Velocity
        self.table.setColumnWidth(8, 80)   # High Velocity
        self.table.setColumnWidth(9, 100)  # Round Robin indicator
        
        # Top row with Add Sample button on the right
        top_layout = QHBoxLayout()
        top_layout.addStretch()  # Push button to the right
        self.add_sample_btn = QPushButton("➕ Add Sample")
        self.add_sample_btn.clicked.connect(self.add_sample)
        self.add_sample_btn.setMinimumHeight(35)  # Make button shorter
        self.add_sample_btn.setMinimumWidth(200)  # Make button wider
        self.add_sample_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 6px;
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #bbdefb;
            }
            QPushButton:pressed {
                background-color: #90caf9;
            }
        """)
        top_layout.addWidget(self.add_sample_btn)
        layout.addLayout(top_layout)
        
        # Create a container for the table and empty message
        table_container = QWidget()
        table_container_layout = QVBoxLayout()
        table_container_layout.setContentsMargins(0, 0, 0, 0)
        table_container.setLayout(table_container_layout)
        
        # Add the table
        table_container_layout.addWidget(self.table)
        
        # Create empty table message overlay
        self.empty_table_label = QLabel("📁 Drag and drop audio files here to get started\n\nOr click the 'Add Sample' button above")
        self.empty_table_label.setAlignment(Qt.AlignCenter)
        self.empty_table_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #666666;
                background-color: #f5f5f5;
                border: 2px dashed #cccccc;
                border-radius: 10px;
                padding: 40px;
                margin: 20px;
            }
        """)
        self.empty_table_label.hide()  # Initially hidden
        table_container_layout.addWidget(self.empty_table_label)
        
        layout.addWidget(table_container)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        # 1. Select All (with toggle functionality)
        self.select_all_btn = QPushButton("☑️ Select All")
        self.select_all_btn.clicked.connect(self.toggle_select_all)
        button_layout.addWidget(self.select_all_btn)
        
        # 2. Remove Selected
        self.remove_sample_btn = QPushButton("➖ Remove Selected")
        self.remove_sample_btn.clicked.connect(self.remove_selected_sample)
        button_layout.addWidget(self.remove_sample_btn)
        
        # 3. Create Group
        self.create_group_btn = QPushButton("📁 Create Group")
        self.create_group_btn.clicked.connect(self.create_group)
        button_layout.addWidget(self.create_group_btn)
        
        # 4. Edit Group
        self.edit_group_btn = QPushButton("✏️ Edit Group")
        self.edit_group_btn.clicked.connect(self.edit_group)
        button_layout.addWidget(self.edit_group_btn)
        
        # 5. Remove Group
        self.remove_group_btn = QPushButton("🗑️ Remove Group")
        self.remove_group_btn.clicked.connect(self.remove_group)
        button_layout.addWidget(self.remove_group_btn)
        
        # 6. Round Robin
        self.round_robin_btn = QPushButton("🎲 Round Robin")
        self.round_robin_btn.clicked.connect(self.configure_round_robin)
        button_layout.addWidget(self.round_robin_btn)
        
        # Add stretch to push sync button to the right
        button_layout.addStretch()
        
        # Add sync button (icon only, aligned right)
        self.sync_btn = QPushButton("🔄")
        self.sync_btn.setToolTip("Sync with XML Preview")
        self.sync_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 16px;
                padding: 4px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 3px;
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.2);
            }
        """)
        self.sync_btn.clicked.connect(self.force_sync_xml)
        button_layout.addWidget(self.sync_btn)
        layout.addLayout(button_layout)
        
        return group_box
    
    def connect_signals(self):
        """Connect signals between components."""
        # Table selection changes
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        # Keyboard events
        self.visual_keyboard.keyClicked.connect(self.on_key_clicked)
        self.visual_keyboard.sampleDropped.connect(self.on_sample_dropped)
        self.visual_keyboard.keyClicked.connect(self.play_sample)
        
        # Model data changes
        self.model.dataChanged.connect(self.on_data_changed)
        self.model.rowsInserted.connect(self.update_empty_table_message)
        self.model.rowsRemoved.connect(self.update_empty_table_message)
        
        # Initial check for empty table
        self.update_empty_table_message()
    
    def update_empty_table_message(self):
        """Show or hide the empty table message based on whether there are samples."""
        if hasattr(self, 'empty_table_label'):
            if self.model.rowCount() == 0:
                self.empty_table_label.show()
                # Reset Select All button text when no samples
                if hasattr(self, 'select_all_btn'):
                    self.select_all_btn.setText("☑️ Select All")
            else:
                self.empty_table_label.hide()
    
    def add_sample(self):
        """Add a new sample file with auto-mapping."""
        from PySide6.QtWidgets import QFileDialog
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Sample Files",
            "",
            "Audio Files (*.wav *.aif *.aiff *.flac *.mp3);;All Files (*)"
        )
        
        if not file_paths:
            return
        
        # Add samples to the list and auto-group by note
        new_samples = []
        for file_path in file_paths:
            # Create a sample
            sample = Sample(Path(file_path))
            # Add to model (ungrouped initially)
            self.model.samples.append(sample)
            new_samples.append(sample)
        
        # Rebuild the model
        self.model._build_sample_list()
        self.model.beginResetModel()
        self.model.endResetModel()
        
        # Update empty table message
        self.update_empty_table_message()
        
        # Auto-map the new samples with progress dialog
        if new_samples:
            self.auto_map_new_samples_with_progress(new_samples)
            
            # Ask user if they want to group samples by note
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Auto-Group Samples",
                "Would you like to automatically group the samples by their root note?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.auto_group_samples_by_note(new_samples)
        
        self.update_keyboard_display()
    
    def on_column_resized(self, logical_index, old_size, new_size):
        """Handle column resize to update panel size."""
        # Calculate total width needed
        total_width = 0
        for i in range(self.table.model().columnCount()):
            total_width += self.table.columnWidth(i)
        
        # Add some padding for scrollbars and margins
        total_width += 50
        
        # Update the table's minimum width
        self.table.setMinimumWidth(total_width)
    
    def auto_group_samples_by_note(self, samples: List[Sample]):
        """Auto-group samples by their root note."""
        # Group samples by root note
        samples_by_note = {}
        for sample in samples:
            if hasattr(sample, 'root_note') and sample.root_note is not None:
                note_name = self.get_note_name(sample.root_note)
                if note_name not in samples_by_note:
                    samples_by_note[note_name] = []
                samples_by_note[note_name].append(sample)
        
        # Create groups for each note
        for note_name, note_samples in samples_by_note.items():
            # Check if group already exists
            existing_group = None
            for group in self.model.sample_groups:
                if group.name == note_name:
                    existing_group = group
                    break
            
            if existing_group:
                # Add samples to existing group
                for sample in note_samples:
                    self.model.add_sample_to_group(sample, existing_group)
            else:
                # Create new group
                group = self.model.create_group(note_name, note_samples)
        
        # Rebuild the model to reflect changes
        self.model._build_sample_list()
        self.model.beginResetModel()
        self.model.endResetModel()
    
    def auto_map_new_samples_with_progress(self, new_samples: List[Sample]):
        """Auto-map new samples with a progress dialog."""
        if not new_samples:
            return
        
        # Create progress dialog
        progress = QProgressDialog("Auto-mapping new samples...", "Cancel", 0, len(new_samples), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        mapped_count = 0
        for i, sample in enumerate(new_samples):
            # Update progress dialog
            progress.setValue(i)
            progress.setLabelText(f"Mapping: {sample.file_path.name}")
            
            # Check if user cancelled
            if progress.wasCanceled():
                break
            
            # Extract root note from filename
            root_note = self.extract_root_note_from_filename(sample.file_path.name)
            if root_note is not None:
                # Set Low/High notes to Root Note by default
                sample.root_note = root_note
                sample.low_note = root_note
                sample.high_note = root_note
                mapped_count += 1
            
            # Check for round robin patterns
            self.detect_round_robin_pattern(sample)
        
        # Note: Auto-detection of round robin groups is now only available 
        # through the "Round Robin by Group" tab when user clicks "Auto-Detect"
        
        # After all samples are mapped, ask user if they want to extend ranges
        if mapped_count > 0:
            try:
                reply = QMessageBox.question(
                    self, 
                    "Extend Sample Ranges", 
                    f"Found {mapped_count} samples with root notes. Would you like to automatically extend their ranges to fill gaps between samples?\n\nThis will:\n- Fill gaps between the lowest and highest samples\n- Extend ranges intelligently to cover the sample range\n- Keep samples within their natural range",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.extend_sample_ranges_intelligently()
            except Exception as e:
                print(f"Error showing extend ranges dialog: {e}")
                # Skip the extend ranges dialog if there's an error
        
        progress.setValue(len(new_samples))
        progress.close()
        
        # Show completion message
        try:
            if mapped_count > 0:
                QMessageBox.information(self, "Auto-Mapping Complete", 
                                      f"Successfully auto-mapped {mapped_count} out of {len(new_samples)} new samples based on filename patterns.")
            else:
                QMessageBox.information(self, "Auto-Mapping Complete", 
                                      "No new samples could be auto-mapped. Please set note ranges manually.")
        except Exception as e:
            print(f"Error showing completion message: {e}")
            # Fallback to console output
            if mapped_count > 0:
                print(f"Successfully auto-mapped {mapped_count} out of {len(new_samples)} new samples based on filename patterns.")
            else:
                print("No new samples could be auto-mapped. Please set note ranges manually.")
    
    def extend_sample_ranges_intelligently(self):
        """Extend sample ranges intelligently to fill gaps between samples."""
        # Get all samples with valid root notes, sorted by root note
        valid_samples = []
        for sample in self.model.samples:
            if hasattr(sample, 'root_note') and sample.root_note is not None:
                valid_samples.append(sample)
        
        if len(valid_samples) < 1:
            return
        
        # Sort by root note
        valid_samples.sort(key=lambda x: x.root_note)
        
        # Group by root note to handle multiple samples on same note
        samples_by_note = {}
        for sample in valid_samples:
            root_note = sample.root_note
            if root_note not in samples_by_note:
                samples_by_note[root_note] = []
            samples_by_note[root_note].append(sample)
        
        # Get unique root notes sorted
        unique_notes = sorted(samples_by_note.keys())
        
        # Find the lowest and highest root notes
        lowest_note = min(unique_notes)
        highest_note = max(unique_notes)
        
        # Extend ranges to fill gaps only between lowest and highest samples
        for i, root_note in enumerate(unique_notes):
            samples_at_note = samples_by_note[root_note]
            
            # Find the next different root note
            next_note = None
            for j in range(i + 1, len(unique_notes)):
                if unique_notes[j] != root_note:
                    next_note = unique_notes[j]
                    break
            
            # Calculate range for this root note
            if root_note == lowest_note:
                # Lowest sample starts at its root note (not 0)
                low_note = root_note
            else:
                # Start one note above the previous highest note
                prev_note = unique_notes[i - 1]
                prev_samples = samples_by_note[prev_note]
                prev_high = max(sample.high_note for sample in prev_samples)
                low_note = prev_high + 1
            
            if root_note == highest_note:
                # Highest sample ends at its root note (not 127)
                high_note = root_note
            else:
                # End one note below the next root note
                high_note = next_note - 1
            
            # Apply the range to all samples at this root note
            for sample in samples_at_note:
                sample.low_note = low_note
                sample.high_note = high_note
        
        # Update the model for all changed samples
        self.model.beginResetModel()
        self.model.endResetModel()
    
    def toggle_select_all(self):
        """Toggle between selecting all and deselecting all samples."""
        # If no samples, default to "Select All"
        if not self.model.samples:
            self.select_all_btn.setText("☑️ Select All")
            return
        
        # Check if all samples are currently selected
        all_selected = all(sample.selected for sample in self.model.samples)
        
        # Use beginResetModel/endResetModel for better performance
        self.model.beginResetModel()
        for sample in self.model.samples:
            sample.selected = not all_selected
        self.model.endResetModel()
        
        # Update button text
        if all_selected:
            self.select_all_btn.setText("☑️ Select All")
        else:
            self.select_all_btn.setText("☐ Unselect All")
    
    def select_all_samples(self):
        """Select all samples by checking all checkboxes."""
        # Use beginResetModel/endResetModel for better performance
        self.model.beginResetModel()
        for sample in self.model.samples:
            sample.selected = True
        self.model.endResetModel()
        self.select_all_btn.setText("☐ Unselect All")
    
    def remove_selected_sample(self):
        """Remove the selected samples."""
        # Get all selected samples (those with checkbox checked)
        selected_samples = self.model.get_selected_samples()
        
        if not selected_samples:
            QMessageBox.information(self, "No Selection", "Please select samples to remove.")
            return
        
        # Remove samples from their groups first
        for sample in selected_samples:
            self.model.remove_sample_from_group(sample)
        
        # Remove samples from the model
        for sample in selected_samples:
            if sample in self.model.samples:
                self.model.samples.remove(sample)
        
        # Rebuild the model
        self.model._build_sample_list()
        self.model.beginResetModel()
        self.model.endResetModel()
        
        # Update empty table message
        self.update_empty_table_message()
        
        # Clear round robin groups if no samples left
        if len(self.model.samples) == 0 and hasattr(self, 'main_window') and hasattr(self.main_window, 'round_robin_manager'):
            self.main_window.round_robin_manager.clear_groups()
        
        # Update keyboard display
        self.update_keyboard_display()
    
    def auto_map_samples(self):
        """Auto-map samples based on filename patterns."""
        for i, sample in enumerate(self.model.samples):
            root_note = self.extract_root_note_from_filename(sample.file_path.name)
            if root_note is not None:
                # Set a reasonable range around the root note
                low_note = max(0, root_note - 12)
                high_note = min(127, root_note + 12)
                
                sample.root_note = root_note
                sample.low_note = low_note
                sample.high_note = high_note
                
                # Update the model
                index = self.model.index(i, 4)  # Root note column
                self.model.dataChanged.emit(index, index, [])
        
        self.update_keyboard_display()
        QMessageBox.information(self, "Auto-Mapping Complete", 
                              "Samples have been auto-mapped based on filename patterns.")
    
    def extract_root_note_from_filename(self, filename: str) -> Optional[int]:
        """Extract root note from filename using common patterns."""
        # Remove file extension
        name = Path(filename).stem.upper()
        
        # Pattern 1: Note + Octave (e.g., "C4", "A#3", "Bb2")
        patterns = [
            r'([A-G]#?b?)(\d+)',  # C4, A#3, Bb2
            r'([A-G])(\d+)',      # C4, A3
            r'([A-G]#?)(\d+)',    # C#4, A3
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                note_name = match.group(1)
                octave = int(match.group(2))
                
                # Convert note name to MIDI number
                note_map = {
                    'C': 0, 'C#': 1, 'DB': 1, 'D': 2, 'D#': 3, 'EB': 3,
                    'E': 4, 'F': 5, 'F#': 6, 'GB': 6, 'G': 7, 'G#': 8,
                    'AB': 8, 'A': 9, 'A#': 10, 'BB': 10, 'B': 11
                }
                
                if note_name in note_map:
                    midi_note = 12 + (octave * 12) + note_map[note_name]
                    if 21 <= midi_note <= 108:  # Valid piano range
                        return midi_note
        
        # Pattern 2: Kick, Snare, etc. with octave
        drum_patterns = [
            (r'KICK.*?C?(\d+)', 36),  # Kick_C1 -> C1 (36)
            (r'SNARE.*?C?(\d+)', 38), # Snare_C2 -> C2 (38)
            (r'HAT.*?C?(\d+)', 42),   # Hat_C3 -> C3 (42)
        ]
        
        for pattern, base_note in drum_patterns:
            match = re.search(pattern, name)
            if match:
                octave = int(match.group(1))
                midi_note = 12 + (octave * 12) + (base_note % 12)
                if 21 <= midi_note <= 108:
                    return midi_note
        
        return None
    
    def on_selection_changed(self):
        """Handle table selection changes."""
        current_row = self.table.currentIndex().row()
        if current_row >= 0 and current_row < len(self.sample_groups):
            sample_group = self.sample_groups[current_row]
            self.visual_keyboard.set_selected_sample(current_row)
            self.visual_keyboard.highlight_sample_range(
                sample_group.low_note, 
                sample_group.high_note, 
                sample_group
            )
    
    def on_key_clicked(self, note_num: int):
        """Handle keyboard key clicks."""
        current_row = self.table.currentIndex().row()
        if current_row >= 0 and current_row < len(self.sample_groups):
            # Update the selected sample's root note
            self.model.update_sample_group_range(
                current_row, note_num, note_num, note_num
            )
    
    def on_sample_dropped(self, root_note: int, low_note: int, high_note: int):
        """Handle sample drops on the keyboard."""
        current_row = self.table.currentIndex().row()
        if current_row >= 0 and current_row < len(self.sample_groups):
            self.model.update_sample_group_range(
                current_row, root_note, low_note, high_note
            )
    
    def on_data_changed(self, top_left, bottom_right, roles):
        """Handle model data changes."""
        self.update_keyboard_display()
    
    def play_sample(self, note_number):
        """Play the sample associated with the clicked key."""
        if note_number in self.visual_keyboard.assigned_samples:
            sample_group = self.visual_keyboard.assigned_samples[note_number]
            
            # Play the first sample in the group
            if sample_group.samples:
                sample = sample_group.samples[0]
                self.play_sample_file(sample)
            else:
                # Play a default sound for empty groups
                self.play_default_sound(note_number)
        else:
            # Play a default sound for empty keys
            self.play_default_sound(note_number)
    
    def try_qmediaplayer_playback(self, sample):
        """Try to play audio using PySide6 QMediaPlayer."""
        try:
            from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
            from PySide6.QtCore import QUrl
            
            # Create media player if it doesn't exist
            if not hasattr(self, 'media_player'):
                self.media_player = QMediaPlayer()
                self.audio_output = QAudioOutput()
                self.media_player.setAudioOutput(self.audio_output)
            
            # Set the media source
            file_url = QUrl.fromLocalFile(str(sample.file_path.absolute()))
            self.media_player.setSource(file_url)
            
            # Play the audio
            self.media_player.play()
            self.show_status_message(f"Playing: {sample.file_path.name}")
            return True
            
        except ImportError:
            # QMediaPlayer not available
            return False
        except Exception as e:
            print(f"QMediaPlayer error: {e}")
            return False
    
    def try_system_player_playback(self, sample):
        """Try to play audio using system default player."""
        # Try pygame first (better for audio files)
        if self.try_pygame_playback(sample):
            return
            
        # Fall back to system default player
        try:
            import subprocess
            import platform
            
            file_path = str(sample.file_path.absolute())
            
            if platform.system() == "Windows":
                # Use Windows default audio player
                subprocess.Popen(['start', '', file_path], shell=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(['open', file_path])
            else:  # Linux
                subprocess.Popen(['xdg-open', file_path])
                
            # Show a brief status message
            self.show_status_message(f"Playing: {sample.file_path.name}")
            
        except Exception as e:
            QMessageBox.warning(self, "Playback Error", 
                              f"Could not play audio file: {str(e)}")
    
    def try_pygame_playback(self, sample):
        """Try to play audio using pygame."""
        try:
            import pygame
            import threading
            
            # Initialize pygame mixer if not already done
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            def play_audio():
                try:
                    pygame.mixer.music.load(str(sample.file_path.absolute()))
                    pygame.mixer.music.play()
                    self.show_status_message(f"Playing: {sample.file_path.name}")
                except Exception as e:
                    print(f"Pygame playback error: {e}")
            
            # Play in a separate thread to avoid blocking the UI
            thread = threading.Thread(target=play_audio)
            thread.daemon = True
            thread.start()
            return True
            
        except ImportError:
            # Pygame not available
            return False
        except Exception as e:
            print(f"Pygame error: {e}")
            return False
    
    def play_default_sound(self, note_number):
        """Play a default sound for empty keys."""
        try:
            # Generate a simple sine wave tone
            import numpy as np
            import sounddevice as sd
            
            # Calculate frequency from MIDI note number
            frequency = 440 * (2 ** ((note_number - 69) / 12))  # A4 = 440Hz, MIDI 69
            
            # Generate a short sine wave (0.5 seconds)
            duration = 0.5
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            wave = np.sin(2 * np.pi * frequency * t)
            
            # Apply a simple envelope to avoid clicks
            envelope = np.exp(-t * 3)  # Exponential decay
            wave = wave * envelope
            
            # Play the sound
            sd.play(wave, sample_rate)
            self.show_status_message(f"Playing default tone: {self.get_note_name(note_number)} ({frequency:.1f} Hz)")
            
        except ImportError:
            # Fallback: just show a message
            self.show_status_message(f"Empty key clicked: {self.get_note_name(note_number)}")
        except Exception as e:
            print(f"Default sound error: {e}")
            self.show_status_message(f"Empty key clicked: {self.get_note_name(note_number)}")
    
    def play_sample_file(self, sample):
        """Play a sample file directly."""
        # Check if the file exists
        if not sample.file_path.exists():
            QMessageBox.warning(self, "File Not Found", 
                              f"Sample file not found: {sample.file_path}")
            return
        
        # Try PySide6 QMediaPlayer first, then fall back to system player
        if self.try_qmediaplayer_playback(sample):
            return
        
        # Fall back to system default player
        self.try_system_player_playback(sample)
    
    def show_status_message(self, message):
        """Show a brief status message (could be implemented as a status bar)."""
        # For now, just print to console. In a full implementation, 
        # this would show in a status bar or notification
        print(f"Status: {message}")
    
    def force_sync_xml(self):
        """Force sync with XML preview."""
        # Emit a signal to trigger XML update
        if self.model.rowCount() > 0:
            self.model.dataChanged.emit(
                self.model.createIndex(0, 0), 
                self.model.createIndex(self.model.rowCount() - 1, self.model.columnCount() - 1),
                []
            )
    
    def get_note_name(self, note_number):
        """Convert MIDI note number to note name."""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_number // 12) - 1
        note = notes[note_number % 12]
        return f"{note}{octave}"
    
    def update_keyboard_display(self):
        """Update the keyboard display with current sample assignments."""
        assigned_samples = {}
        round_robin_samples = {}
        
        for sample in self.model.samples:
            if hasattr(sample, 'low_note') and hasattr(sample, 'high_note'):
                for note_num in range(sample.low_note, sample.high_note + 1):
                    if 21 <= note_num <= 108:  # Valid piano range
                        # Check if this is a round robin sample
                        if hasattr(sample, 'seq_mode') and sample.seq_mode in ['random', 'true_random', 'round_robin']:
                            round_robin_samples[note_num] = {
                                'sample': sample,
                                'seq_mode': sample.seq_mode,
                                'seq_position': getattr(sample, 'seq_position', 1),
                                'seq_length': getattr(sample, 'seq_length', 0)
                            }
                        else:
                            # Find the group this sample belongs to
                            group = self.model.sample_to_group.get(sample)
                            if group:
                                assigned_samples[note_num] = group
        
        self.visual_keyboard.set_assigned_samples(assigned_samples)
        self.visual_keyboard.set_round_robin_samples(round_robin_samples)
    
    def dragEnterEvent(self, event):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            # Check if any of the URLs are audio files
            for url in event.mimeData().urls():
                file_path = Path(url.toLocalFile())
                if file_path.suffix.lower() in ['.wav', '.aif', '.aiff', '.flac', '.mp3']:
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop events."""
        if event.mimeData().hasUrls():
            # Get audio files from the dropped URLs
            audio_files = []
            for url in event.mimeData().urls():
                file_path = Path(url.toLocalFile())
                if file_path.suffix.lower() in ['.wav', '.aif', '.aiff', '.flac', '.mp3']:
                    audio_files.append(file_path)
            
            if audio_files:
                # Add the files as samples
                new_samples = []
                for file_path in audio_files:
                    # Create a sample
                    sample = Sample(file_path)
                    self.model.samples.append(sample)
                    new_samples.append(sample)
                
                # Rebuild the model
                self.model._build_sample_list()
                self.model.beginResetModel()
                self.model.endResetModel()
                
                # Update empty table message
                self.update_empty_table_message()
                
                # Auto-map the new samples
                if new_samples:
                    self.auto_map_new_samples_with_progress(new_samples)
                
                self.update_keyboard_display()
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def get_sample_groups(self) -> List[SampleGroup]:
        """Get the current list of sample groups in the order they appear in the table."""
        # Get regular sample groups from the model
        if hasattr(self, 'model') and self.model:
            groups = self.model.sample_groups.copy()
        else:
            groups = self.sample_groups.copy()
        
        # Add round robin groups as proper SampleGroup objects
        if hasattr(self, 'main_window') and hasattr(self.main_window, 'round_robin_manager'):
            for group_name, group_data in self.main_window.round_robin_manager.get_round_robin_groups().items():
                # Create a SampleGroup for this round robin group
                rr_group = SampleGroup(
                    name=group_name,
                    enabled=True,
                    volume="1.0",
                    seq_mode=group_data['seq_mode'],
                    seq_length=group_data['seq_length'],
                    samples=group_data['samples']
                )
                groups.append(rr_group)
        
        return groups
    
    def create_group(self):
        """Create a new group with selected samples."""
        selected_samples = self.model.get_selected_samples()
        
        # Show dialog to create group
        dialog = GroupEditDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            group_data = dialog.get_group_data()
            group = self.model.create_group(group_data['name'])
            
            # Set group attributes
            group.enabled = group_data['enabled']
            group.volume = group_data['volume']
            group.amp_vel_track = group_data['amp_vel_track']
            group.group_tuning = group_data['group_tuning']
            
            # Add selected samples to the group
            for sample in selected_samples:
                self.model.add_sample_to_group(sample, group)
            
            # Clear selection
            for sample in self.model.samples:
                sample.selected = False
            self.model.dataChanged.emit(self.model.createIndex(0, 0), self.model.createIndex(self.model.rowCount() - 1, self.model.columnCount() - 1), [])
    
    def edit_group(self):
        """Edit the group of selected samples."""
        selected_samples = self.model.get_selected_samples()
        if not selected_samples:
            QMessageBox.information(self, "No Selection", "Please select samples to edit their group.")
            return
        
        # Get the group of the first selected sample
        group = self.model.sample_to_group.get(selected_samples[0])
        if not group:
            QMessageBox.information(self, "No Group", "Selected samples are not in a group.")
            return
        
        # Show dialog to edit group
        dialog = GroupEditDialog(group, parent=self)
        if dialog.exec() == QDialog.Accepted:
            group_data = dialog.get_group_data()
            
            # Update group attributes
            group.name = group_data['name']
            group.enabled = group_data['enabled']
            group.volume = group_data['volume']
            group.amp_vel_track = group_data['amp_vel_track']
            group.group_tuning = group_data['group_tuning']
            
            # Refresh the display
            self.model.dataChanged.emit(self.model.createIndex(0, 0), self.model.createIndex(self.model.rowCount() - 1, self.model.columnCount() - 1), [])
    
    def remove_group(self):
        """Remove the group of selected samples."""
        selected_samples = self.model.get_selected_samples()
        if not selected_samples:
            QMessageBox.information(self, "No Selection", "Please select samples to remove from their group.")
            return
        
        # Get the group of the first selected sample
        group = self.model.sample_to_group.get(selected_samples[0])
        if not group:
            QMessageBox.information(self, "No Group", "Selected samples are not in a group.")
            return
        
        # Confirm removal
        reply = QMessageBox.question(
            self, 
            "Remove Group", 
            f"Are you sure you want to remove the group '{group.name}'?\n\nThis will make all samples in the group ungrouped (shown in red).",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.model.remove_group(group)
            # Clear selection
            for sample in self.model.samples:
                sample.selected = False
            self.model.dataChanged.emit(self.model.createIndex(0, 0), self.model.createIndex(self.model.rowCount() - 1, self.model.columnCount() - 1), [])
    
    def set_sample_groups(self, sample_groups: List[SampleGroup]):
        """Set the list of sample groups with auto-mapping."""
        self.sample_groups = sample_groups
        self.model = SampleGroupModel(sample_groups)
        self.table.setModel(self.model)
        self.connect_signals()
        
        # Auto-map samples with progress dialog
        if sample_groups:
            self.auto_map_samples_with_progress()
        
        self.update_keyboard_display()
    
    def auto_map_samples_with_progress(self):
        """Auto-map samples with a progress dialog."""
        if not self.model.samples:
            return
        
        # Create progress dialog
        progress = QProgressDialog("Auto-mapping samples...", "Cancel", 0, len(self.model.samples), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        mapped_count = 0
        for i, sample in enumerate(self.model.samples):
            # Update progress dialog
            progress.setValue(i)
            progress.setLabelText(f"Mapping: {sample.file_path.name}")
            
            # Check if user cancelled
            if progress.wasCanceled():
                break
            
            # Extract root note from filename
            root_note = self.extract_root_note_from_filename(sample.file_path.name)
            if root_note is not None:
                # Set a reasonable range around the root note
                low_note = max(0, root_note - 12)
                high_note = min(127, root_note + 12)
                
                # Update the sample
                sample.root_note = root_note
                sample.low_note = low_note
                sample.high_note = high_note
                mapped_count += 1
        
        progress.setValue(len(self.model.samples))
        progress.close()
        
        # Show completion message
        if mapped_count > 0:
            QMessageBox.information(self, "Auto-Mapping Complete", 
                                  f"Successfully auto-mapped {mapped_count} out of {len(self.model.samples)} samples based on filename patterns.")
        else:
            QMessageBox.information(self, "Auto-Mapping Complete", 
                                  "No samples could be auto-mapped. Please set note ranges manually.")
    
    def configure_round_robin(self):
        """Configure round robin for selected samples."""
        # Get selected samples using the model's method
        selected_samples = self.model.get_selected_samples()
        
        if not selected_samples:
            QMessageBox.warning(self, "No Selection", "Please select samples to configure round robin.")
            return
        
        # Show round robin dialog with all available samples
        dialog = RoundRobinDialog(samples=selected_samples, sample_mapping=self, parent=self)
        if dialog.exec() == QDialog.Accepted:
            settings = dialog.get_settings()
            
            # Apply settings to selected samples
            for sample in settings['samples']:
                sample.seq_mode = settings['seq_mode']
                sample.seq_length = settings['seq_length']
            
            # Update the model
            self.model.beginResetModel()
            self.model.endResetModel()
            
            # Update keyboard display
            self.update_keyboard_display()
            
            # Trigger XML update
            if hasattr(self.parent(), 'update_xml_live'):
                self.parent().update_xml_live()
    
    def detect_round_robin_pattern(self, sample: Sample):
        """Detect round robin patterns in filename and set appropriate attributes."""
        filename = sample.file_path.stem.lower()  # Get filename without extension
        
        # Common round robin patterns
        patterns = [
            r'_rr(\d+)$',      # _rr1, _rr2, etc.
            r'_(\d+)$',        # _1, _2, etc.
            r'_round(\d+)$',   # _round1, _round2, etc.
            r'_alt(\d+)$',     # _alt1, _alt2, etc.
            r'_var(\d+)$',     # _var1, _var2, etc.
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    position = int(match.group(1))
                    sample.seq_mode = "round_robin"
                    sample.seq_position = position
                    # Don't set seq_length here - let the user configure it
                    break
                except ValueError:
                    continue


class RoundRobinDialog(QDialog):
    """Dialog for configuring round robin settings."""
    
    def __init__(self, samples: List[Sample] = None, parent=None, sample_mapping=None):
        super().__init__(parent)
        self.samples = samples or []
        self.sample_mapping = sample_mapping
        self.selected_samples = self.samples.copy()  # Start with provided samples
        self.setWindowTitle("Configure Round Robin")
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
        self.load_existing_settings()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Create main layout
        main_layout = QVBoxLayout()
        
        # 1. Group Name
        name_group = QGroupBox("Group Name")
        name_layout = QVBoxLayout()
        self.group_name_edit = QLineEdit()
        self.group_name_edit.setPlaceholderText("Enter group name (e.g., C4_RoundRobin)")
        self.group_name_edit.setToolTip("Name for this round robin group")
        name_layout.addWidget(self.group_name_edit)
        name_group.setLayout(name_layout)
        main_layout.addWidget(name_group)
        
        # 2. Sequence Length
        length_group = QGroupBox("Sequence Length")
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("Length:"))
        self.length_spin = QSpinBox()
        self.length_spin.setRange(0, 127)
        self.length_spin.setValue(0)
        self.length_spin.setSpecialValueText("Auto-detect")
        self.length_spin.setToolTip("Number of samples in the round robin sequence. Set to 0 for auto-detection.")
        length_layout.addWidget(self.length_spin)
        length_layout.addStretch()
        length_group.setLayout(length_layout)
        main_layout.addWidget(length_group)
        
        # 3. Round Robin Mode
        mode_group = QGroupBox("Round Robin Mode")
        mode_layout = QVBoxLayout()
        
        self.mode_buttons = QButtonGroup()
        self.always_radio = QRadioButton("Always (default) - No round robin")
        self.random_radio = QRadioButton("Random - Random selection from samples")
        self.true_random_radio = QRadioButton("True Random - Completely random selection")
        self.round_robin_radio = QRadioButton("Round Robin - Sequential selection")
        
        self.mode_buttons.addButton(self.always_radio, 0)
        self.mode_buttons.addButton(self.random_radio, 1)
        self.mode_buttons.addButton(self.true_random_radio, 2)
        self.mode_buttons.addButton(self.round_robin_radio, 3)
        
        self.always_radio.setChecked(True)
        
        mode_layout.addWidget(self.always_radio)
        mode_layout.addWidget(self.random_radio)
        mode_layout.addWidget(self.true_random_radio)
        mode_layout.addWidget(self.round_robin_radio)
        mode_group.setLayout(mode_layout)
        main_layout.addWidget(mode_group)
        
        # Create splitter for sample browser
        splitter = QSplitter(Qt.Horizontal)
        
        # 4. Available Samples
        available_group = QGroupBox("Available Samples")
        available_layout = QVBoxLayout()
        
        # Sample list
        self.available_samples_list = QListWidget()
        self.available_samples_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        available_layout.addWidget(self.available_samples_list)
        
        # Add/Remove buttons
        sample_buttons_layout = QHBoxLayout()
        self.add_sample_btn = QPushButton("➕ Add Selected")
        self.add_sample_btn.clicked.connect(self.add_selected_samples)
        self.add_sample_btn.setStyleSheet("""
            QPushButton {
                border-radius: 15px;
                padding: 8px 16px;
                font-weight: bold;
                background-color: #e8f5e8;
                border: 2px solid #4caf50;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #c8e6c9;
                color: #ffffff;
                border: 3px solid #388e3c;
                font-size: 13px;
            }
            QPushButton:pressed {
                background-color: #a5d6a7;
                color: #ffffff;
                border: 3px solid #2e7d32;
            }
        """)
        
        self.remove_sample_btn = QPushButton("➖ Remove Selected")
        self.remove_sample_btn.clicked.connect(self.remove_selected_samples)
        self.remove_sample_btn.setStyleSheet("""
            QPushButton {
                border-radius: 15px;
                padding: 8px 16px;
                font-weight: bold;
                background-color: #ffebee;
                border: 2px solid #f44336;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #ffcdd2;
                color: #ffffff;
                border: 3px solid #d32f2f;
                font-size: 13px;
            }
            QPushButton:pressed {
                background-color: #ef9a9a;
                color: #ffffff;
                border: 3px solid #c62828;
            }
        """)
        
        sample_buttons_layout.addWidget(self.add_sample_btn)
        sample_buttons_layout.addWidget(self.remove_sample_btn)
        sample_buttons_layout.addStretch()
        
        available_layout.addLayout(sample_buttons_layout)
        available_group.setLayout(available_layout)
        splitter.addWidget(available_group)
        
        # 5. Selected Samples for Round Robin
        selected_group = QGroupBox("Selected Samples for Round Robin")
        selected_layout = QVBoxLayout()
        
        # Selected samples list
        self.selected_samples_list = QListWidget()
        self.selected_samples_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        selected_layout.addWidget(self.selected_samples_list)
        
        # Position controls for selected samples
        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel("Position:"))
        self.position_spin = QSpinBox()
        self.position_spin.setRange(1, 127)
        self.position_spin.setValue(1)
        self.position_spin.setToolTip("Position in the round robin sequence")
        position_layout.addWidget(self.position_spin)
        position_layout.addStretch()
        selected_layout.addLayout(position_layout)
        
        selected_group.setLayout(selected_layout)
        splitter.addWidget(selected_group)
        
        # Set splitter proportions (50% each)
        splitter.setSizes([400, 400])
        main_layout.addWidget(splitter)
        
        layout.addLayout(main_layout)
        
        # Old sample controls removed - using new browser interface
        
        # Old sample controls removed - using new browser interface
        
        # Position assignment removed - using automatic positioning in new interface
        
        # Preview section removed - using new interface
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # Load available samples
        self.load_available_samples()
        self.update_selected_samples_list()
    
    def showEvent(self, event):
        """Refresh available samples when dialog is shown."""
        super().showEvent(event)
        self.load_available_samples()
        self.update_selected_samples_list()
    
    def load_available_samples(self):
        """Load all available samples from the sample mapping."""
        self.available_samples_list.clear()
        
        if self.sample_mapping and hasattr(self.sample_mapping, 'model'):
            # Get all samples directly from the model's samples list
            samples = self.sample_mapping.model.samples
            for sample in samples:
                if sample:
                    # Create item with sample info
                    item_text = f"{sample.file_path.name} (Note: {sample.root_note})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, sample)
                    self.available_samples_list.addItem(item)
    
    def add_selected_samples(self):
        """Add selected samples from available list to round robin group."""
        selected_items = self.available_samples_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select samples to add.")
            return
        
        for item in selected_items:
            sample = item.data(Qt.UserRole)
            if sample not in self.selected_samples:
                self.selected_samples.append(sample)
        
        self.update_selected_samples_list()
        self.update_available_samples_list()
    
    def remove_selected_samples(self):
        """Remove selected samples from round robin group."""
        selected_items = self.selected_samples_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select samples to remove.")
            return
        
        for item in selected_items:
            sample = item.data(Qt.UserRole)
            if sample in self.selected_samples:
                self.selected_samples.remove(sample)
        
        self.update_selected_samples_list()
        self.update_available_samples_list()
    
    def update_selected_samples_list(self):
        """Update the selected samples list display."""
        self.selected_samples_list.clear()
        
        for i, sample in enumerate(self.selected_samples):
            item_text = f"{sample.file_path.name} (Note: {sample.root_note}, Pos: {i+1})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, sample)
            self.selected_samples_list.addItem(item)
    
    def update_available_samples_list(self):
        """Update the available samples list to exclude already selected ones."""
        self.available_samples_list.clear()
        
        if self.sample_mapping and hasattr(self.sample_mapping, 'model'):
            # Get all samples directly from the model's samples list
            for sample in self.sample_mapping.model.samples:
                if sample and sample not in self.selected_samples:
                    # Create item with sample info
                    item_text = f"{sample.file_path.name} (Note: {sample.root_note})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, sample)
                    self.available_samples_list.addItem(item)
    
    def load_existing_settings(self):
        """Load existing round robin settings from samples."""
        if not self.samples:
            return
        
        # Add existing samples to selected_samples
        self.selected_samples = self.samples.copy()
        
        # Check if samples already have round robin settings
        first_sample = self.samples[0]
        if hasattr(first_sample, 'seq_mode') and first_sample.seq_mode != "always":
            mode_map = {"always": 0, "random": 1, "true_random": 2, "round_robin": 3}
            if first_sample.seq_mode in mode_map:
                self.mode_buttons.button(mode_map[first_sample.seq_mode]).setChecked(True)
        
        if hasattr(first_sample, 'seq_length'):
            self.length_spin.setValue(first_sample.seq_length)
        
        # Set group name if samples are in a group
        if hasattr(self.sample_mapping, 'model') and hasattr(self.sample_mapping.model, 'sample_to_group'):
            group = self.sample_mapping.model.sample_to_group.get(first_sample)
            if group and hasattr(group, 'name'):
                self.group_name_edit.setText(group.name)
        
        # Update the UI lists
        self.update_selected_samples_list()
        self.update_available_samples_list()
    
    # Old method removed - using new browser interface
    
    # Old method removed - using new browser interface
    
    # Old method removed - using new browser interface
    
    # Old method removed - using new browser interface
    
    # Old method removed - using new browser interface
    
    # Old method removed - using new browser interface
    
    # Old method removed - using new browser interface
    
    def get_settings(self):
        """Get the configured round robin settings."""
        # Get mode
        mode_map = {0: "always", 1: "random", 2: "true_random", 3: "round_robin"}
        seq_mode = mode_map[self.mode_buttons.checkedId()]
        
        # Get sequence length
        seq_length = self.length_spin.value()
        
        # Get samples with positions from selected_samples
        samples_with_positions = []
        for i, sample in enumerate(self.selected_samples):
            sample.seq_position = i + 1  # Auto-assign positions based on order
            sample.seq_mode = seq_mode
            sample.seq_length = seq_length
            samples_with_positions.append(sample)
        
        # Get group name
        group_name = self.group_name_edit.text().strip()
        if not group_name:
            # Generate default name from first sample
            if self.selected_samples:
                first_sample = self.selected_samples[0]
                group_name = f"RR_{first_sample.file_path.stem}"
            else:
                group_name = "RR_Group"
        
        return {
            'group_name': group_name,
            'seq_mode': seq_mode,
            'seq_length': seq_length,
            'samples': samples_with_positions
        }


class MultiGroupEditDialog(QDialog):
    """Dialog for editing multiple round robin groups - mode and length only."""
    
    def __init__(self, group_names: List[str], parent=None):
        super().__init__(parent)
        self.group_names = group_names
        self.setWindowTitle(f"Edit {len(group_names)} Groups")
        self.setModal(True)
        self.resize(400, 200)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(f"Edit Round Robin Settings for {len(self.group_names)} Groups")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # Group list
        groups_label = QLabel("Selected Groups:")
        layout.addWidget(groups_label)
        
        groups_list = QListWidget()
        groups_list.addItems(self.group_names)
        groups_list.setMaximumHeight(80)
        groups_list.setEnabled(False)  # Read-only
        layout.addWidget(groups_list)
        
        # Mode selection
        mode_group = QGroupBox("Round Robin Mode")
        mode_layout = QVBoxLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["always", "round_robin", "random", "true_random"])
        self.mode_combo.setCurrentText("round_robin")
        mode_layout.addWidget(self.mode_combo)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Length setting
        length_group = QGroupBox("Round Robin Length")
        length_layout = QVBoxLayout()
        
        length_layout.addWidget(QLabel("Length (0 = Auto-detect):"))
        self.length_edit = QSpinBox()
        self.length_edit.setRange(0, 100)
        self.length_edit.setValue(0)
        self.length_edit.setSpecialValueText("Auto")
        length_layout.addWidget(self.length_edit)
        
        length_group.setLayout(length_layout)
        layout.addWidget(length_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_settings(self):
        """Get the current settings."""
        return {
            'seq_mode': self.mode_combo.currentText(),
            'seq_length': self.length_edit.value()
        }


class RoundRobinManager(QWidget):
    """Widget for managing round robin groups."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.round_robin_groups = {}  # Dict mapping group names to sample lists
        self.sample_mapping = parent
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the round robin manager UI."""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Round Robin Groups"))
        self.add_group_btn = QPushButton("➕ Add Group")
        self.add_group_btn.clicked.connect(self.add_group)
        self.add_group_btn.setMinimumHeight(35)  # Make button shorter
        self.add_group_btn.setMinimumWidth(200)  # Make button wider
        self.add_group_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 6px;
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #bbdefb;
                border: 3px solid #1976d2;
            }
            QPushButton:pressed {
                background-color: #90caf9;
                border: 3px solid #1565c0;
            }
        """)
        header_layout.addWidget(self.add_group_btn)
        layout.addLayout(header_layout)
        
        # Groups tree widget
        self.groups_tree = QTreeWidget()
        self.groups_tree.setHeaderLabels(["Group Name", "Mode", "Samples", "Length", "Details"])
        self.groups_tree.setAlternatingRowColors(True)
        self.groups_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.groups_tree)
        
        # Group controls
        controls_layout = QHBoxLayout()
        self.edit_group_btn = QPushButton("✏️ Edit Group")
        self.remove_group_btn = QPushButton("🗑️ Remove Group")
        self.preview_btn = QPushButton("🎵 Preview")
        self.auto_detect_btn = QPushButton("🔍 Auto-Detect")
        self.select_all_btn = QPushButton("☑️ Select All")
        
        self.edit_group_btn.clicked.connect(self.edit_group)
        self.remove_group_btn.clicked.connect(self.remove_group)
        self.preview_btn.clicked.connect(self.preview_group)
        self.auto_detect_btn.clicked.connect(self.auto_detect_groups)
        self.select_all_btn.clicked.connect(self.select_all_groups)
        
        # Initialize preview thread reference
        self.current_preview_thread = None
        
        controls_layout.addWidget(self.select_all_btn)
        controls_layout.addWidget(self.edit_group_btn)
        controls_layout.addWidget(self.remove_group_btn)
        controls_layout.addWidget(self.preview_btn)
        controls_layout.addWidget(self.auto_detect_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        self.setLayout(layout)
    
    def add_group(self):
        """Add a new round robin group."""
        if not hasattr(self.sample_mapping, 'model'):
            QMessageBox.warning(self, "No Samples", "No samples available to create a group.")
            return
        
        # Check if there are any samples available
        sample_count = self.sample_mapping.model.rowCount()
        if sample_count == 0:
            QMessageBox.warning(self, "No Samples", "No samples available to create a group.")
            return
        
        # Show round robin dialog without pre-selected samples
        dialog = RoundRobinDialog(sample_mapping=self.sample_mapping, parent=self)
        if dialog.exec() == QDialog.Accepted:
            settings = dialog.get_settings()
            
            # Check if any samples were selected
            if not settings['samples']:
                QMessageBox.information(self, "No Samples Selected", "Please select at least one sample for the round robin group.")
                return
            
            # Check if samples are already in a group
            first_sample = settings['samples'][0]
            existing_group = None
            
            # Check if all samples belong to the same group
            if hasattr(self.sample_mapping, 'model') and hasattr(self.sample_mapping.model, 'sample_to_group'):
                groups = set()
                for sample in settings['samples']:
                    group = self.sample_mapping.model.sample_to_group.get(sample)
                    if group:
                        groups.add(group)
                
                # If all samples are in the same group, use that group
                if len(groups) == 1:
                    existing_group = list(groups)[0]
            
            if existing_group:
                # Overwrite existing group with round robin settings
                group_name = existing_group.name
                # Update the existing group's round robin settings
                existing_group.seq_mode = settings['seq_mode']
                existing_group.seq_length = settings['seq_length']
                
                # Store in round robin groups for tracking
                self.round_robin_groups[group_name] = {
                    'samples': settings['samples'],
                    'seq_mode': settings['seq_mode'],
                    'seq_length': settings['seq_length']
                }
            else:
                # Use group name from dialog
                group_name = settings['group_name']
                
                # Create a new SampleGroup in the model
                if hasattr(self.sample_mapping, 'model'):
                    new_group = SampleGroup(
                        name=group_name,
                        enabled=True,
                        volume="1.0",
                        seq_mode=settings['seq_mode'],
                        seq_length=settings['seq_length'],
                        samples=settings['samples']
                    )
                    
                    # Add the group to the model
                    self.sample_mapping.model.add_sample_group(new_group)
                    
                    # Move samples to the new group
                    for sample in settings['samples']:
                        self.sample_mapping.model.add_sample_to_group(sample, new_group)
                
                # Store in round robin groups for tracking
                self.round_robin_groups[group_name] = {
                    'samples': settings['samples'],
                    'seq_mode': settings['seq_mode'],
                    'seq_length': settings['seq_length']
                }
            
            # Reset individual sample round robin settings since they're handled at group level
            for sample in settings['samples']:
                sample.seq_mode = "always"  # Reset to default since group handles round robin
                sample.seq_length = 0       # Reset to default since group handles round robin
                # seq_position is still set for ordering within the group
            
            # Update the tree
            self.update_groups_tree()
            
            # Trigger XML update
            if hasattr(self.sample_mapping, 'force_sync_xml'):
                self.sample_mapping.force_sync_xml()
    
    def clear_groups(self):
        """Clear all round robin groups when there are no samples."""
        self.round_robin_groups.clear()
        self.update_groups_tree()
        
        # Reset all samples' group associations
        if hasattr(self.sample_mapping, 'model') and hasattr(self.sample_mapping.model, 'sample_to_group'):
            self.sample_mapping.model.sample_to_group.clear()
        
        # Trigger XML update
        if hasattr(self.sample_mapping, 'force_sync_xml'):
            self.sample_mapping.force_sync_xml()
    
    def edit_group(self):
        """Edit the selected round robin group(s)."""
        selected_items = self.groups_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a group to edit.")
            return
        
        if len(selected_items) == 1:
            # Single group edit - show full round robin dialog
            self.edit_single_group(selected_items[0])
        else:
            # Multiple groups selected - show simplified dialog for mode and length only
            self.edit_multiple_groups(selected_items)
    
    def edit_single_group(self, item):
        """Edit a single round robin group."""
        group_name = item.text(0)
        if group_name in self.round_robin_groups:
            group_data = self.round_robin_groups[group_name]
            samples = group_data['samples']
            
            # Show round robin dialog with existing samples
            dialog = RoundRobinDialog(samples=samples, sample_mapping=self.sample_mapping, parent=self)
            if dialog.exec() == QDialog.Accepted:
                settings = dialog.get_settings()
                
                # Check if group name changed
                new_group_name = settings['group_name']
                if new_group_name != group_name:
                    # Remove old group and create new one
                    if group_name in self.round_robin_groups:
                        del self.round_robin_groups[group_name]
                    
                    # Update group name in the model if it exists
                    if hasattr(self.sample_mapping, 'model') and hasattr(self.sample_mapping.model, 'sample_to_group'):
                        for sample in settings['samples']:
                            group = self.sample_mapping.model.sample_to_group.get(sample)
                            if group and group.name == group_name:
                                group.name = new_group_name
                                group.seq_mode = settings['seq_mode']
                                group.seq_length = settings['seq_length']
                                break
                
                # Update the group
                self.round_robin_groups[new_group_name] = {
                    'samples': settings['samples'],
                    'seq_mode': settings['seq_mode'],
                    'seq_length': settings['seq_length']
                }
                
                # Also update the actual group in the model if it exists (for unchanged name)
                if new_group_name == group_name and hasattr(self.sample_mapping, 'model') and hasattr(self.sample_mapping.model, 'sample_to_group'):
                    for sample in settings['samples']:
                        group = self.sample_mapping.model.sample_to_group.get(sample)
                        if group and group.name == group_name:
                            group.seq_mode = settings['seq_mode']
                            group.seq_length = settings['seq_length']
                            break
                
                # Reset individual sample round robin settings since they're handled at group level
                for sample in settings['samples']:
                    sample.seq_mode = "always"  # Reset to default since group handles round robin
                    sample.seq_length = 0       # Reset to default since group handles round robin
                    # seq_position is still set for ordering within the group
                
                # Update the tree
                self.update_groups_tree()
                
                # Trigger XML update
                if hasattr(self.sample_mapping, 'force_sync_xml'):
                    self.sample_mapping.force_sync_xml()
    
    def edit_multiple_groups(self, items):
        """Edit multiple round robin groups - only mode and length."""
        group_names = [item.text(0) for item in items]
        
        # Show simplified dialog for mode and length only
        dialog = MultiGroupEditDialog(group_names, parent=self)
        if dialog.exec() == QDialog.Accepted:
            settings = dialog.get_settings()
            
            # Update all selected groups
            for group_name in group_names:
                if group_name in self.round_robin_groups:
                    self.round_robin_groups[group_name]['seq_mode'] = settings['seq_mode']
                    self.round_robin_groups[group_name]['seq_length'] = settings['seq_length']
                    
                    # Also update the actual group in the model if it exists
                    if hasattr(self.sample_mapping, 'model') and hasattr(self.sample_mapping.model, 'sample_to_group'):
                        for sample in self.round_robin_groups[group_name]['samples']:
                            group = self.sample_mapping.model.sample_to_group.get(sample)
                            if group and group.name == group_name:
                                group.seq_mode = settings['seq_mode']
                                group.seq_length = settings['seq_length']
                                break
            
            self.update_groups_tree()
            
            # Trigger XML update
            if hasattr(self.sample_mapping, 'force_sync_xml'):
                self.sample_mapping.force_sync_xml()
    
    def remove_group(self):
        """Remove the selected round robin group."""
        current_item = self.groups_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a group to remove.")
            return
        
        group_name = current_item.text(0)
        reply = QMessageBox.question(
            self, 
            "Remove Group", 
            f"Are you sure you want to remove the round robin group '{group_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if group_name in self.round_robin_groups:
                # Reset round robin settings for samples in this group
                group_data = self.round_robin_groups[group_name]
                for sample in group_data['samples']:
                    sample.seq_mode = "always"
                    sample.seq_length = 0
                    sample.seq_position = 1
                
                del self.round_robin_groups[group_name]
                self.update_groups_tree()
                
                # Trigger XML update
                if hasattr(self.sample_mapping, 'force_sync_xml'):
                    self.sample_mapping.force_sync_xml()
    
    def preview_group(self):
        """Preview the selected round robin group by cycling through all samples."""
        current_item = self.groups_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a group to preview.")
            return
        
        group_name = current_item.text(0)
        if group_name in self.round_robin_groups:
            group_data = self.round_robin_groups[group_name]
            samples = group_data['samples']
            
            if samples:
                if hasattr(self.sample_mapping, 'play_sample_file'):
                    # Start the round robin preview
                    self.start_round_robin_preview(samples, group_data['seq_mode'])
                else:
                    QMessageBox.information(self, "Preview", f"Would cycle through {len(samples)} samples in round robin mode: {group_data['seq_mode']}")
    
    def start_round_robin_preview(self, samples, seq_mode):
        """Start a round robin preview that cycles through all samples."""
        if not samples:
            return
        
        # Create a preview thread to cycle through samples
        from PySide6.QtCore import QThread, QTimer
        import time
        
        class RoundRobinPreviewThread(QThread):
            def __init__(self, samples, seq_mode, play_callback):
                super().__init__()
                self.samples = samples
                self.seq_mode = seq_mode
                self.play_callback = play_callback
                self.running = True
                self.current_index = 0
            
            def run(self):
                if self.seq_mode == "round_robin":
                    # Sequential round robin - play each sample in order
                    for i, sample in enumerate(self.samples):
                        if not self.running:
                            break
                        self.play_callback(sample)
                        if i < len(self.samples) - 1:  # Don't wait after the last sample
                            self.msleep(2000)  # Wait 2 seconds between samples
                elif self.seq_mode == "random":
                    # Random selection - play 5 random samples
                    import random
                    for _ in range(min(5, len(self.samples) * 2)):  # Play up to 5 samples
                        if not self.running:
                            break
                        sample = random.choice(self.samples)
                        self.play_callback(sample)
                        self.msleep(2000)  # Wait 2 seconds between samples
                elif self.seq_mode == "true_random":
                    # True random - play 5 random samples with random timing
                    import random
                    for _ in range(min(5, len(self.samples) * 2)):  # Play up to 5 samples
                        if not self.running:
                            break
                        sample = random.choice(self.samples)
                        self.play_callback(sample)
                        # Random delay between 1-3 seconds
                        self.msleep(random.randint(1000, 3000))
                else:  # "always" mode - just play the first sample
                    self.play_callback(self.samples[0])
            
            def stop(self):
                self.running = False
        
        # Start the preview thread
        self.preview_thread = RoundRobinPreviewThread(samples, seq_mode, self.sample_mapping.play_sample_file)
        self.preview_thread.start()
        
        # Store reference so we can stop it if needed
        self.current_preview_thread = self.preview_thread
        
        # Update button text to show it's playing
        self.preview_btn.setText("⏹️ Stop Preview")
        self.preview_btn.clicked.disconnect()
        self.preview_btn.clicked.connect(self.stop_preview)
    
    def stop_preview(self):
        """Stop the current round robin preview."""
        if self.current_preview_thread and self.current_preview_thread.isRunning():
            self.current_preview_thread.stop()
            self.current_preview_thread.wait()  # Wait for thread to finish
            self.current_preview_thread = None
        
        # Reset button text
        self.preview_btn.setText("🎵 Preview")
        self.preview_btn.clicked.disconnect()
        self.preview_btn.clicked.connect(self.preview_group)
    
    def select_all_groups(self):
        """Select all groups in the tree."""
        self.groups_tree.selectAll()
    
    def get_note_name(self, midi_note):
        """Convert MIDI note number to note name."""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1
        note_index = midi_note % 12
        return f"{note_names[note_index]}{octave}"
    
    def closeEvent(self, event):
        """Clean up when the widget is closed."""
        self.stop_preview()
        super().closeEvent(event)
    
    def auto_detect_groups(self):
        """Auto-detect round robin groups from filename patterns."""
        if not hasattr(self.sample_mapping, 'model'):
            QMessageBox.warning(self, "No Samples", "No samples available for auto-detection.")
            return
        
        # Group samples by base name (without round robin suffix)
        samples_by_base = {}
        for sample in self.sample_mapping.model.samples:
            base_name = self.extract_base_name(sample.file_path.stem)
            if base_name not in samples_by_base:
                samples_by_base[base_name] = []
            samples_by_base[base_name].append(sample)
        
        # Create groups for samples with multiple variations
        detected_groups = 0
        for base_name, samples in samples_by_base.items():
            if len(samples) > 1:
                # Set seq_position for each sample based on filename pattern
                for sample in samples:
                    sample.seq_position = self.extract_round_robin_position(sample.file_path.stem)
                
                # Sort samples by detected position
                samples.sort(key=lambda s: s.seq_position)
                
                # Use the note name from the first sample instead of base name
                first_sample = samples[0]
                note_name = self.get_note_name(first_sample.root_note)
                group_name = f"RR_{note_name}"
                self.round_robin_groups[group_name] = {
                    'samples': samples,
                    'seq_mode': 'round_robin',
                    'seq_length': len(samples)
                }
                detected_groups += 1
        
        if detected_groups > 0:
            # Create SampleGroup objects in the model for detected groups
            for group_name, group_data in self.round_robin_groups.items():
                # Create a new SampleGroup in the model
                if hasattr(self.sample_mapping, 'model'):
                    new_group = SampleGroup(
                        name=group_name,
                        enabled=True,
                        volume="1.0",
                        seq_mode=group_data['seq_mode'],
                        seq_length=group_data['seq_length'],
                        samples=group_data['samples']
                    )
                    
                    # Add the group to the model
                    self.sample_mapping.model.add_sample_group(new_group)
                    
                    # Move samples to the new group
                    for sample in group_data['samples']:
                        self.sample_mapping.model.add_sample_to_group(sample, new_group)
                        # Reset individual sample round robin settings since group handles it
                        sample.seq_mode = "always"
                        sample.seq_length = 0
            
            self.update_groups_tree()
            
            # Trigger XML update
            if hasattr(self.sample_mapping, 'force_sync_xml'):
                self.sample_mapping.force_sync_xml()
            
            QMessageBox.information(self, "Auto-Detection Complete", 
                                  f"Detected {detected_groups} round robin groups.")
        else:
            QMessageBox.information(self, "Auto-Detection Complete", 
                                  "No round robin patterns detected.")
    
    def extract_base_name(self, filename):
        """Extract base name from filename by removing round robin patterns."""
        # Remove common round robin patterns
        patterns = [
            r'_rr\d+$',      # _rr1, _rr2, etc.
            r'_\d+$',        # _1, _2, etc.
            r'_round\d+$',   # _round1, _round2, etc.
            r'_alt\d+$',     # _alt1, _alt2, etc.
            r'_var\d+$',     # _var1, _var2, etc.
            r'#\d+$',        # #1, #2, etc.
        ]
        
        for pattern in patterns:
            filename = re.sub(pattern, '', filename, flags=re.IGNORECASE)
        
        return filename
    
    def extract_round_robin_position(self, filename):
        """Extract round robin position from filename patterns."""
        # Check for # pattern first (e.g., C4#1, C4#2)
        hash_match = re.search(r'#(\d+)$', filename)
        if hash_match:
            return int(hash_match.group(1))
        
        # Check for other patterns
        patterns = [
            (r'_rr(\d+)$', 1),      # _rr1, _rr2, etc.
            (r'_(\d+)$', 1),        # _1, _2, etc.
            (r'_round(\d+)$', 1),   # _round1, _round2, etc.
            (r'_alt(\d+)$', 1),     # _alt1, _alt2, etc.
            (r'_var(\d+)$', 1),     # _var1, _var2, etc.
        ]
        
        for pattern, group_num in patterns:
            match = re.search(pattern, filename, flags=re.IGNORECASE)
            if match:
                return int(match.group(group_num))
        
        return 1  # Default position
    
    def update_groups_tree(self):
        """Update the groups tree widget."""
        self.groups_tree.clear()
        
        for group_name, group_data in self.round_robin_groups.items():
            # Create details string
            details = f"Mode: {group_data['seq_mode']}"
            if group_data['seq_length'] > 0:
                details += f", Length: {group_data['seq_length']}"
            else:
                details += ", Length: Auto"
            
            item = QTreeWidgetItem([
                group_name,
                group_data['seq_mode'],
                str(len(group_data['samples'])),
                str(group_data['seq_length']) if group_data['seq_length'] > 0 else "Auto",
                details
            ])
            
            # Add samples as child items
            for i, sample in enumerate(group_data['samples']):
                position = getattr(sample, 'seq_position', i+1)
                child_item = QTreeWidgetItem([
                    f"{i+1}. {sample.file_path.name}",
                    f"Position {position}",
                    "",
                    "",
                    f"File: {sample.file_path.name}"
                ])
                item.addChild(child_item)
            
            self.groups_tree.addTopLevelItem(item)
        
        # Expand all items
        self.groups_tree.expandAll()
    
    def get_round_robin_groups(self):
        """Get all round robin groups."""
        return self.round_robin_groups
