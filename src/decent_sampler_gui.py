"""
DecentSampler GUI Application

A PySide6-based GUI for creating DecentSampler (.dspreset) files.
"""

import sys
import os
from pathlib import Path
from typing import List, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QLineEdit, QTextEdit, QListWidget, QPushButton,
    QFileDialog, QMessageBox, QGroupBox, QSpinBox, QSplitter,
    QListWidgetItem, QFrame, QCheckBox, QTabWidget, QComboBox,
    QMenuBar, QMenu, QDialog, QDialogButtonBox, QSlider
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QTextCharFormat, QColor, QSyntaxHighlighter, QKeySequence, QAction, QPixmap

from decent_sampler import DecentPreset, SampleGroup
from sample_mapping import SampleMappingWidget, RoundRobinManager
from project_manager import Project, ProjectSettings


class PreferencesDialog(QDialog):
    """Dialog for configuring application preferences."""
    
    def __init__(self, settings: ProjectSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.resize(400, 300)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the preferences UI."""
        layout = QVBoxLayout(self)
        
        # Autosave group
        autosave_group = QGroupBox("Autosave Settings")
        autosave_layout = QVBoxLayout()
        autosave_group.setLayout(autosave_layout)
        
        # Enable autosave checkbox
        self.autosave_enabled_checkbox = QCheckBox("Enable autosave")
        self.autosave_enabled_checkbox.setChecked(True)
        self.autosave_enabled_checkbox.toggled.connect(self.toggle_autosave_settings)
        autosave_layout.addWidget(self.autosave_enabled_checkbox)
        
        # Autosave interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Autosave interval:"))
        self.autosave_interval_spinbox = QSpinBox()
        self.autosave_interval_spinbox.setRange(1, 60)
        self.autosave_interval_spinbox.setSuffix(" minutes")
        self.autosave_interval_spinbox.setValue(5)
        interval_layout.addWidget(self.autosave_interval_spinbox)
        interval_layout.addStretch()
        autosave_layout.addLayout(interval_layout)
        
        # Autosave location
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Autosave location:"))
        self.autosave_location_edit = QLineEdit()
        self.autosave_location_edit.setReadOnly(True)
        location_layout.addWidget(self.autosave_location_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_autosave_location)
        location_layout.addWidget(browse_btn)
        autosave_layout.addLayout(location_layout)
        
        # Info label
        info_label = QLabel("Autosave files are automatically cleaned up. Only the 5 most recent autosaves are kept.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        autosave_layout.addWidget(info_label)
        
        layout.addWidget(autosave_group)
        
        # Recent projects group
        recent_group = QGroupBox("Recent Projects")
        recent_layout = QVBoxLayout()
        recent_group.setLayout(recent_layout)
        
        # Max recent projects
        max_recent_layout = QHBoxLayout()
        max_recent_layout.addWidget(QLabel("Maximum recent projects:"))
        self.max_recent_spinbox = QSpinBox()
        self.max_recent_spinbox.setRange(1, 20)
        self.max_recent_spinbox.setValue(10)
        max_recent_layout.addWidget(self.max_recent_spinbox)
        max_recent_layout.addStretch()
        recent_layout.addLayout(max_recent_layout)
        
        layout.addWidget(recent_group)
        
        # Add stretch
        layout.addStretch()
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_settings(self):
        """Load current settings into the dialog."""
        self.autosave_enabled_checkbox.setChecked(self.settings.autosave_enabled)
        self.autosave_interval_spinbox.setValue(self.settings.autosave_interval)
        self.autosave_location_edit.setText(str(self.settings.temp_directory))
        self.max_recent_spinbox.setValue(self.settings.max_recent_projects)
        
        self.toggle_autosave_settings()
    
    def toggle_autosave_settings(self):
        """Enable/disable autosave settings based on checkbox."""
        enabled = self.autosave_enabled_checkbox.isChecked()
        self.autosave_interval_spinbox.setEnabled(enabled)
        self.autosave_location_edit.setEnabled(enabled)
    
    def browse_autosave_location(self):
        """Browse for autosave location."""
        current_path = self.autosave_location_edit.text()
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Autosave Directory",
            current_path if current_path else ""
        )
        
        if directory:
            self.autosave_location_edit.setText(directory)
    
    def get_settings(self) -> ProjectSettings:
        """Get the updated settings from the dialog."""
        new_settings = ProjectSettings()
        new_settings.autosave_enabled = self.autosave_enabled_checkbox.isChecked()
        new_settings.autosave_interval = self.autosave_interval_spinbox.value()
        new_settings.temp_directory = Path(self.autosave_location_edit.text())
        new_settings.max_recent_projects = self.max_recent_spinbox.value()
        
        # Preserve other settings
        new_settings.recent_projects = self.settings.recent_projects
        new_settings.window_geometry = self.settings.window_geometry
        new_settings.last_samples_directory = self.settings.last_samples_directory
        new_settings.last_export_directory = self.settings.last_export_directory
        
        return new_settings


class MigrationDialog(QDialog):
    """Dialog for informing users about project version migrations."""
    
    def __init__(self, from_version: str, to_version: str, changes: List[str], parent=None):
        super().__init__(parent)
        self.from_version = from_version
        self.to_version = to_version
        self.changes = changes
        self.setWindowTitle("Project Migration")
        self.setModal(True)
        self.resize(500, 400)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the migration dialog UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Project Migration Required")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Version info
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel(f"From version: {self.from_version}"))
        version_layout.addWidget(QLabel("→"))
        version_layout.addWidget(QLabel(f"To version: {self.to_version}"))
        version_layout.addStretch()
        layout.addLayout(version_layout)
        
        # Changes list
        changes_group = QGroupBox("Changes Applied")
        changes_layout = QVBoxLayout()
        changes_group.setLayout(changes_layout)
        
        changes_text = QTextEdit()
        changes_text.setReadOnly(True)
        changes_text.setMaximumHeight(200)
        
        changes_content = "The following changes have been applied to make your project compatible:\n\n"
        for change in self.changes:
            changes_content += f"• {change}\n"
        
        changes_text.setPlainText(changes_content)
        changes_layout.addWidget(changes_text)
        
        layout.addWidget(changes_group)
        
        # Info message
        info_label = QLabel("Your project has been successfully migrated and is now compatible with this version of the application.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #51cf66; font-weight: bold; padding: 10px;")
        layout.addWidget(info_label)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


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
        
        # Project management
        self.current_project: Optional[Project] = None
        self.settings_file = Path.home() / ".decent_converter" / "settings.json"
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        self.app_settings = ProjectSettings.load_from_file(self.settings_file)
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.autosave_project)
        
        self.init_ui()
        self.setup_connections()
        self.setup_autosave()
        self.check_for_recovery_files()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("DecentSampler Library Creator")
        self.setGeometry(100, 100, 1600, 900)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Title and status bar
        title_layout = QHBoxLayout()
        
        # Logo
        logo_label = QLabel()
        
        # Get the correct path for the logo based on whether we're running from source or executable
        def get_resource_path(relative_path):
            """Get absolute path to resource, works for dev and for PyInstaller"""
            try:
                # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS
            except Exception:
                # Running from source
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        
        logo_path = get_resource_path("assets/DSLC Logo.png")
        
        # Fallback to development path if PyInstaller path doesn't work
        if not os.path.exists(logo_path):
            logo_path = Path(__file__).parent.parent / "assets" / "DSLC Logo.png"
        
        if os.path.exists(logo_path):
            try:
                pixmap = QPixmap(str(logo_path))
                if not pixmap.isNull():
                    # Scale the logo to appropriate size (max height 80px for better visibility)
                    scaled_pixmap = pixmap.scaledToHeight(80, Qt.SmoothTransformation)
                    logo_label.setPixmap(scaled_pixmap)
                    logo_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    # Ensure the label has enough space
                    logo_label.setMinimumHeight(80)
                    logo_label.setMaximumHeight(80)
                else:
                    logo_label.setText("Failed to load logo")
            except Exception as e:
                logo_label.setText(f"Error loading logo: {e}")
        else:
            # Fallback to text if logo not found
            logo_label.setText("DecentSampler Library Creator")
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            logo_label.setFont(title_font)
        title_layout.addWidget(logo_label)
        
        # Project status indicator
        self.project_status_indicator = QLabel("●")
        self.project_status_indicator.setStyleSheet("color: #666; font-size: 20px; font-weight: bold;")
        self.project_status_indicator.setToolTip("Project Status")
        title_layout.addWidget(self.project_status_indicator)
        
        main_layout.addLayout(title_layout)
        
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
        
        # Export .dspreset button at bottom (fixed height)
        save_panel = self.create_save_panel()
        right_side_layout.addWidget(save_panel, 0)  # No stretch, fixed size
        
        content_layout.addLayout(right_side_layout)
        main_layout.addLayout(content_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Add permanent status widgets
        self.create_status_widgets()
    
    def create_menu_bar(self):
        """Create the main menu bar with project operations."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # New Project
        new_action = QAction("&New Project", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.setStatusTip("Create a new project")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        # Open Project
        open_action = QAction("&Open Project...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("Open an existing project")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        # Recent Projects submenu
        self.recent_menu = file_menu.addMenu("Open &Recent")
        self.update_recent_projects_menu()
        
        file_menu.addSeparator()
        
        # Save Project
        save_action = QAction("&Save Project", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.setStatusTip("Save the current project")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        # Save Project As
        save_as_action = QAction("Save Project &As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.setStatusTip("Save the current project with a new name")
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Export submenu
        export_menu = file_menu.addMenu("&Export")
        
        # Export .dspreset
        export_dspreset_action = QAction("Export &Preset (.dspreset)...", self)
        export_dspreset_action.setStatusTip("Export current preset as .dspreset file")
        export_dspreset_action.triggered.connect(self.save_preset)
        export_menu.addAction(export_dspreset_action)
        
        # Export Compressed Package
        export_package_action = QAction("Export &Package (.zip)...", self)
        export_package_action.setStatusTip("Export preset with samples as compressed package")
        export_package_action.triggered.connect(self.export_package)
        export_menu.addAction(export_package_action)
        
        file_menu.addSeparator()
        
        # Preferences
        preferences_action = QAction("&Preferences...", self)
        preferences_action.setStatusTip("Configure application preferences")
        preferences_action.triggered.connect(self.show_preferences)
        file_menu.addAction(preferences_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About
        about_action = QAction("&About", self)
        about_action.setStatusTip("About DecentSampler Library Creator")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Version Info
        version_action = QAction("&Version Information", self)
        version_action.setStatusTip("Show version and compatibility information")
        version_action.triggered.connect(self.show_version_info)
        help_menu.addAction(version_action)
    
    def update_recent_projects_menu(self):
        """Update the recent projects submenu."""
        self.recent_menu.clear()
        
        if not self.app_settings.recent_projects:
            no_recent_action = QAction("No recent projects", self)
            no_recent_action.setEnabled(False)
            self.recent_menu.addAction(no_recent_action)
            return
        
        for project_path in self.app_settings.recent_projects:
            action = QAction(Path(project_path).name, self)
            action.setStatusTip(f"Open {project_path}")
            action.triggered.connect(lambda checked, path=project_path: self.open_project_file(Path(path)))
            self.recent_menu.addAction(action)
        
        self.recent_menu.addSeparator()
        clear_action = QAction("Clear Recent Projects", self)
        clear_action.triggered.connect(self.clear_recent_projects)
        self.recent_menu.addAction(clear_action)
    
    def create_status_widgets(self):
        """Create permanent status bar widgets."""
        # Project status label
        self.project_status_label = QLabel("No Project")
        self.project_status_label.setStyleSheet("color: #666; font-weight: bold;")
        self.statusBar().addPermanentWidget(self.project_status_label)
        
        # Sample count label
        self.sample_count_label = QLabel("0 samples")
        self.sample_count_label.setStyleSheet("color: #666;")
        self.statusBar().addPermanentWidget(self.sample_count_label)
        
        # Autosave status label
        self.autosave_status_label = QLabel("")
        self.autosave_status_label.setStyleSheet("color: #666; font-size: 11px;")
        self.statusBar().addPermanentWidget(self.autosave_status_label)
        
        # Update initial status
        self.update_status_widgets()
    
    def update_status_widgets(self):
        """Update the status bar widgets with current information."""
        # Update project status
        if self.current_project:
            if self.current_project.is_modified:
                self.project_status_label.setText("Modified")
                self.project_status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
                # Update visual indicator
                self.project_status_indicator.setText("●")
                self.project_status_indicator.setStyleSheet("color: #ff6b6b; font-size: 20px; font-weight: bold;")
                self.project_status_indicator.setToolTip("Project has unsaved changes")
            else:
                self.project_status_label.setText("Saved")
                self.project_status_label.setStyleSheet("color: #51cf66; font-weight: bold;")
                # Update visual indicator
                self.project_status_indicator.setText("●")
                self.project_status_indicator.setStyleSheet("color: #51cf66; font-size: 20px; font-weight: bold;")
                self.project_status_indicator.setToolTip("Project is saved")
        else:
            self.project_status_label.setText("No Project")
            self.project_status_label.setStyleSheet("color: #666; font-weight: bold;")
            # Update visual indicator
            self.project_status_indicator.setText("●")
            self.project_status_indicator.setStyleSheet("color: #666; font-size: 20px; font-weight: bold;")
            self.project_status_indicator.setToolTip("No project loaded")
        
        # Update sample count
        sample_count = 0
        if hasattr(self, 'sample_mapping') and hasattr(self.sample_mapping, 'model'):
            sample_count = len(self.sample_mapping.model.samples)
        
        self.sample_count_label.setText(f"{sample_count} samples")
        
        # Update autosave status
        if self.app_settings.autosave_enabled:
            if self.current_project and self.current_project.is_modified:
                self.autosave_status_label.setText("Autosave: Active")
                self.autosave_status_label.setStyleSheet("color: #51cf66; font-size: 11px;")
            else:
                self.autosave_status_label.setText("Autosave: Ready")
                self.autosave_status_label.setStyleSheet("color: #666; font-size: 11px;")
        else:
            self.autosave_status_label.setText("Autosave: Disabled")
            self.autosave_status_label.setStyleSheet("color: #ff6b6b; font-size: 11px;")
    
    def show_preferences(self):
        """Show preferences dialog."""
        dialog = PreferencesDialog(self.app_settings, self)
        if dialog.exec() == QDialog.Accepted:
            # Update settings
            self.app_settings = dialog.get_settings()
            
            # Save settings to file
            self.app_settings.save_to_file(self.settings_file)
            
            # Restart autosave timer with new settings
            self.autosave_timer.stop()
            self.setup_autosave()
            
            # Show confirmation
            self.statusBar().showMessage("Preferences saved")
    
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
        self.sample_mapping.main_window = self  # Set reference to main window
        layout.addWidget(self.sample_mapping)
        
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
        self.round_robin_manager.main_window = self  # Set reference to main window
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
        self.samples_path_edit.setPlaceholderText("Samples")
        self.samples_path_edit.setText("Samples")  # Set default value
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
        
        self.save_preset_btn = QPushButton("Export .dspreset...")
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
        # Connect preset property changes to live XML updates and mark as modified
        self.preset_name_edit.textChanged.connect(self.schedule_xml_update)
        self.preset_name_edit.textChanged.connect(self.mark_project_modified)
        self.author_edit.textChanged.connect(self.schedule_xml_update)
        self.author_edit.textChanged.connect(self.mark_project_modified)
        self.category_edit.textChanged.connect(self.schedule_xml_update)
        self.category_edit.textChanged.connect(self.mark_project_modified)
        self.description_edit.textChanged.connect(self.schedule_xml_update)
        self.description_edit.textChanged.connect(self.mark_project_modified)
        self.min_version_edit.textChanged.connect(self.schedule_xml_update)
        self.min_version_edit.textChanged.connect(self.mark_project_modified)
        
        # Connect other UI changes to mark as modified
        self.samples_path_edit.textChanged.connect(self.mark_project_modified)
        self.volume_edit.textChanged.connect(self.mark_project_modified)
        self.global_tuning_edit.textChanged.connect(self.mark_project_modified)
        self.glide_time_edit.textChanged.connect(self.mark_project_modified)
        self.glide_mode_combo.currentTextChanged.connect(self.mark_project_modified)
        self.global_round_robin_checkbox.toggled.connect(self.mark_project_modified)
        self.global_seq_mode_combo.currentTextChanged.connect(self.mark_project_modified)
        self.global_seq_length_edit.textChanged.connect(self.mark_project_modified)
    
    
    def schedule_xml_update(self):
        """Schedule an XML update with a small delay to avoid excessive updates."""
        self.update_timer.stop()
        self.update_timer.start(300)  # 300ms delay
    
    def mark_project_modified(self):
        """Mark the current project as modified."""
        if self.current_project:
            self.current_project.mark_modified()
            self.update_window_title()
            self.update_status_widgets()
    
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
        
        # Add XML declaration manually since we can't use it with unicode encoding
        xml_declaration = "<?xml version='1.0' encoding='UTF-8'?>\n"
        return xml_declaration + xml_string
    
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
            "Export DecentSampler Preset",
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
            self.statusBar().showMessage(f"Preset exported to: {file_path}")
            QMessageBox.information(self, "Success", f"Preset exported successfully to:\n{file_path}")
    
    def export_package(self):
        """Export preset with samples as a compressed package."""
        # Check for mandatory fields
        if not self.preset_name_edit.text().strip():
            QMessageBox.warning(self, "Missing Information", "Please enter a Preset Name before exporting.")
            return
        
        if not self.author_edit.text().strip():
            QMessageBox.warning(self, "Missing Information", "Please enter an Author before exporting.")
            return
        
        # Check if we have samples
        if not hasattr(self, 'sample_mapping') or not self.sample_mapping.get_sample_groups():
            QMessageBox.warning(self, "No Samples", "No samples found to export.")
            return
        
        # Get file path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Package", 
            f"{self.preset_name_edit.text()}.zip",
            "ZIP Archive (*.zip)"
        )
        
        if not file_path:
            return
        
        try:
            import zipfile
            import tempfile
            import shutil
            from pathlib import Path
            
            # Create temporary directory for package contents
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create Samples directory
                samples_dir = temp_path / "Samples"
                samples_dir.mkdir()
                
                # Copy all sample files to Samples directory
                sample_files = []
                for sample_group in self.sample_mapping.get_sample_groups():
                    for sample in sample_group.samples:
                        if sample.file_path.exists():
                            dest_path = samples_dir / sample.file_path.name
                            shutil.copy2(sample.file_path, dest_path)
                            sample_files.append(sample.file_path.name)
                
                if not sample_files:
                    QMessageBox.warning(self, "No Sample Files", "No sample files found to include in package.")
                    return
                
                # Create preset file
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
                
                # Save preset file
                preset_file = temp_path / f"{self.preset_name_edit.text()}.dspreset"
                xml_tree.write(preset_file, encoding='utf-8', xml_declaration=False, pretty_print=True)
                
                # Create ZIP file
                with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Add preset file
                    zipf.write(preset_file, preset_file.name)
                    
                    # Add all sample files
                    for sample_file in sample_files:
                        sample_path = samples_dir / sample_file
                        zipf.write(sample_path, f"Samples/{sample_file}")
                
                self.statusBar().showMessage(f"Package exported to: {file_path}")
                QMessageBox.information(self, "Success", 
                    f"Package exported successfully to:\n{file_path}\n\n"
                    f"Includes:\n"
                    f"- {preset_file.name}\n"
                    f"- {len(sample_files)} sample files in Samples/ folder")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export package:\n{str(e)}")
    
    def create_preset(self) -> DecentPreset:
        """Create a DecentPreset object from current UI state."""
        preset = DecentPreset(
            preset_name=self.preset_name_edit.text() or "Untitled Preset",
            author=self.author_edit.text(),
            description=self.description_edit.toPlainText(),
            category=self.category_edit.text(),
            samples_path=self.samples_path_edit.text() or "Samples"
        )
        
        # Add only sample groups that have samples (for XML generation)
        # Empty groups are kept in the project but not included in XML
        # Note: Round Robin groups are already included in the main sample groups
        if hasattr(self, 'sample_mapping'):
            sample_groups = self.sample_mapping.get_sample_groups()
            for sample_group in sample_groups:
                # Only add groups that have samples to the XML
                if sample_group.samples:
                    preset.add_sample_group(sample_group)
        
        return preset
    
    # Project Management Methods
    
    def setup_autosave(self):
        """Setup autosave timer."""
        if self.app_settings.autosave_enabled:
            interval_ms = self.app_settings.autosave_interval * 60 * 1000  # Convert minutes to milliseconds
            self.autosave_timer.start(interval_ms)
    
    def autosave_project(self):
        """Perform autosave if needed."""
        if self.current_project and self.current_project.is_autosave_needed():
            self.current_project.create_autosave()
            self.current_project.cleanup_autosaves()
    
    def check_for_recovery_files(self):
        """Check for recovery files and prompt user if found."""
        if not self.app_settings.autosave_enabled:
            return
        
        try:
            # Ensure temp directory exists
            self.app_settings.temp_directory.mkdir(parents=True, exist_ok=True)
            
            # Find all autosave files
            autosave_files = list(self.app_settings.temp_directory.glob("autosave_*.dsproj"))
            
            if not autosave_files:
                return
            
            # Sort by modification time (newest first)
            autosave_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_autosave = autosave_files[0]
            
            # Check if autosave is recent (within last 24 hours)
            import time
            current_time = time.time()
            file_time = latest_autosave.stat().st_mtime
            time_diff = current_time - file_time
            
            if time_diff > 24 * 60 * 60:  # 24 hours
                return
            
            # Prompt user about recovery
            reply = QMessageBox.question(
                self,
                "Recovery File Found",
                f"A recovery file was found from {self.format_file_time(latest_autosave)}.\n\n"
                f"Would you like to recover your work?\n\n"
                f"File: {latest_autosave.name}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.recover_from_file(latest_autosave)
            else:
                # Clean up old autosave files if user doesn't want to recover
                self.cleanup_all_autosaves()
                
        except Exception as e:
            print(f"Error checking for recovery files: {e}")
    
    def format_file_time(self, file_path: Path) -> str:
        """Format file modification time for display."""
        import time
        from datetime import datetime
        
        timestamp = file_path.stat().st_mtime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def recover_from_file(self, autosave_path: Path):
        """Recover project from autosave file."""
        try:
            # Load the autosave project
            recovered_project = Project.load(autosave_path)
            if not recovered_project:
                QMessageBox.critical(self, "Recovery Failed", "Failed to load recovery file.")
                return
            
            # Set as current project
            self.current_project = recovered_project
            
            # Load project data into UI
            self.load_project_to_ui(recovered_project)
            
            # Update UI
            self.update_window_title()
            
            # Update status
            self.statusBar().showMessage(f"Recovered from: {autosave_path.name}")
            
            # Clean up the recovered autosave file
            autosave_path.unlink()
            
            QMessageBox.information(
                self,
                "Recovery Successful",
                "Your work has been successfully recovered from the autosave file."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Recovery Failed",
                f"Failed to recover from autosave file:\n{str(e)}"
            )
    
    def cleanup_all_autosaves(self):
        """Clean up all autosave files."""
        try:
            if self.app_settings.temp_directory.exists():
                autosave_files = list(self.app_settings.temp_directory.glob("autosave_*.dsproj"))
                for file in autosave_files:
                    file.unlink()
        except Exception as e:
            print(f"Error cleaning up autosaves: {e}")
    
    def get_project_version_from_file(self, file_path: Path) -> Optional[str]:
        """Get the original version from a project file without loading it."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
                return data.get('version', '1.0.0')
        except Exception:
            return None
    
    def show_migration_dialog(self, from_version: str, to_version: str):
        """Show migration dialog to inform user about version changes."""
        # Get migration changes based on version
        changes = self.get_migration_changes(from_version, to_version)
        
        dialog = MigrationDialog(from_version, to_version, changes, self)
        dialog.exec()
    
    def get_migration_changes(self, from_version: str, to_version: str) -> List[str]:
        """Get list of changes applied during migration."""
        changes = []
        
        if from_version == "1.0.0":
            changes.append("Added round robin groups support")
            changes.append("Enhanced project structure for future features")
        
        if from_version in ["1.0.0", "1.1.0"]:
            changes.append("Added autosave functionality")
            changes.append("Enhanced settings management")
        
        if from_version in ["1.0.0", "1.1.0", "1.2.0"]:
            changes.append("Added visual indicators and enhanced UI")
            changes.append("Improved project status tracking")
        
        if not changes:
            changes.append("Updated project format for compatibility")
        
        return changes
    
    def show_about(self):
        """Show About dialog."""
        QMessageBox.about(
            self,
            "About DecentSampler Library Creator",
            "<h3>DecentSampler Library Creator</h3>"
            "<p>Version 1.0.0</p>"
            "<p>A professional tool for creating DecentSampler (.dspreset) files with advanced sample mapping and round robin support.</p>"
            "<p><b>Author:</b> Caio Dettmar</p>"
            "<p><b>GitHub:</b> <a href='https://github.com/caiodettmar/DecentSampler-Library-Creator'>https://github.com/caiodettmar/DecentSampler-Library-Creator</a></p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Advanced sample mapping with visual keyboard</li>"
            "<li>Round robin group management</li>"
            "<li>Project file management with autosave</li>"
            "<li>Real-time XML preview</li>"
            "<li>Professional workflow tools</li>"
            "</ul>"
            "<p>Built with PySide6 and Python</p>"
        )
    
    def show_version_info(self):
        """Show version information dialog."""
        from project_manager import ProjectVersion
        
        version_info = f"""
<h3>Version Information</h3>
<p><b>Current Application Version:</b> 1.0.0</p>
<p><b>Minimum Supported Project Version:</b> {ProjectVersion.MIN_SUPPORTED_VERSION}</p>

<h4>Version History:</h4>
<ul>
<li><b>1.0.0:</b> Initial version with basic project management</li>
</ul>

<h4>Compatibility:</h4>
<p>This application can open and migrate projects from version 1.0.0 and later.</p>
<p>Projects are automatically migrated to the current version when opened.</p>

<h4>Author:</h4>
<p><b>Developer:</b> Caio Dettmar</p>
<p><b>GitHub:</b> <a href='https://github.com/caiodettmar/DecentSampler-Library-Creator'>https://github.com/caiodettmar/DecentSampler-Library-Creator</a></p>
"""
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Version Information")
        msg_box.setText(version_info)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec()
    
    def new_project(self):
        """Create a new project."""
        if self.check_unsaved_changes():
            return
        
        # Create new project
        self.current_project = Project()
        
        # Reset UI to default state
        self.reset_ui_to_defaults()
        
        # Mark as modified since it's a new unsaved project
        self.current_project.mark_modified()
        
        # Update window title
        self.update_window_title()
        
        # Update status
        self.statusBar().showMessage("New project created")
        
        # Update recent projects menu
        self.update_recent_projects_menu()
    
    def open_project(self):
        """Open an existing project."""
        if self.check_unsaved_changes():
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "DecentSampler Project (*.dsproj);;All Files (*)"
        )
        
        if file_path:
            self.open_project_file(Path(file_path))
    
    def open_project_file(self, file_path: Path):
        """Open a project from file path."""
        if not file_path.exists():
            QMessageBox.warning(self, "File Not Found", f"The project file does not exist:\n{file_path}")
            self.app_settings.remove_recent_project(str(file_path))
            self.update_recent_projects_menu()
            return
        
        try:
            # Load project
            project = Project.load(file_path)
            if not project:
                QMessageBox.critical(self, "Error", f"Failed to load project:\n{file_path}")
                return
            
            # Check if migration was performed
            original_version = self.get_project_version_from_file(file_path)
            if original_version and original_version != project.version:
                self.show_migration_dialog(original_version, project.version)
            
            # Set as current project
            self.current_project = project
            
            # Load project data into UI
            self.load_project_to_ui(project)
            
            # Add to recent projects
            self.app_settings.add_recent_project(str(file_path))
            
            # Update UI
            self.update_window_title()
            self.update_recent_projects_menu()
            
            # Update status
            self.statusBar().showMessage(f"Project loaded: {file_path.name}")
            
        except ValueError as e:
            # Handle version compatibility errors
            QMessageBox.critical(self, "Version Incompatible", f"Cannot load project:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project:\n{str(e)}")
    
    def save_project(self):
        """Save the current project."""
        if not self.current_project:
            self.save_project_as()
            return
        
        if not self.current_project.project_path:
            self.save_project_as()
            return
        
        # Save current UI state to project
        self.save_ui_to_project()
        
        # Save project
        if self.current_project.save():
            self.statusBar().showMessage(f"Project saved: {self.current_project.project_path.name}")
            self.update_window_title()
            
            # Show success message
            QMessageBox.information(
                self,
                "Project Saved",
                f"Project saved successfully to:\n{self.current_project.project_path}"
            )
        else:
            QMessageBox.critical(self, "Error", "Failed to save project")
    
    def save_project_as(self):
        """Save the current project with a new name."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project As",
            "",
            "DecentSampler Project (*.dsproj);;All Files (*)"
        )
        
        if file_path:
            # Create new project if none exists
            if not self.current_project:
                self.current_project = Project()
            
            # Set project path
            self.current_project.project_path = Path(file_path)
            
            # Save current UI state to project
            self.save_ui_to_project()
            
            # Save project
            if self.current_project.save():
                # Add to recent projects
                self.app_settings.add_recent_project(str(file_path))
                
                # Update UI
                self.update_window_title()
                self.update_recent_projects_menu()
                self.statusBar().showMessage(f"Project saved: {file_path}")
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Project Saved",
                    f"Project saved successfully to:\n{file_path}"
                )
            else:
                QMessageBox.critical(self, "Error", "Failed to save project")
    
    def clear_recent_projects(self):
        """Clear the recent projects list."""
        reply = QMessageBox.question(
            self,
            "Clear Recent Projects",
            "Are you sure you want to clear the recent projects list?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.app_settings.recent_projects.clear()
            self.update_recent_projects_menu()
            self.statusBar().showMessage("Recent projects cleared")
    
    def check_unsaved_changes(self) -> bool:
        """Check for unsaved changes and prompt user if needed."""
        if not self.current_project or not self.current_project.is_modified:
            return False
        
        # Get project name for the dialog
        project_name = "Untitled Project"
        if self.current_project.project_path:
            project_name = self.current_project.project_path.stem
        elif self.current_project.decent_preset:
            project_name = self.current_project.decent_preset.preset_name or "Untitled Project"
        
        # Create informative message
        message = f"The project '{project_name}' has unsaved changes.\n\n"
        message += "What would you like to do?"
        
        # Create custom dialog with better buttons
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Unsaved Changes")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Warning)
        
        # Add custom buttons
        save_btn = msg_box.addButton("Save", QMessageBox.AcceptRole)
        discard_btn = msg_box.addButton("Don't Save", QMessageBox.DestructiveRole)
        cancel_btn = msg_box.addButton("Cancel", QMessageBox.RejectRole)
        
        # Set default button
        msg_box.setDefaultButton(save_btn)
        
        # Show dialog
        msg_box.exec()
        clicked_button = msg_box.clickedButton()
        
        if clicked_button == save_btn:
            # Try to save, return True if save was cancelled
            if not self.current_project.project_path:
                # No project path, need to use Save As
                self.save_project_as()
                return False
            else:
                # Save to existing path
                if self.current_project.save():
                    self.statusBar().showMessage(f"Project saved: {self.current_project.project_path.name}")
                    return False
                else:
                    # Save failed, ask user what to do
                    return self.handle_save_failure()
        elif clicked_button == discard_btn:
            return False
        else:  # Cancel
            return True
    
    def handle_save_failure(self) -> bool:
        """Handle save failure and ask user what to do."""
        reply = QMessageBox.question(
            self,
            "Save Failed",
            "Failed to save the project. Would you like to try saving with a different name?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.save_project_as()
            return False
        else:
            return True
    
    def reset_ui_to_defaults(self):
        """Reset UI to default state for new project."""
        # Clear preset information
        self.preset_name_edit.clear()
        self.author_edit.clear()
        self.category_edit.clear()
        self.description_edit.clear()
        self.samples_path_edit.setText("Samples")
        self.min_version_edit.setText("0")
        
        # Reset global attributes
        self.volume_edit.setText("1.0")
        self.global_tuning_edit.setText("0.0")
        self.glide_time_edit.setText("0.0")
        self.glide_mode_combo.setCurrentText("legato")
        self.global_round_robin_checkbox.setChecked(False)
        self.global_seq_mode_combo.setCurrentText("always")
        self.global_seq_length_edit.setText("0")
        
        # Clear sample mapping
        if hasattr(self, 'sample_mapping'):
            self.sample_mapping.set_sample_groups([])
        
        # Clear round robin groups
        if hasattr(self, 'round_robin_manager'):
            self.round_robin_manager.set_round_robin_groups({})
        
        # Update XML
        self.update_xml_live()
        
        # Update status widgets to show clean state
        self.update_status_widgets()
    
    def load_project_to_ui(self, project: Project):
        """Load project data into UI."""
        if not project.decent_preset:
            return
        
        preset = project.decent_preset
        
        # Load preset information
        self.preset_name_edit.setText(preset.preset_name)
        self.author_edit.setText(preset.author)
        self.category_edit.setText(preset.category)
        self.description_edit.setPlainText(preset.description)
        self.samples_path_edit.setText(preset.samples_path)
        
        # Load UI state
        ui_state = project.ui_state
        self.min_version_edit.setText(ui_state.get('min_version', '0'))
        self.volume_edit.setText(ui_state.get('volume', '1.0'))
        self.global_tuning_edit.setText(ui_state.get('global_tuning', '0.0'))
        self.glide_time_edit.setText(ui_state.get('glide_time', '0.0'))
        self.glide_mode_combo.setCurrentText(ui_state.get('glide_mode', 'legato'))
        
        # Global round robin settings
        global_rr_enabled = ui_state.get('global_round_robin_enabled', False)
        self.global_round_robin_checkbox.setChecked(global_rr_enabled)
        self.global_seq_mode_combo.setCurrentText(ui_state.get('global_seq_mode', 'always'))
        self.global_seq_length_edit.setText(ui_state.get('global_seq_length', '0'))
        
        # Load sample groups into mapping widget
        if hasattr(self, 'sample_mapping'):
            self.sample_mapping.set_sample_groups(preset.sample_groups)
        
        # Load round robin groups
        if hasattr(self, 'round_robin_manager'):
            self.round_robin_manager.set_round_robin_groups(project.round_robin_groups)
        
        # Update XML
        self.update_xml_live()
    
    def save_ui_to_project(self):
        """Save current UI state to project."""
        if not self.current_project:
            return
        
        # Create DecentPreset from current UI
        preset = self.create_preset()
        self.current_project.set_decent_preset(preset)
        
        # Save UI state
        self.current_project.ui_state.update({
            'current_tab': 0,  # Could be enhanced to remember current tab
            'xml_wrap_enabled': self.wrap_checkbox.isChecked(),
            'global_round_robin_enabled': self.global_round_robin_checkbox.isChecked(),
            'preset_name': self.preset_name_edit.text(),
            'author': self.author_edit.text(),
            'category': self.category_edit.text(),
            'description': self.description_edit.toPlainText(),
            'samples_path': self.samples_path_edit.text(),
            'min_version': self.min_version_edit.text(),
            'volume': self.volume_edit.text(),
            'global_tuning': self.global_tuning_edit.text(),
            'glide_time': self.glide_time_edit.text(),
            'glide_mode': self.glide_mode_combo.currentText(),
            'global_seq_mode': self.global_seq_mode_combo.currentText(),
            'global_seq_length': self.global_seq_length_edit.text()
        })
        
        # Save round robin groups
        if hasattr(self, 'round_robin_manager'):
            self.current_project.round_robin_groups = self.round_robin_manager.get_round_robin_groups()
    
    def update_window_title(self):
        """Update window title with project name and modified status."""
        if self.current_project:
            title = f"DecentSampler Library Creator - {self.current_project.get_title()}"
        else:
            title = "DecentSampler Library Creator - Untitled Project"
        
        self.setWindowTitle(title)
        self.update_status_widgets()
    
    def closeEvent(self, event):
        """Handle application close event."""
        if self.check_unsaved_changes():
            event.ignore()
        else:
            # Create final autosave if project is modified
            if self.current_project and self.current_project.is_modified:
                try:
                    self.current_project.create_autosave()
                except Exception as e:
                    print(f"Error creating final autosave: {e}")
            
            # Save settings before closing
            self.app_settings.save_to_file(self.settings_file)
            event.accept()


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
