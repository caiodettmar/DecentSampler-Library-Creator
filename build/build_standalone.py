#!/usr/bin/env python3
"""
Build script for creating standalone executable of DecentSampler Library Creator.
This script uses PyInstaller to create a standalone executable with all dependencies.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from build_config import BuildConfig

def clean_build_dirs():
    """Clean previous build directories."""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)

def create_version_info():
    """Create version information for the executable."""
    version_info = BuildConfig.get_version_info()
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    print("Created version_info.txt")

def build_executable():
    """Build the standalone executable using PyInstaller."""
    print("Building standalone executable...")
    
    # Build PyInstaller command from configuration
    cmd = ['pyinstaller']
    
    # Add options from configuration
    if BuildConfig.PYINSTALLER_OPTIONS.get('onefile'):
        cmd.append('--onefile')
    if BuildConfig.PYINSTALLER_OPTIONS.get('windowed'):
        cmd.append('--windowed')
    if BuildConfig.PYINSTALLER_OPTIONS.get('clean'):
        cmd.append('--clean')
    if BuildConfig.PYINSTALLER_OPTIONS.get('noconfirm'):
        cmd.append('--noconfirm')
    
    cmd.extend(['--name', BuildConfig.OUTPUT_NAME])
    cmd.extend(['--version-file', 'version_info.txt'])
    
    # Add icon if it exists
    if os.path.exists(BuildConfig.ICON_FILE):
        cmd.extend(['--icon', BuildConfig.ICON_FILE])
    else:
        print("Warning: icon.ico not found, building without icon")
    
    # Add data files
    for src, dst in BuildConfig.PYINSTALLER_OPTIONS.get('add_data', []):
        cmd.extend(['--add-data', f'{src};{dst}'])
    
    # Add hidden imports
    for module in BuildConfig.PYINSTALLER_OPTIONS.get('hidden_imports', []):
        cmd.extend(['--hidden-import', module])
    
    # Add exclude modules
    for module in BuildConfig.PYINSTALLER_OPTIONS.get('exclude_modules', []):
        cmd.extend(['--exclude-module', module])
    
    # Add main script (from parent directory)
    cmd.append(f'../{BuildConfig.MAIN_SCRIPT}')
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_installer_script():
    """Create NSIS installer script."""
    installer_script = BuildConfig.get_nsis_script()
    
    with open('installer.nsi', 'w', encoding='utf-8') as f:
        f.write(installer_script)
    print("Created installer.nsi")

def create_build_batch():
    """Create Windows batch file for easy building."""
    batch_content = '''@echo off
echo Building DecentSampler Library Creator...
echo.

REM Activate virtual environment
call ds_creator_env\\Scripts\\activate

REM Install build dependencies
echo Installing build dependencies...
pip install pyinstaller auto-py-to-exe

REM Run the build script
echo Running build script...
python build_standalone.py

echo.
echo Build complete! Check the dist folder for the executable.
echo.
pause'''
    
    with open('build.bat', 'w', encoding='utf-8') as f:
        f.write(batch_content)
    print("Created build.bat")

def main():
    """Main build process."""
    print("DecentSampler Library Creator - Standalone Build Script")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('../src/decent_sampler_gui.py'):
        print("Error: src/decent_sampler_gui.py not found. Please run this script from the build directory.")
        return False
    
    # Clean previous builds
    clean_build_dirs()
    
    # Create version info
    create_version_info()
    
    # Build executable
    if not build_executable():
        print("Build failed!")
        return False
    
    # Create installer script
    create_installer_script()
    
    # Create build batch file
    create_build_batch()
    
    print("\n" + "=" * 60)
    print("Build process completed successfully!")
    print("\nFiles created:")
    print("- dist/DecentSamplerLibraryCreator.exe (standalone executable)")
    print("- installer.nsi (NSIS installer script)")
    print("- build.bat (Windows build script)")
    print("- version_info.txt (version information)")
    print("\nTo create an installer:")
    print("1. Install NSIS (https://nsis.sourceforge.io/)")
    print("2. Right-click installer.nsi and select 'Compile NSIS Script'")
    print("3. Or run: makensis installer.nsi")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
