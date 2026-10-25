# -*- mode: python ; coding: utf-8 -*-
# PyInstaller's built-in PySide6 hooks collect the required Qt runtime/plugins.
# Avoid collect_submodules("PySide6"): it scans a very large package tree and
# makes CI builds unnecessarily slow.
a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SmartTV-Toolkit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
