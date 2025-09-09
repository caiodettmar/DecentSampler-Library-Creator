#!/usr/bin/env python3
"""
Test script for Round Robin functionality in DecentSampler Preset Creator

This script demonstrates the round robin features implemented:
1. Round Robin Dialog with seqMode, seqLength, and seqPosition controls
2. Round Robin Manager for managing round robin groups
3. Visual indicators on keyboard for round robin samples
4. Table view updates to show round robin information
5. Automatic round robin detection from filename patterns
6. XML generation with round robin attributes
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import Qt

# Add the current directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from decent_sampler import Sample, SampleGroup, DecentPreset
from sample_mapping import SampleMappingWidget, RoundRobinDialog, RoundRobinManager


class RoundRobinTestWindow(QMainWindow):
    """Test window for round robin functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Round Robin Test - DecentSampler Preset Creator")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("Round Robin Functionality Test")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Create sample mapping widget
        self.sample_mapping = SampleMappingWidget()
        layout.addWidget(self.sample_mapping)
        
        # Add test buttons
        self.add_test_samples()
        
        # Create round robin manager
        self.round_robin_manager = RoundRobinManager(self.sample_mapping)
        layout.addWidget(self.round_robin_manager)
        
        # Add status label
        self.status_label = QLabel("Ready - Add some sample files to test round robin functionality")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
    
    def add_test_samples(self):
        """Add some test samples to demonstrate round robin functionality."""
        # Create test samples with round robin patterns
        test_samples = [
            Sample(Path("test_samples/C4_rr1.wav"), root_note=60, low_note=60, high_note=60, seq_mode="round_robin", seq_position=1, seq_length=3),
            Sample(Path("test_samples/C4_rr2.wav"), root_note=60, low_note=60, high_note=60, seq_mode="round_robin", seq_position=2, seq_length=3),
            Sample(Path("test_samples/C4_rr3.wav"), root_note=60, low_note=60, high_note=60, seq_mode="round_robin", seq_position=3, seq_length=3),
            Sample(Path("test_samples/D4_1.wav"), root_note=62, low_note=62, high_note=62, seq_mode="round_robin", seq_position=1, seq_length=2),
            Sample(Path("test_samples/D4_2.wav"), root_note=62, low_note=62, high_note=62, seq_mode="round_robin", seq_position=2, seq_length=2),
            Sample(Path("test_samples/E4_round1.wav"), root_note=64, low_note=64, high_note=64, seq_mode="random", seq_position=1, seq_length=2),
            Sample(Path("test_samples/E4_round2.wav"), root_note=64, low_note=64, high_note=64, seq_mode="random", seq_position=2, seq_length=2),
            Sample(Path("test_samples/F4_alt1.wav"), root_note=65, low_note=65, high_note=65, seq_mode="true_random", seq_position=1, seq_length=3),
            Sample(Path("test_samples/F4_alt2.wav"), root_note=65, low_note=65, high_note=65, seq_mode="true_random", seq_position=2, seq_length=3),
            Sample(Path("test_samples/F4_alt3.wav"), root_note=65, low_note=65, high_note=65, seq_mode="true_random", seq_position=3, seq_length=3),
            Sample(Path("test_samples/G4_var1.wav"), root_note=67, low_note=67, high_note=67),  # No round robin
            Sample(Path("test_samples/G4_var2.wav"), root_note=67, low_note=67, high_note=67),  # No round robin
        ]
        
        # Add samples to the model
        for sample in test_samples:
            self.sample_mapping.model.samples.append(sample)
        
        # Rebuild the model
        self.sample_mapping.model._build_sample_list()
        self.sample_mapping.model.beginResetModel()
        self.sample_mapping.model.endResetModel()
        
        # Update keyboard display
        self.sample_mapping.update_keyboard_display()
        
        # Update status
        self.status_label.setText(f"Added {len(test_samples)} test samples. Try the Round Robin features!")
        self.status_label.setStyleSheet("color: #006600; font-weight: bold;")


def main():
    """Main function to run the test application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Round Robin Test")
    app.setApplicationVersion("1.0.0")
    
    # Create and show test window
    window = RoundRobinTestWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()