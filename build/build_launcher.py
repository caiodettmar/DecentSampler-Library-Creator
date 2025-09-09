#!/usr/bin/env python3
"""
Build launcher for DecentSampler Library Creator.
Provides an interactive interface for building the standalone application.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed."""
    required_packages = ['PySide6', 'lxml', 'pyinstaller']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install " + " ".join(missing_packages))
        return False
    
    return True

def create_icon():
    """Create application icon if it doesn't exist."""
    if not os.path.exists('icon.ico'):
        print("Creating application icon...")
        try:
            subprocess.run([sys.executable, 'create_icon.py'], check=True)
            print("Icon created successfully!")
        except subprocess.CalledProcessError:
            print("Warning: Could not create icon, building without icon")
    else:
        print("Icon file already exists")

def build_executable():
    """Build the standalone executable."""
    print("Building standalone executable...")
    try:
        subprocess.run([sys.executable, 'build_standalone.py'], check=True)
        print("Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False

def create_installer():
    """Create Windows installer using NSIS."""
    if not os.path.exists('installer.nsi'):
        print("Installer script not found. Please run build_standalone.py first.")
        return False
    
    print("Creating Windows installer...")
    try:
        # Check if NSIS is available
        subprocess.run(['makensis', '--version'], check=True, capture_output=True)
        
        # Create installer
        subprocess.run(['makensis', 'installer.nsi'], check=True)
        print("Installer created successfully!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("NSIS not found or installer creation failed.")
        print("Please install NSIS from https://nsis.sourceforge.io/")
        return False

def show_menu():
    """Show interactive menu."""
    while True:
        print("\n" + "="*60)
        print("DecentSampler Library Creator - Build Launcher")
        print("="*60)
        print("1. Check Requirements")
        print("2. Create Icon")
        print("3. Build Executable")
        print("4. Create Installer")
        print("5. Full Build (All Steps)")
        print("6. Exit")
        print("="*60)
        
        choice = input("Enter your choice (1-6): ").strip()
        
        if choice == '1':
            if check_requirements():
                print("All requirements are satisfied!")
            else:
                print("Please install missing packages and try again.")
        
        elif choice == '2':
            create_icon()
        
        elif choice == '3':
            if check_requirements():
                build_executable()
            else:
                print("Please install missing packages first.")
        
        elif choice == '4':
            create_installer()
        
        elif choice == '5':
            print("Starting full build process...")
            if not check_requirements():
                print("Please install missing packages first.")
                continue
            
            create_icon()
            if build_executable():
                create_installer()
                print("\nFull build process completed!")
                print("Check the 'dist' folder for your executable.")
        
        elif choice == '6':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter 1-6.")

def main():
    """Main function."""
    print("DecentSampler Library Creator - Build Launcher")
    print("This tool will help you build a standalone executable and installer.")
    
    # Check if we're in the right directory
    if not os.path.exists('decent_sampler_gui.py'):
        print("Error: Please run this script from the project root directory.")
        print("Make sure 'decent_sampler_gui.py' is in the current directory.")
        return False
    
    show_menu()
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBuild process interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
