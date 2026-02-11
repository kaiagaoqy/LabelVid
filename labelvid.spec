# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=[],
    datas=[('/Users/kaiagao/miniconda3/envs/labelvid/lib/python3.14/site-packages/osam/_models', 'osam/_models'), ('/Users/kaiagao/miniconda3/envs/labelvid/lib/python3.14/site-packages/whisper/assets', 'whisper/assets')],
    hiddenimports=['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtMultimedia', 'PyQt5.sip', 'cv2', 'numpy', 'PIL', 'PIL.Image', 'loguru', 'natsort', 'osam', 'imgviz', 'whisper'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'IPython', 'jupyter', 'notebook'],
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
    name='LabelVid',
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
)
app = BUNDLE(
    exe,
    name='LabelVid.app',
    icon=None,
    bundle_identifier=None,
)
