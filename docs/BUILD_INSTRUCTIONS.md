# Build Instructions for DecentSampler Library Creator

This document provides comprehensive instructions for building a standalone executable and installer for the DecentSampler Library Creator application.

## Prerequisites

### Required Software
1. **Python 3.8+** - Download from [python.org](https://python.org)
2. **PyInstaller** - For creating standalone executables
3. **NSIS** - For creating Windows installers (optional)

### Required Python Packages
```bash
pip install PySide6 lxml pyinstaller
```

## Quick Build (Automated)

### Option 1: Using the Build Script
```bash
# Activate virtual environment
ds_creator_env\Scripts\activate

# Run the automated build script
python build_standalone.py
```

### Option 2: Using the Batch File (Windows)
```bash
# Double-click or run from command line
build.bat
```

## Manual Build Process

### Step 1: Prepare the Environment
```bash
# Create virtual environment (if not exists)
python -m venv ds_creator_env

# Activate virtual environment
# Windows:
ds_creator_env\Scripts\activate
# Linux/Mac:
source ds_creator_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Create Application Icon (Optional)
```bash
python create_icon.py
```

### Step 3: Build Standalone Executable
```bash
# Using PyInstaller directly
pyinstaller --onefile --windowed --name=DecentSamplerLibraryCreator --icon=icon.ico --version-file=version_info.txt --add-data="README.md;." --add-data="ROADMAP.md;." --hidden-import=PySide6.QtCore --hidden-import=PySide6.QtWidgets --hidden-import=PySide6.QtGui --hidden-import=PySide6.QtMultimedia --hidden-import=lxml --hidden-import=lxml.etree --hidden-import=lxml._elementpath --clean decent_sampler_gui.py
```

### Step 4: Create Windows Installer (Optional)

#### Install NSIS
1. Download NSIS from [nsis.sourceforge.io](https://nsis.sourceforge.io/)
2. Install NSIS

#### Create Installer
```bash
# Compile the NSIS script
makensis installer.nsi
```

## Build Configuration

The build process uses `build_config.py` for centralized configuration:

### Application Metadata
- **Name**: DecentSampler Library Creator
- **Version**: 1.0.0
- **Author**: Caio Dettmar
- **Description**: A professional tool for creating DecentSampler preset files

### PyInstaller Options
- **One File**: Creates a single executable file
- **Windowed**: No console window (GUI application)
- **Clean**: Cleans cache before building
- **Hidden Imports**: Includes all required PySide6 and lxml modules

### Distribution Files
- README.md
- ROADMAP.md
- requirements.txt

## Output Files

After successful build, you'll find:

### Executable
- `dist/DecentSamplerLibraryCreator.exe` - Standalone executable

### Installer Files
- `installer.nsi` - NSIS installer script
- `DecentSamplerLibraryCreator_Setup.exe` - Windows installer (after NSIS compilation)

### Build Artifacts
- `version_info.txt` - Version information for Windows executable
- `build/` - PyInstaller build directory
- `dist/` - Distribution directory

## Troubleshooting

### Common Issues

#### 1. PyInstaller Not Found
```bash
pip install pyinstaller
```

#### 2. Missing Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Icon File Issues
- The build will work without an icon file
- Create icon using `python create_icon.py`
- Or provide your own `icon.ico` file

#### 4. Large Executable Size
- This is normal for PySide6 applications
- The executable includes the entire Qt framework
- Typical size: 50-100 MB

#### 5. Antivirus False Positives
- Some antivirus software may flag PyInstaller executables
- This is a common false positive
- Add the executable to antivirus exclusions if needed

### Build Optimization

#### Reduce Executable Size
```bash
# Exclude unnecessary modules
pyinstaller --exclude-module=tkinter --exclude-module=matplotlib --exclude-module=numpy --exclude-module=scipy --exclude-module=pandas [other options]
```

#### Include Additional Files
```bash
# Add custom data files
pyinstaller --add-data="path/to/file;destination" [other options]
```

## Testing the Build

### Test Standalone Executable
1. Navigate to `dist/` directory
2. Run `DecentSamplerLibraryCreator.exe`
3. Verify all features work correctly
4. Test with sample files

### Test Installer
1. Run `DecentSamplerLibraryCreator_Setup.exe`
2. Follow installation wizard
3. Verify application launches from Start Menu
4. Test uninstallation

## Distribution

### File Structure for Distribution
```
DecentSamplerLibraryCreator_Release/
├── DecentSamplerLibraryCreator_Setup.exe  # Windows installer
├── DecentSamplerLibraryCreator.exe         # Standalone executable
├── README.md                               # User documentation
├── ROADMAP.md                              # Development roadmap
└── LICENSE                                 # License file
```

### Release Checklist
- [ ] Test executable on clean Windows system
- [ ] Verify all features work correctly
- [ ] Test installer and uninstaller
- [ ] Update version numbers
- [ ] Create release notes
- [ ] Package distribution files

## Advanced Configuration

### Custom Icon
Replace `icon.ico` with your own icon file (256x256 pixels recommended).

### Custom Version Information
Edit `build_config.py` to modify version information and metadata.

### Additional PyInstaller Options
Modify `BuildConfig.PYINSTALLER_OPTIONS` in `build_config.py` for additional options.

## Support

For build issues or questions:
- Check the [GitHub Issues](https://github.com/caiodettmar/DecentSampler-Library-Creator/issues)
- Review PyInstaller documentation
- Check NSIS documentation for installer issues
