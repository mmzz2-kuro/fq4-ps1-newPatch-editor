param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "../.."))
$Spec = Join-Path $ProjectRoot "tools/packaging/fq4_gui.spec"
$Dist = Join-Path $ProjectRoot "tools/dist"
$Build = Join-Path $ProjectRoot "work/fq4/012/pyinstaller-build"

& $Python -m PyInstaller --noconfirm --clean --distpath $Dist --workpath $Build $Spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

$Exe = Join-Path $Dist "FQ4-Standard-BIOS-Korean-Tool.exe"
if (-not (Test-Path -LiteralPath $Exe -PathType Leaf)) {
    throw "Expected EXE was not created: $Exe"
}
Get-FileHash -Algorithm SHA256 -LiteralPath $Exe
