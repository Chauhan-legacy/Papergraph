@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo               Starting PaperGraph
echo    Scientific Research Intelligence & Knowledge Graph
echo ========================================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo Please run setup_windows.bat first.
    pause
    exit /b 1
)

echo [*] Launching local PaperGraph scientific server...
echo [*] Application URL: http://127.0.0.1:8000
echo [*] Press Ctrl+C in this console to stop the server anytime.
echo.

:: Automatically open user browser after a 2 second delay in parallel
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000"

:: Start Uvicorn
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

