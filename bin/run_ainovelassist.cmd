@echo off
REM AInovelAssist Windows launcher
SET ROOT_DIR=%~dp0..
cd /d "%ROOT_DIR%"
"%ROOT_DIR%\.venv\Scripts\python.exe" -m scripts.app %*

