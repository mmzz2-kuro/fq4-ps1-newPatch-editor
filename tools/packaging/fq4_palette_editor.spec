# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path(SPECPATH).parents[1]
tools = root / 'tools'
a = Analysis(
    [str(tools / 'FQ4PaletteEditor' / 'app.py')],
    pathex=[str(tools / 'scripts')],
    binaries=[],
    datas=[
        (str(root / 'docs' / 'fq4' / 'analysis' / '001' / 'original-files.json'), 'data'),
        (str(tools / 'FQ4SaveEditor' / 'class_names.json'), 'data'),
    ],
    hiddenimports=['fq4_class_sprite'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='FQ4-Class-Palette-Editor',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=True,
    upx_exclude=[], runtime_tmpdir=None, console=False,
    disable_windowed_traceback=False, argv_emulation=False,
    target_arch=None, codesign_identity=None, entitlements_file=None,
)
