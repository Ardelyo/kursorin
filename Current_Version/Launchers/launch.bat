@echo off
echo ========================================
echo   Smart Cursor Control - Stable Version
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found. Launching stable launcher...
echo.

python launcher_stable.py

echo.
echo Smart Cursor Control closed.
echo Check launcher_stable.log for any issues.
pause
