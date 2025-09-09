# DecentSampler Library Creator

**Version 1.0.0** | **Author**: Caio Dettmar | **GitHub**: [DecentSampler-Library-Creator](https://github.com/caiodettmar/DecentSampler-Library-Creator)

A professional Python GUI application for creating DecentSampler (.dspreset) files with advanced project management, round robin support, and comprehensive sample mapping tools. Create professional sample libraries with ease!

## ✨ Key Features

### 🎵 **Professional Sample Management**
- **Multi-Tab Interface**: Organized workflow with Sample Mapping, Library Information, and XML Preview
- **Advanced Sample Mapping**: Professional table view with visual piano keyboard for precise sample assignment
- **Real-time XML Preview**: Live XML generation with syntax highlighting and automatic updates
- **Audio Playback**: Built-in audio player with volume control and pitch adjustment for sample testing
- **Drag & Drop Support**: Intuitive file management with visual feedback

### 🔄 **Round Robin System**
- **Auto-Detection**: Automatically detect round robin patterns from filenames (#1, #2, etc.)
- **Manual Group Creation**: Create and manage round robin groups with custom settings
- **Visual Management**: Tree view interface for organizing round robin samples
- **XML Integration**: Seamless integration with DecentSampler XML output

### 💾 **Project Management**
- **Complete Project System**: Save and load entire projects with all settings and samples
- **Autosave & Recovery**: Automatic backup system with crash recovery
- **Recent Projects**: Quick access to recently opened projects
- **Version Management**: Project versioning with migration support
- **Portable Projects**: Relative paths ensure projects work across different systems

### 🎹 **Advanced Audio Features**
- **Pitch Adjustment**: Automatic pitch shifting for samples played on different keys
- **Volume Control**: Integrated volume slider with mute/unmute functionality
- **Multiple Playback Methods**: QMediaPlayer with fallback support
- **Real-time Feedback**: Status messages for all audio operations

### 📁 **Export Options**
- **Preset Export**: Export as .dspreset files with proper XML formatting
- **Package Export**: Create compressed ZIP packages with samples and preset files
- **Standalone Executable**: Build system for creating distributable applications
- **Professional Installer**: NSIS-based installer for easy distribution

## 📋 Requirements

### **System Requirements**
- **Python 3.8+** (for development)
- **Windows 10/11** (for standalone executable)
- **50-100 MB** disk space (for standalone executable)

### **Python Dependencies**
- **PySide6** - Modern Qt GUI framework
- **lxml** - XML processing and generation
- **pathlib** - Modern file path handling (built-in)
- **json** - Project serialization (built-in)

### **Optional Dependencies**
- **pygame** - Enhanced audio playback
- **numpy** - Audio processing
- **sounddevice** - Low-latency audio
- **PIL/Pillow** - Icon creation

## 🚀 Installation

### **Option 1: Standalone Executable (Recommended)**
1. Download `DecentSamplerLibraryCreator_Setup.exe` from releases
2. Run the installer and follow the setup wizard
3. Launch from Start Menu or desktop shortcut

### **Option 2: Python Development Setup**
1. **Clone the repository:**
   ```bash
   git clone https://github.com/caiodettmar/DecentSampler-Library-Creator.git
   cd DecentSampler-Library-Creator
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv ds_creator_env
   ```

3. **Activate virtual environment:**
   - **Windows**: `ds_creator_env\Scripts\activate`
   - **Linux/Mac**: `source ds_creator_env/bin/activate`

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application:**
   ```bash
   # Option 1: Direct launch
   python main.py
   
   # Option 2: Using launcher script
   python run.py
   
   # Option 3: Windows batch file
   run.bat
   ```

## 🎯 Usage Guide

### **Quick Start**
1. **Launch the application** (standalone executable or Python script)
2. **Create a new project** or open an existing one
3. **Add sample files** using the "➕ Add Sample" button
4. **Configure sample properties** in the table view
5. **Set library information** (name, author, description)
6. **Export your preset** using File → Export → Export Preset (.dspreset)

### **Complete Workflow**

#### **1. Project Management**
- **New Project**: File → New Project (resets all data)
- **Open Project**: File → Open Project (loads .dsproj files)
- **Save Project**: File → Save Project (saves current work)
- **Recent Projects**: Quick access to recently opened projects

#### **2. Sample Management**
- **Add Samples**: Click "➕ Add Sample" to select audio files
- **Auto-Mapping**: Samples are automatically mapped based on filename patterns
- **Manual Configuration**: Edit root note, note range, and velocity range in the table
- **Visual Keyboard**: Click piano keys to test sample playback with pitch adjustment

#### **3. Round Robin Setup**
- **Auto-Detection**: Automatically detect round robin patterns (#1, #2, etc.)
- **Manual Groups**: Create custom round robin groups
- **Group Management**: Organize samples into round robin sequences
- **XML Integration**: Round robin groups are automatically included in XML output

#### **4. Library Configuration**
- **Preset Information**: Set name, author, description, category
- **Global Settings**: Configure volume, tuning, glide time, and mode
- **Version Requirements**: Set minimum DecentSampler version
- **Samples Path**: Define relative path for sample files

#### **5. Export Options**
- **Export Preset**: File → Export → Export Preset (.dspreset) - Single preset file
- **Export Package**: File → Export → Export Package (.zip) - Preset with samples
- **Live XML Preview**: Real-time XML generation with syntax highlighting

### **Advanced Features**

#### **Audio Playback**
- **Volume Control**: Adjust playback volume with slider above piano
- **Mute/Unmute**: Toggle audio with mute button
- **Pitch Adjustment**: Samples automatically pitch-shift when played on different keys
- **Status Messages**: Real-time feedback for audio operations

#### **Project Features**
- **Autosave**: Automatic backup every 5 minutes (configurable)
- **Crash Recovery**: Recover unsaved work on application restart
- **Portable Projects**: Projects work across different systems
- **Version Management**: Automatic project versioning and migration

## 📁 Project Structure

```
DecentSampler-Library-Creator/
├── 📱 src/                           # Source Code
│   ├── decent_sampler_gui.py         # Main GUI application
│   ├── decent_sampler.py             # Core preset generation classes
│   ├── sample_mapping.py             # Advanced sample mapping & round robin
│   └── project_manager.py            # Project management system
├── 🏗️ build/                         # Build System
│   ├── build_standalone.py           # Main build script
│   ├── build_config.py               # Build configuration
│   ├── build_launcher.py              # Interactive build launcher
│   ├── create_icon.py                # Icon creation utility
│   └── build.bat                      # Windows build script
├── 📚 docs/                          # Documentation
│   ├── ROADMAP.md                    # Development roadmap
│   ├── ROUND_ROBIN_README.md         # Round robin documentation
│   └── BUILD_INSTRUCTIONS.md         # Build documentation
├── 🧪 tests/                         # Testing Files
│   ├── test_round_robin.py           # Round robin testing
│   └── test_hash_pattern.py          # Pattern testing
├── 🛠️ utils/                         # Utility Scripts
│   ├── run_gui.py                    # GUI launcher script
│   └── run_gui.bat                   # Windows batch launcher
├── 🚀 dist/                          # Distribution Output
│   └── DecentSamplerLibraryCreator.exe
└── 📄 Root Files                     # Project Root
    ├── main.py                       # Main application launcher
    ├── run.py                        # Simple launcher script
    ├── run.bat                       # Windows batch launcher
    ├── README.md                     # This File
    ├── requirements.txt              # Python dependencies
    ├── PROJECT_STRUCTURE.md          
    ├── installer.nsi                 # NSIS installer script
    ├── version_info.txt              # Version information
    └── DecentSamplerLibraryCreator.spec
```

## 🎵 Supported Audio Formats

The application supports all audio formats compatible with DecentSampler:
- **WAV** (.wav) - Uncompressed audio
- **AIFF** (.aif, .aiff) - Apple audio format
- **FLAC** (.flac) - Lossless compression
- **MP3** (.mp3) - Compressed audio

## 🔗 DecentSampler Integration

Generated .dspreset files are fully compatible with:
- **DecentSampler VST** plugin (Windows/macOS/Linux)
- **DecentSampler AU** plugin (macOS)
- **DecentSampler standalone** application

## 🏗️ Building from Source

### **Create Standalone Executable**
```bash
# Install build dependencies
pip install pyinstaller

# Navigate to build directory
cd build

# Run build script
python build_standalone.py

# Or use interactive launcher
python build_launcher.py
```

### **Create Windows Installer**
1. Install NSIS from [nsis.sourceforge.io](https://nsis.sourceforge.io/)
2. Compile installer: `makensis installer.nsi`
3. Get installer: `DecentSamplerLibraryCreator_Setup.exe`

## 🎨 Application Assets

The application includes custom branding assets:

- **`icon.ico`** - Windows application icon (favicon)
- **`assets/DSLC Logo.png`** - Main application logo displayed in the GUI
- **`assets/app_icon_*.png`** - Various icon sizes for different uses

The logo replaces the text title in the main application window, providing a professional branded appearance.

See [BUILD_INSTRUCTIONS.md](docs/BUILD_INSTRUCTIONS.md) for detailed build documentation.

## 🐛 Troubleshooting

### **Common Issues**
- **Audio not playing**: Check volume slider and mute button
- **Samples not loading**: Verify file paths and audio format support
- **XML not updating**: Use refresh buttons in each tab
- **Project not saving**: Check file permissions and disk space

### **Performance Tips**
- Use WAV files for best performance
- Keep sample files under 100MB each
- Close other audio applications while testing
- Use SSD storage for better loading times

## 📄 License

This project is provided as-is for educational and personal use.

## 🤝 Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### **Development Guidelines**
- Follow PEP 8 Python style guidelines
- Add tests for new features
- Update documentation for changes
- Test on multiple Windows versions

## 📞 Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/caiodettmar/DecentSampler-Library-Creator/issues)
- **Documentation**: Check [ROADMAP.md](ROADMAP.md) for development plans
- **Community**: Join discussions in GitHub Discussions

---

**Made with ❤️ by [Caio Dettmar](https://github.com/caiodettmar)**
