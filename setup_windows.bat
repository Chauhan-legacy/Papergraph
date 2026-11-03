@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo        PaperGraph Windows Automated Setup
echo   Local-First Research Intelligence Platform
echo ========================================================
echo.

:: 1. Verify Python Installation
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not found in your PATH.
    echo Please install Python 3.11 or newer from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo [*] Detected Python %PY_VER%

:: 2. Setup Virtual Environment
if not exist ".venv" (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [*] Existing virtual environment found.
)

:: 3. Upgrade Pip & Install Dependencies
echo [*] Installing PaperGraph core scientific dependencies...
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo [*] Core setup completed successfully!
echo [*] To launch PaperGraph, execute: run_windows.bat
echo ========================================================
echo.
pause

