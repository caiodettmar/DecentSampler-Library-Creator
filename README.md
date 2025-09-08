# DecentSampler Library Creator

A Python GUI application for creating DecentSampler (.dspreset) files, featuring advanced round robin support and professional sample mapping tools.

## Features

### GUI Application
- **Multi-Tab Interface**: Organized tabs for sample management, library information, live XML preview, and advanced sample mapping
- **Sample Management**: Add multiple audio files and configure their properties
- **Library Information**: Set library name, author, description, category, and minimum version requirements
- **Real-time Editing**: Edit sample properties (root note, note range, velocity range) in real-time
- **Live XML Preview**: See XML updates in real-time as you make changes with syntax highlighting
- **Advanced Sample Mapping**: Professional table view and visual piano keyboard for precise sample assignment
- **Round Robin Support**: Create and manage round robin groups for natural sample variations
- **Auto-Mapping**: Intelligent root note extraction from filenames using common patterns
- **Round Robin Auto-Detection**: Automatically detect round robin patterns from filenames (#1, #2, etc.)
- **File Export**: Save presets as .dspreset files with proper XML formatting

## Requirements

- Python 3.8+
- PySide6 (for GUI)
- lxml (for XML generation)

## Installation

1. Clone or download this repository
2. Create a virtual environment:
   ```bash
   python -m venv ds_creator_env
   ```
3. Activate the virtual environment:
   - Windows: `ds_creator_env\Scripts\activate`
   - Linux/Mac: `source ds_creator_env/bin/activate`
4. Install dependencies:
   ```bash
   pip install PySide6 lxml
   ```

## Usage

### GUI Application

**Option 1: Run directly**
```bash
python decent_sampler_gui.py
```

**Option 2: Use the launcher script**
```bash
python run_gui.py
```

**Option 3: Use the batch file (Windows)**
```bash
run_gui.bat
```

#### GUI Workflow:
1. **Add Sample Files**: Click "Add Files..." to select audio files
2. **Configure Sample Properties**: Select a sample in the list to edit its properties:
   - Root Note: The note that plays at the original pitch
   - Note Range: The range of notes this sample responds to
   - Velocity Range: The velocity range this sample responds to
3. **Set Library Information**: Fill in the library name, author, description, category, and minimum version
4. **Live XML Preview**: See real-time XML updates in the right panel as you make changes
5. **Advanced Sample Mapping**: Use the bottom panel for professional sample assignment:
   - **Table View**: Edit sample properties in a spreadsheet-like interface
   - **Visual Keyboard**: Keyboard with highlights to indicate mapping.
   - **Auto-Mapping**: Extract root notes from filenames automatically
   - **Round Robin Groups**: Create and manage round robin groups for natural variations
   - **Sync Changes**: Apply mapping changes back to the main sample list
6. **Round Robin Management**: Use the "Round Robin by Group" tab to:
   - Create round robin groups from selected samples
   - Auto-detect round robin patterns from filenames
   - Configure round robin modes and sequence lengths
   - Preview round robin playback
7. **Save Preset**: Use "Save Preset..." to save as a .dspreset file

## File Structure

```
DecentSampler Library Creator/
├── decent_sampler.py          # Core classes for preset generation
├── decent_sampler_gui.py      # PySide6 GUI application
├── sample_mapping.py          # Advanced sample mapping and round robin functionality
├── run_gui.py                 # GUI launcher script
├── run_gui.bat               # Windows batch file launcher
├── README.md                 # This file
├── ROUND_ROBIN_README.md     # Round robin feature documentation
└── ds_creator_env/           # Virtual environment (created during setup)
```

## Supported Audio Formats

The application supports common audio formats that DecentSampler can load:
- WAV (.wav)
- AIFF (.aif, .aiff)
- FLAC (.flac)
- MP3 (.mp3)

## DecentSampler Integration

Generated .dspreset files are compatible with:
- DecentSampler VST plugin
- DecentSampler AU plugin (macOS)
- DecentSampler standalone application

## License

This project is provided as-is for educational and personal use.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.
