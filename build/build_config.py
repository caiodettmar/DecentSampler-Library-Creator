#!/usr/bin/env python3
"""
Build configuration for DecentSampler Library Creator.
Contains all build settings and metadata.
"""

import os
from pathlib import Path

class BuildConfig:
    """Build configuration class."""
    
    # Application metadata
    APP_NAME = "DecentSampler Library Creator"
    APP_VERSION = "1.0.0"
    APP_AUTHOR = "Caio Dettmar"
    APP_DESCRIPTION = "A professional tool for creating DecentSampler preset files"
    APP_URL = "https://github.com/caiodettmar/DecentSampler-Library-Creator"
    
    # Build settings
    MAIN_SCRIPT = "src/decent_sampler_gui.py"
    OUTPUT_NAME = "DecentSamplerLibraryCreator"
    ICON_FILE = "../icon.ico"  # Will be created if not exists
    
    # PyInstaller settings
    PYINSTALLER_OPTIONS = {
        'onefile': True,
        'windowed': True,
        'clean': True,
        'noconfirm': True,
        'hidden_imports': [
            'PySide6.QtCore',
            'PySide6.QtWidgets', 
            'PySide6.QtGui',
            'PySide6.QtMultimedia',
            'lxml',
            'lxml.etree',
            'lxml._elementpath',
            'json',
            'pathlib',
            'tempfile',
            'shutil',
            'zipfile'
        ],
        'add_data': [
            ('../README.md', '.'),
            ('../docs/ROADMAP.md', 'docs/'),
            ('../requirements.txt', '.'),
            ('../assets/DSLC Logo.png', 'assets/')
        ],
        'exclude_modules': [
            'tkinter',
            'matplotlib',
            'numpy',
            'scipy',
            'pandas'
        ]
    }
    
    # NSIS installer settings
    INSTALLER_SETTINGS = {
        'install_size': 50000,  # KB
        'request_execution_level': 'admin',
        'install_dir': r'$PROGRAMFILES\DecentSampler Library Creator',
        'start_menu_folder': 'DecentSampler Library Creator',
        'registry_key': 'DecentSamplerLibraryCreator'
    }
    
    # Files to include in distribution
    DISTRIBUTION_FILES = [
        'README.md',
        'ROADMAP.md',
        'requirements.txt'
    ]
    
    @classmethod
    def get_version_info(cls):
        """Get version information for Windows executable."""
        return f'''# UTF-8
#
# Version information for {cls.APP_NAME}
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({cls.APP_VERSION.replace(".", ",")},0),
    prodvers=({cls.APP_VERSION.replace(".", ",")},0),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{cls.APP_AUTHOR}'),
        StringStruct(u'FileDescription', u'{cls.APP_DESCRIPTION}'),
        StringStruct(u'FileVersion', u'{cls.APP_VERSION}.0'),
        StringStruct(u'InternalName', u'{cls.OUTPUT_NAME}'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2024 {cls.APP_AUTHOR}'),
        StringStruct(u'OriginalFilename', u'{cls.OUTPUT_NAME}.exe'),
        StringStruct(u'ProductName', u'{cls.APP_NAME}'),
        StringStruct(u'ProductVersion', u'{cls.APP_VERSION}.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)'''
    
    @classmethod
    def get_nsis_script(cls):
        """Get NSIS installer script."""
        return f'''!define APPNAME "{cls.APP_NAME}"
!define COMPANYNAME "{cls.APP_AUTHOR}"
!define DESCRIPTION "{cls.APP_DESCRIPTION}"
!define VERSIONMAJOR {cls.APP_VERSION.split(".")[0]}
!define VERSIONMINOR {cls.APP_VERSION.split(".")[1]}
!define VERSIONBUILD {cls.APP_VERSION.split(".")[2]}
!define HELPURL "{cls.APP_URL}"
!define UPDATEURL "{cls.APP_URL}"
!define ABOUTURL "{cls.APP_URL}"
!define INSTALLSIZE {cls.INSTALLER_SETTINGS["install_size"]}

RequestExecutionLevel {cls.INSTALLER_SETTINGS["request_execution_level"]}
InstallDir "{cls.INSTALLER_SETTINGS["install_dir"]}"
Name "${{APPNAME}}"
outFile "{cls.OUTPUT_NAME}_Setup.exe"

!include LogicLib.nsh

page directory
page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${{If}} $0 != "admin"
    messageBox mb_iconstop "Administrator rights required!"
    setErrorLevel 740
    quit
${{EndIf}}
!macroend

function .onInit
    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
functionEnd

section "install"
    setOutPath $INSTDIR
    file "dist\\\\{cls.OUTPUT_NAME}.exe"
    file "..\\\\README.md"
    file "..\\\\docs\\\\ROADMAP.md"
    
    writeUninstaller "$INSTDIR\\\\uninstall.exe"
    
    createDirectory "$SMPROGRAMS\\\\${{APPNAME}}"
    createShortCut "$SMPROGRAMS\\\\${{APPNAME}}\\\\{cls.OUTPUT_NAME}.lnk" "$INSTDIR\\\\{cls.OUTPUT_NAME}.exe" "" "$INSTDIR\\\\{cls.OUTPUT_NAME}.exe"
    createShortCut "$SMPROGRAMS\\\\${{APPNAME}}\\\\Uninstall.lnk" "$INSTDIR\\\\uninstall.exe"
    
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "DisplayName" "${{APPNAME}}"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "UninstallString" "$\\\\"$INSTDIR\\\\uninstall.exe$\\\\""
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "InstallLocation" "$\\\\"$INSTDIR$\\\\""
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "DisplayIcon" "$\\\\"$INSTDIR\\\\{cls.OUTPUT_NAME}.exe$\\\\""
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "Publisher" "${{COMPANYNAME}}"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "HelpLink" "${{HELPURL}}"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "URLUpdateInfo" "${{UPDATEURL}}"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "URLInfoAbout" "${{ABOUTURL}}"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "DisplayVersion" "${{VERSIONMAJOR}}.${{VERSIONMINOR}}.${{VERSIONBUILD}}"
    WriteRegDWORD HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "VersionMajor" ${{VERSIONMAJOR}}
    WriteRegDWORD HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "VersionMinor" ${{VERSIONMINOR}}
    WriteRegDWORD HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "EstimatedSize" ${{INSTALLSIZE}}
sectionEnd

section "uninstall"
    delete "$INSTDIR\\\\{cls.OUTPUT_NAME}.exe"
    delete "$INSTDIR\\\\README.md"
    delete "$INSTDIR\\\\ROADMAP.md"
    delete "$INSTDIR\\\\uninstall.exe"
    rmDir "$INSTDIR"
    
    delete "$SMPROGRAMS\\\\${{APPNAME}}\\\\{cls.OUTPUT_NAME}.lnk"
    delete "$SMPROGRAMS\\\\${{APPNAME}}\\\\Uninstall.lnk"
    rmDir "$SMPROGRAMS\\\\${{APPNAME}}"
    
    DeleteRegKey HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}"
sectionEnd'''
