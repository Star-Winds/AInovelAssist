# install.ps1
# Windows installer: create virtual environment, install dependencies, and create launcher run_ainovelassist.cmd

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "===== AInovelAssist Windows Installer ====="
Write-Host ""

# 1. Project paths
$RootDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir  = Join-Path $RootDir ".venv"
$ReqFile  = Join-Path $RootDir "requirements.txt"
$BinDir   = Join-Path $RootDir "bin"
$Launcher = Join-Path $BinDir "run_ainovelassist.cmd"

Write-Host "Project directory: $RootDir"

# 2. Check python
Write-Host ""
Write-Host "Checking for python..."
try {
    $pythonCmd = Get-Command python -ErrorAction Stop
    Write-Host "Found python at: $($pythonCmd.Source)"
} catch {
    Write-Host "ERROR: python was not found. Please install Python 3.11+ and add it to PATH."
    exit 1
}

# 3. Create virtual environment
if (-not (Test-Path $VenvDir)) {
    Write-Host ""
    Write-Host "Creating virtual environment in: $VenvDir"
    python -m venv $VenvDir
} else {
    Write-Host ""
    Write-Host "Virtual environment already exists: $VenvDir"
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "ERROR: $VenvPython was not found. Virtual environment creation may have failed."
    exit 1
}

# 4. Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..."
& $VenvPython -m pip install --upgrade pip

# 5. Install dependencies
if (-not (Test-Path $ReqFile)) {
    Write-Host "ERROR: requirements.txt not found in project root."
    exit 1
}

Write-Host ""
Write-Host "Installing dependencies from requirements.txt..."
& $VenvPython -m pip install -r $ReqFile

# 6. Create bin directory
if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir | Out-Null
}

# 7. Create Windows launcher (CMD batch file)
Write-Host ""
Write-Host "Creating launcher: $Launcher"

$launcherLines = @(
    '@echo off',
    'REM AInovelAssist Windows launcher',
    'SET ROOT_DIR=%~dp0..',
    '"%ROOT_DIR%\.venv\Scripts\python.exe" "%ROOT_DIR%\scripts\app.py" %*'
)

$launcherLines | Set-Content -Path $Launcher -Encoding ASCII

Write-Host ""
Write-Host "===== Install completed ====="
Write-Host "Run example with:"
Write-Host "  `"$Launcher demo`""
Write-Host ""
Write-Host "Or double-click bin\\run_ainovelassist.cmd in File Explorer."
Write-Host ""
