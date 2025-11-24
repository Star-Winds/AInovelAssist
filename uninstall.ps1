#!/usr/bin/env pwsh
# Windows-friendly uninstaller: remove venv and launcher
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvDir = Join-Path $root ".venv"
$binDir = Join-Path $root "bin"
$launcher = Join-Path $binDir "ainovelassist.cmd"

if (Test-Path $venvDir) {
    Remove-Item -Recurse -Force $venvDir
    Write-Output "已删除虚拟环境 $venvDir"
} else {
    Write-Output "未找到虚拟环境，跳过。"
}

if (Test-Path $launcher) {
    Remove-Item -Force $launcher
    Write-Output "已删除启动脚本 $launcher"
}

if (Test-Path $binDir) {
    Remove-Item -Force $binDir -ErrorAction SilentlyContinue
}
