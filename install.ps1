#!/usr/bin/env pwsh
# Windows-friendly installer: create venv, install deps, and generate launcher
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvDir = Join-Path $root ".venv"
$binDir = Join-Path $root "bin"
$launcher = Join-Path $binDir "ainovelassist.cmd"

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "❌ 未找到 python，请安装 Python 3.11+ 后再试。"
    exit 1
}

& $pythonCmd.Source -m venv $venvDir
$venvPython = Join-Path $venvDir "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $root "requirements.txt")

New-Item -ItemType Directory -Force -Path $binDir | Out-Null
$launcherContent = @"
@echo off
setlocal
set SCRIPT_DIR=%~dp0..
"%SCRIPT_DIR%\.venv\Scripts\python.exe" "%SCRIPT_DIR%\scripts\app.py" %*
"@
Set-Content -Path $launcher -Value $launcherContent -Encoding ASCII

Write-Output "安装完成！使用 $launcher 运行示例："
Write-Output "  $launcher demo"
