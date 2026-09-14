$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root
python -m PyInstaller --noconfirm --clean --distpath tools/dist --workpath work/fq4/save-editor/pyinstaller tools/packaging/fq4_save_editor.spec
