# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
root = Path(SPECPATH).parents[1]
tools = root / 'tools'
a = Analysis([str(tools/'FQ4SaveEditor'/'app.py')], pathex=[str(tools/'scripts')],
    binaries=[], datas=[(str(tools/'FQ4SaveEditor'/'character_names.json'),'.'),(str(tools/'FQ4SaveEditor'/'class_names.json'),'.'),(str(tools/'FQ4SaveEditor'/'class_catalog.json'),'.'),(str(tools/'FQ4SaveEditor'/'item_names.json'),'.'),(str(tools/'FQ4SaveEditor'/'class_icons'),'class_icons'),(str(tools/'scripts'/'fq4_memcard.py'),'scripts')],
    hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[])
pyz = PYZ(a.pure)
exe = EXE(pyz,a.scripts,a.binaries,a.datas,[],name='FQ4-PS1-Save-Editor',debug=False,bootloader_ignore_signals=False,
    strip=False,upx=True,upx_exclude=[],runtime_tmpdir=None,console=False,disable_windowed_traceback=False,
    argv_emulation=False,target_arch=None,codesign_identity=None,entitlements_file=None)
