@echo off
REM Smart Cursor Control - Modular Version Launcher
REM This batch file checks Python installation and launches the application

echo ========================================
echo 🖱️  Smart Cursor Control - Modular Version
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if we're in the right directory
if not exist "launch.py" (
    echo ❌ launch.py not found
    echo Please run this batch file from the Current_Version directory
    echo.
    pause
    exit /b 1
)

echo 🚀 Starting Smart Cursor Control...
echo.

REM Launch the application
python launch.py

echo.
echo Application closed.
pause
