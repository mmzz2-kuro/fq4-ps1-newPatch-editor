$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root
python -m PyInstaller --noconfirm --clean --distpath tools/dist --workpath work/fq4/039/pyinstaller tools/packaging/fq4_palette_editor.spec
