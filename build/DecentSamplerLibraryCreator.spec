# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['..\\src\\decent_sampler_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('../README.md', '.'), ('../docs/ROADMAP.md', 'docs/'), ('../requirements.txt', '.'), ('../assets/DSLC Logo.png', 'assets/')],
    hiddenimports=['PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui', 'PySide6.QtMultimedia', 'lxml', 'lxml.etree', 'lxml._elementpath', 'json', 'pathlib', 'tempfile', 'shutil', 'zipfile'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DecentSamplerLibraryCreator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon=['..\\icon.ico'],
)
