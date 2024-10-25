# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['PoleIO-Main.py'],
    pathex=['/Users/tobydz/Documents/Documents - Tobys MacBook Pro/_CODE/Pole.IO/venv/lib/python3.13/site-packages/'],
    binaries=[('/Users/tobydz/Documents/Documents - Tobys MacBook Pro/_CODE/Pole.IO/venv/lib/python3.13/site-packages/PyQt5/Qt5/plugins/platforms/libqcocoa.dylib', 'PyQt5/Qt5/plugins/platforms')],
    datas=[('/Users/tobydz/Documents/Documents - Tobys MacBook Pro/_CODE/Pole.IO/SRC/PoleIO-UI.ui', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='PoleIO',
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
    name='PoleIO.app',
    icon=None,
    bundle_identifier=None,
)
