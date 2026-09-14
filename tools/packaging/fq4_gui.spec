# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project_root = Path(SPECPATH).parents[1]
tools_dir = project_root / "tools"
scripts_dir = tools_dir / "scripts"
deps_dir = project_root / "work" / "fq4" / "python-deps"

a = Analysis(
    [str(tools_dir / "fq4_bios_independent_gui.py")],
    pathex=[str(scripts_dir), str(deps_dir)],
    binaries=[(str(deps_dir / "keystone" / "keystone.dll"), "keystone")],
    datas=[],
    hiddenimports=["build_fq4_bios_independent", "build_full_font_runtime", "build_bios_independent_poc", "build_party_race_limit_patch", "repair_cdrom_xa_ecc", "verify_cdrom_xa_ecc"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["unicorn"],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="FQ4-Standard-BIOS-Korean-Tool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
