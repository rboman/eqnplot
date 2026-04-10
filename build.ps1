param(
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    throw "Python virtuel introuvable. Cree d'abord .venv puis installe les dependances."
}

Write-Host "Installation des outils de build..."
& $PythonExe -m pip install --upgrade pip pyinstaller | Out-Host

Write-Host "Nettoyage des repertoires build/dist..."
if (Test-Path "build") { Remove-Item -LiteralPath "build" -Recurse -Force }
if (Test-Path "dist") { Remove-Item -LiteralPath "dist" -Recurse -Force }

if ($OneFile) {
    Write-Host "Build PyInstaller en mode onefile..."
    $iconPath = Join-Path $ProjectRoot "assets\eqnplot-icon.ico"
    $args = @(
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name", "EqnPlot",
        "--onefile"
    )
    if (Test-Path $iconPath) {
        $args += @("--icon", $iconPath)
        $args += @("--add-data", "$iconPath;assets")
    }
    $args += "main.py"
    & $PythonExe @args | Out-Host
} else {
    Write-Host "Build PyInstaller via EqnPlot.spec..."
    & $PythonExe -m PyInstaller --noconfirm --clean EqnPlot.spec | Out-Host
}

Write-Host "Build termine. Sortie dans dist\"
