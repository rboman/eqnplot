param(
    [switch]$OneFile,
    [switch]$Upx
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    throw "Virtualenv Python not found. Create .venv and install dependencies first."
}

$args = @("build.py")
if ($OneFile) {
    $args += "--onefile"
}
if ($Upx) {
    $args += "--upx"
}
& $PythonExe @args | Out-Host
