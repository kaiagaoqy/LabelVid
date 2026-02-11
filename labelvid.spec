# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for LabelVid
Build with: pyinstaller labelvid.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Get the project root
project_root = Path(SPECPATH)

# Collect data files
datas = []

# Add any icon or resource files if they exist
icon_path = project_root / 'labelvid' / 'icons'
if icon_path.exists():
    datas.append((str(icon_path), 'labelvid/icons'))

# Hidden imports for PyQt5 and other dependencies
hiddenimports = [
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtMultimedia',
    'PyQt5.sip',
    'cv2',
    'numpy',
    'PIL',
    'PIL.Image',
    'loguru',
    'natsort',
    'labelvid',
    'labelvid.app',
    'labelvid.widgets',
    'labelvid.widgets.canvas',
    'labelvid.widgets.label_dialog',
    'labelvid.widgets.clip_list_widget',
    'labelvid.widgets.clip_timeline_widget',
    'labelvid.utils',
    'labelvid.label_file',
    'labelvid.shape',
]

# Optional: Add SAM/Whisper imports if available
try:
    import osam
    hiddenimports.extend([
        'osam',
        'imgviz',
        'labelvid._automation',
    ])
except ImportError:
    pass

try:
    import whisper
    hiddenimports.extend([
        'whisper',
        'labelvid._whisper',
        'labelvid._whisper._transcriber',
    ])
except ImportError:
    pass

a = Analysis(
    ['run.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LabelVid',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if available: 'labelvid/icons/app.ico'
)

# For macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='LabelVid.app',
        icon=None,  # Add icon path here if available: 'labelvid/icons/app.icns'
        bundle_identifier='com.labelvid.app',
        info_plist={
            'CFBundleName': 'LabelVid',
            'CFBundleDisplayName': 'LabelVid',
            'CFBundleVersion': '0.1.0',
            'CFBundleShortVersionString': '0.1.0',
            'NSHighResolutionCapable': True,
        },
    )
