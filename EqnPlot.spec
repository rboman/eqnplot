# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path


PROJECT_ROOT = Path.cwd()
ICON_PATH = PROJECT_ROOT / "assets" / "eqnplot-icon.ico"
USE_UPX = os.environ.get("EQNPLOT_USE_UPX", "").lower() in {"1", "true", "yes", "on"}


a = Analysis(
    ["main.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[(str(ICON_PATH), "assets")] if ICON_PATH.exists() else [],
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
    [],
    exclude_binaries=True,
    name="EqnPlot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=USE_UPX,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(ICON_PATH)] if ICON_PATH.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=USE_UPX,
    upx_exclude=[],
    name="EqnPlot",
)
