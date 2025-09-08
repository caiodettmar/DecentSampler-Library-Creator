"""
DecentSampler GUI Application

A PySide6-based GUI for creating DecentSampler (.dspreset) files.
"""

import sys
from pathlib import Path
from typing import List, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QLineEdit, QTextEdit, QListWidget, QPushButton,
    QFileDialog, QMessageBox, QGroupBox, QSpinBox, QSplitter,
    QListWidgetItem, QFrame, QCheckBox, QTabWidget, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QTextCharFormat, QColor, QSyntaxHighlighter

from decent_sampler import DecentPreset, SampleGroup
from sample_mapping import SampleMappingWidget, RoundRobinManager


class XMLSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for XML content with improved dark mode colors."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # XML tags - bright cyan for better visibility
        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor(86, 156, 214))  # Bright cyan
        tag_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((r'<[^>]+>', tag_format))
        
        # XML attributes - bright yellow
        attr_format = QTextCharFormat()
        attr_format.setForeground(QColor(220, 220, 170))  # Light yellow
        self.highlighting_rules.append((r'\b\w+="[^"]*"', attr_format))
        
        # XML attribute values - bright green
        attr_value_format = QTextCharFormat()
        attr_value_format.setForeground(QColor(206, 145, 120))  # Light orange
        self.highlighting_rules.append((r'="[^"]*"', attr_value_format))
        
        # XML comments - muted green
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(106, 153, 85))  # Muted green
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((r'<!--.*-->', comment_format))
        
        # XML declaration - bright purple
        decl_format = QTextCharFormat()
        decl_format.setForeground(QColor(197, 134, 192))  # Light purple
        decl_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((r'<\?xml[^>]*\?>', decl_format))
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text."""
        import re
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, format)


class XMLEditor(QTextEdit):
    """XML editor widget with syntax highlighting and live updates."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_editor()
        self.highlighter = XMLSyntaxHighlighter(self.document())
        self.wrap_enabled = True  # Default to wrap enabled
    
    def setup_editor(self):
        """Setup the editor appearance and behavior."""
        # Set monospace font
        font = QFont("Consolas", 11)
        font.setFixedPitch(True)
        self.setFont(font)
        
        # Set editor properties
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.WidgetWidth)  # Default to wrap enabled
        
        # Set improved dark mode styling
        self.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d30;
                color: #d4d4d4;
                border: 2px solid #3e3e42;
                border-radius: 4px;
                padding: 8px;
                selection-background-color: #264f78;
                selection-color: #ffffff;
            }
            QTextEdit:focus {
                border-color: #0078d4;
            }
        """)
    
    def set_wrap_mode(self, enabled: bool):
        """Enable or disable text wrapping."""
        self.wrap_enabled = enabled
        if enabled:
            self.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            self.setLineWrapMode(QTextEdit.NoWrap)
    
    def update_xml(self, xml_string: str):
        """Update the XML content with improved formatting."""
        # Store current scroll position and wrap mode
        scrollbar = self.verticalScrollBar()
        scroll_position = scrollbar.value()
        current_wrap_mode = self.lineWrapMode()
        
        # Update content
        self.setPlainText(xml_string)
        
        # Restore wrap mode (in case it was reset)
        self.setLineWrapMode(current_wrap_mode)
        
        # Move cursor to top
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.setTextCursor(cursor)
        
        # Restore scroll position if it was at the top
        if scroll_position == 0:
            scrollbar.setValue(0)






class DecentSamplerMainWindow(QMainWindow):
    """Main window for the DecentSampler GUI application."""
    
    def __init__(self):
        super().__init__()
        self.xml_editor = None
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_xml_live)
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("DecentSampler Library Creator")
        self.setGeometry(100, 100, 1600, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Title
        title_label = QLabel("DecentSampler Library Creator")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Main content area with Sample Mapping and Preview
        content_layout = QHBoxLayout()
        
        # Tab view (Sample Mapping + Preset Information) - takes most space
        tab_widget = self.create_tab_widget()
        content_layout.addWidget(tab_widget)
        
        # Right side with Preview and Save
        right_side_layout = QVBoxLayout()
        
        # XML Preview (takes most space)
        preview_panel = self.create_xml_panel()
        right_side_layout.addWidget(preview_panel, 1)  # Give it stretch factor of 1
        
        # Save Preset button at bottom (fixed height)
        save_panel = self.create_save_panel()
        right_side_layout.addWidget(save_panel, 0)  # No stretch, fixed size
        
        content_layout.addLayout(right_side_layout)
        main_layout.addLayout(content_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_tab_widget(self) -> QWidget:
        """Create the tab widget with Sample Mapping, Round Robin, and Preset Information."""
        tab_widget = QTabWidget()
        
        # Sample Mapping tab
        mapping_tab = self.create_mapping_tab()
        tab_widget.addTab(mapping_tab, "Sample Mapping")
        
        # Round Robin tab
        round_robin_tab = self.create_round_robin_tab()
        tab_widget.addTab(round_robin_tab, "Round Robin by Group")
        
        # Library Information tab
        preset_tab = self.create_preset_tab()
        tab_widget.addTab(preset_tab, "Library Information")
        
        return tab_widget
    
    def create_mapping_tab(self) -> QWidget:
        """Create the sample mapping tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Create sample mapping widget
        self.sample_mapping = SampleMappingWidget()
        layout.addWidget(self.sample_mapping)
        
        # Store reference to sample mapping for round robin manager
        self.sample_mapping.main_window = self
        
        # Connect sample mapping changes to live XML updates
        if hasattr(self.sample_mapping, 'model'):
            self.sample_mapping.model.dataChanged.connect(self.schedule_xml_update)
        
        
        return tab
    
    def create_round_robin_tab(self) -> QWidget:
        """Create the round robin management tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Create round robin manager
        self.round_robin_manager = RoundRobinManager(self.sample_mapping)
        layout.addWidget(self.round_robin_manager)
        
        return tab
    
    def create_preset_tab(self) -> QWidget:
        """Create the preset information tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Library info group
        preset_group = QGroupBox("Library Information")
        preset_layout = QGridLayout()
        preset_group.setLayout(preset_layout)
        
        # Library name
        preset_layout.addWidget(QLabel("Library Name:"), 0, 0)
        self.preset_name_edit = QLineEdit()
        self.preset_name_edit.setPlaceholderText("Enter library name...")
        self.preset_name_edit.textChanged.connect(self.schedule_xml_update)
        preset_layout.addWidget(self.preset_name_edit, 0, 1)
        
        # Author
        preset_layout.addWidget(QLabel("Author:"), 1, 0)
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Enter author name...")
        self.author_edit.textChanged.connect(self.schedule_xml_update)
        preset_layout.addWidget(self.author_edit, 1, 1)
        
        # Category
        preset_layout.addWidget(QLabel("Category:"), 2, 0)
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("e.g., Piano, Strings, Drums...")
        self.category_edit.textChanged.connect(self.schedule_xml_update)
        preset_layout.addWidget(self.category_edit, 2, 1)
        
        # Description
        preset_layout.addWidget(QLabel("Description:"), 3, 0)
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter description...")
        self.description_edit.setMaximumHeight(100)
        self.description_edit.textChanged.connect(self.schedule_xml_update)
        preset_layout.addWidget(self.description_edit, 3, 1)
        
        # Samples Path
        preset_layout.addWidget(QLabel("Samples Path:"), 4, 0)
        self.samples_path_edit = QLineEdit()
        self.samples_path_edit.setPlaceholderText("/Samples")
        self.samples_path_edit.setText("/Samples")  # Set default value
        self.samples_path_edit.textChanged.connect(self.schedule_xml_update)
        preset_layout.addWidget(self.samples_path_edit, 4, 1)
        
        # Min Version
        preset_layout.addWidget(QLabel("Min Version:"), 5, 0)
        self.min_version_edit = QLineEdit()
        self.min_version_edit.setPlaceholderText("0 (omit if 0 or empty)")
        self.min_version_edit.setText("0")  # Set default value
        self.min_version_edit.textChanged.connect(self.schedule_xml_update)
        preset_layout.addWidget(self.min_version_edit, 5, 1)
        
        layout.addWidget(preset_group)
        
        # Global Groups Attributes
        groups_group = QGroupBox("Global Groups Attributes")
        groups_layout = QGridLayout()
        groups_group.setLayout(groups_layout)
        
        # Volume
        groups_layout.addWidget(QLabel("Volume:"), 0, 0)
        self.volume_edit = QLineEdit()
        self.volume_edit.setPlaceholderText("1.0 or 3dB")
        self.volume_edit.setText("1.0")  # Set default value
        self.volume_edit.textChanged.connect(self.schedule_xml_update)
        groups_layout.addWidget(self.volume_edit, 0, 1)
        
        # Global Tuning
        groups_layout.addWidget(QLabel("Global Tuning:"), 1, 0)
        self.global_tuning_edit = QLineEdit()
        self.global_tuning_edit.setPlaceholderText("0.0 (semitones)")
        self.global_tuning_edit.setText("0.0")  # Set default value
        self.global_tuning_edit.textChanged.connect(self.schedule_xml_update)
        groups_layout.addWidget(self.global_tuning_edit, 1, 1)
        
        # Glide Time
        groups_layout.addWidget(QLabel("Glide Time:"), 2, 0)
        self.glide_time_edit = QLineEdit()
        self.glide_time_edit.setPlaceholderText("0.0")
        self.glide_time_edit.setText("0.0")  # Set default value
        self.glide_time_edit.textChanged.connect(self.schedule_xml_update)
        groups_layout.addWidget(self.glide_time_edit, 2, 1)
        
        # Glide Mode
        groups_layout.addWidget(QLabel("Glide Mode:"), 3, 0)
        self.glide_mode_combo = QComboBox()
        self.glide_mode_combo.addItems(["legato", "always", "off"])
        self.glide_mode_combo.setCurrentText("legato")  # Set default value
        self.glide_mode_combo.currentTextChanged.connect(self.schedule_xml_update)
        groups_layout.addWidget(self.glide_mode_combo, 3, 1)
        
        # Global Round Robin Enable
        self.global_round_robin_checkbox = QCheckBox("Enable Global Round Robin")
        self.global_round_robin_checkbox.setChecked(False)  # Default to disabled
        self.global_round_robin_checkbox.toggled.connect(self.toggle_global_round_robin)
        groups_layout.addWidget(self.global_round_robin_checkbox, 4, 0, 1, 2)
        
        # Global Round Robin Mode
        groups_layout.addWidget(QLabel("Global Round Robin Mode:"), 5, 0)
        self.global_seq_mode_combo = QComboBox()
        self.global_seq_mode_combo.addItems(["always", "random", "true_random", "round_robin"])
        self.global_seq_mode_combo.setCurrentText("always")  # Set default value
        self.global_seq_mode_combo.currentTextChanged.connect(self.schedule_xml_update)
        self.global_seq_mode_combo.setEnabled(False)  # Start disabled
        groups_layout.addWidget(self.global_seq_mode_combo, 5, 1)
        
        # Global Round Robin Length
        groups_layout.addWidget(QLabel("Global Round Robin Length:"), 6, 0)
        self.global_seq_length_edit = QLineEdit()
        self.global_seq_length_edit.setPlaceholderText("0 (auto-detect)")
        self.global_seq_length_edit.setText("0")  # Set default value
        self.global_seq_length_edit.textChanged.connect(self.schedule_xml_update)
        self.global_seq_length_edit.setEnabled(False)  # Start disabled
        groups_layout.addWidget(self.global_seq_length_edit, 6, 1)
        
        layout.addWidget(groups_group)
        
        # Add sync button (matching Sample Mapping style)
        sync_layout = QHBoxLayout()
        sync_layout.addStretch()  # Push button to the right
        
        self.sync_xml_btn = QPushButton("🔄")
        self.sync_xml_btn.setToolTip("Sync with XML Preview")
        self.sync_xml_btn.setStyleSheet("""
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
        self.sync_xml_btn.clicked.connect(self.update_xml_live)
        sync_layout.addWidget(self.sync_xml_btn)
        layout.addLayout(sync_layout)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        return tab
    
    def create_save_panel(self) -> QWidget:
        """Create the save panel with action buttons."""
        panel = QWidget()
        panel.setMaximumWidth(200)
        panel.setMaximumHeight(120)  # Limit height to make it more compact
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Action buttons group
        buttons_group = QGroupBox("Actions")
        buttons_layout = QVBoxLayout()
        buttons_group.setLayout(buttons_layout)
        
        self.save_preset_btn = QPushButton("Save Preset...")
        self.save_preset_btn.clicked.connect(self.save_preset)
        self.save_preset_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 10px; }")
        buttons_layout.addWidget(self.save_preset_btn)
        
        layout.addWidget(buttons_group)
        
        return panel
    
    def create_xml_panel(self) -> QWidget:
        """Create the XML preview panel."""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # XML preview group
        xml_group = QGroupBox("XML Preview")
        xml_layout = QVBoxLayout()
        xml_group.setLayout(xml_layout)
        
        # XML controls
        controls_layout = QHBoxLayout()
        
        # Text wrap checkbox
        self.wrap_checkbox = QCheckBox("Wrap Text")
        self.wrap_checkbox.setChecked(True)  # Default to wrap enabled
        self.wrap_checkbox.stateChanged.connect(self.toggle_text_wrap)
        controls_layout.addWidget(self.wrap_checkbox)
        
        controls_layout.addStretch()  # Push controls to the left
        
        xml_layout.addLayout(controls_layout)
        
        # XML editor with increased height
        self.xml_editor = XMLEditor()
        self.xml_editor.setMinimumHeight(600)  # Set minimum height to 600px
        xml_layout.addWidget(self.xml_editor)
        
        layout.addWidget(xml_group)
        
        # Add stretch to push XML group to top and make it expand
        layout.addStretch()
        
        # Initialize with empty XML
        self.update_xml_live()
        
        return panel
    
    def toggle_text_wrap(self, state):
        """Toggle text wrapping in the XML editor."""
        if self.xml_editor:
            # Handle checkbox state properly
            enabled = state == Qt.CheckState.Checked
            self.xml_editor.set_wrap_mode(enabled)
    
    def toggle_global_round_robin(self, checked):
        """Toggle global round robin settings enabled/disabled."""
        self.global_seq_mode_combo.setEnabled(checked)
        self.global_seq_length_edit.setEnabled(checked)
        self.schedule_xml_update()
    
    
    
    
    def setup_connections(self):
        """Setup signal connections."""
        # Connect preset property changes to live XML updates
        self.preset_name_edit.textChanged.connect(self.schedule_xml_update)
        self.author_edit.textChanged.connect(self.schedule_xml_update)
        self.category_edit.textChanged.connect(self.schedule_xml_update)
        self.description_edit.textChanged.connect(self.schedule_xml_update)
        self.min_version_edit.textChanged.connect(self.schedule_xml_update)
    
    
    def schedule_xml_update(self):
        """Schedule an XML update with a small delay to avoid excessive updates."""
        self.update_timer.stop()
        self.update_timer.start(300)  # 300ms delay
    
    def update_xml_live(self):
        """Update the XML editor with current preset data."""
        if not self.xml_editor:
            return
        
        try:
            # Check if we have samples from the mapping widget
            has_samples = False
            if hasattr(self, 'sample_mapping'):
                sample_groups = self.sample_mapping.get_sample_groups()
                has_samples = len(sample_groups) > 0
            
            if not has_samples:
                # Show empty preset XML with better formatting
                xml_string = """<?xml version='1.0' encoding='UTF-8'?>
<DecentSampler>
  <groups>
    
    <!-- Add sample files to see XML here -->
    <!-- Each sample will appear as a <sample> element inside a <group> -->
    
  </groups>
</DecentSampler>"""
            else:
                preset = self.create_preset()
                
                # Get global attributes from UI
                global_volume = self.volume_edit.text() or "1.0"
                global_tuning = self.global_tuning_edit.text() or "0.0"
                glide_time = self.glide_time_edit.text() or "0.0"
                glide_mode = self.glide_mode_combo.currentText() or "legato"
                
                # Only include global round robin settings if enabled
                if self.global_round_robin_checkbox.isChecked():
                    global_seq_mode = self.global_seq_mode_combo.currentText() or "always"
                    global_seq_length = self.global_seq_length_edit.text() or "0"
                else:
                    global_seq_mode = "always"  # Default when disabled
                    global_seq_length = "0"     # Default when disabled
                
                # Generate XML with global attributes
                min_version = self.min_version_edit.text() or "0"
                xml_tree = preset.to_xml(
                    global_volume=global_volume,
                    global_tuning=global_tuning,
                    glide_time=glide_time,
                    glide_mode=glide_mode,
                    global_seq_mode=global_seq_mode,
                    global_seq_length=global_seq_length,
                    min_version=min_version,
                    preset_name=self.preset_name_edit.text(),
                    author=self.author_edit.text(),
                    category=self.category_edit.text(),
                    description=self.description_edit.toPlainText()
                )
                xml_string = self.format_xml(xml_tree)
            
            self.xml_editor.update_xml(xml_string)
            
        except Exception as e:
            error_xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<DecentSampler>
  <groups>
    
    <!-- Error generating XML: {str(e)} -->
    <!-- Please check your preset configuration -->
    
  </groups>
</DecentSampler>"""
            self.xml_editor.update_xml(error_xml)
    
    def format_xml(self, xml_tree) -> str:
        """Format XML tree to string with proper indentation."""
        from lxml import etree
        
        # Convert to string with pretty printing
        xml_string = etree.tostring(
            xml_tree, 
            encoding='unicode', 
            pretty_print=True,
            xml_declaration=False
        )
        return xml_string
    
    def save_preset(self):
        """Save the preset to a file."""
        # Check for mandatory fields
        if not self.preset_name_edit.text().strip():
            QMessageBox.warning(self, "Missing Information", "Please enter a Preset Name before saving.")
            return
        
        if not self.author_edit.text().strip():
            QMessageBox.warning(self, "Missing Information", "Please enter an Author before saving.")
            return
        
        if hasattr(self, 'sample_mapping'):
            sample_groups = self.sample_mapping.get_sample_groups()
            if not sample_groups:
                QMessageBox.warning(self, "No Samples", "Please add at least one sample file using the Sample Mapping tab.")
                return
        else:
            QMessageBox.warning(self, "No Samples", "Please add at least one sample file using the Sample Mapping tab.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save DecentSampler Preset",
            "",
            "DecentSampler Preset (*.dspreset);;All Files (*)"
        )
        
        if file_path:
            preset = self.create_preset()
            
            # Get global attributes from UI
            global_volume = self.volume_edit.text() or "1.0"
            global_tuning = self.global_tuning_edit.text() or "0.0"
            glide_time = self.glide_time_edit.text() or "0.0"
            glide_mode = self.glide_mode_combo.currentText() or "legato"
            
            # Only include global round robin settings if enabled
            if self.global_round_robin_checkbox.isChecked():
                global_seq_mode = self.global_seq_mode_combo.currentText() or "always"
                global_seq_length = self.global_seq_length_edit.text() or "0"
            else:
                global_seq_mode = "always"  # Default when disabled
                global_seq_length = "0"     # Default when disabled
            
            # Generate XML with global attributes and save
            min_version = self.min_version_edit.text() or "0"
            xml_tree = preset.to_xml(
                global_volume=global_volume,
                global_tuning=global_tuning,
                glide_time=glide_time,
                glide_mode=glide_mode,
                global_seq_mode=global_seq_mode,
                global_seq_length=global_seq_length,
                min_version=min_version,
                preset_name=self.preset_name_edit.text(),
                author=self.author_edit.text(),
                category=self.category_edit.text(),
                description=self.description_edit.toPlainText()
            )
            xml_tree.write(file_path, encoding='utf-8', xml_declaration=False, pretty_print=True)
            self.statusBar().showMessage(f"Preset saved to: {file_path}")
            QMessageBox.information(self, "Success", f"Preset saved successfully to:\n{file_path}")
    
    def create_preset(self) -> DecentPreset:
        """Create a DecentPreset object from current UI state."""
        preset = DecentPreset(
            preset_name=self.preset_name_edit.text() or "Untitled Preset",
            author=self.author_edit.text(),
            description=self.description_edit.toPlainText(),
            category=self.category_edit.text(),
            samples_path=self.samples_path_edit.text() or "/Samples"
        )
        
        # Add all sample groups from the mapping widget
        if hasattr(self, 'sample_mapping'):
            sample_groups = self.sample_mapping.get_sample_groups()
            for sample_group in sample_groups:
                preset.add_sample_group(sample_group)
        
        return preset


def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("DecentSampler Library Creator")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Decent Converter")
    
    # Create and show main window
    window = DecentSamplerMainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
