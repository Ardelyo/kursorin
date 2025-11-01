@echo off
echo ========================================
echo   Smart Cursor Control - START HERE
echo ========================================
echo.
echo Welcome to Smart Cursor Control!
echo.
echo This launcher will help you get started safely.
echo.

REM Check if we're in the right directory
if not exist "Launchers\launcher_stable.py" (
    echo ERROR: Please run this from the Current_Version folder
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Choose an option:
echo [1] Run System Test (recommended first)
echo [2] Launch Smart Cursor
echo [3] Run Demo Mode Only
echo.

set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo Running system test...
    echo.
    python test_system.py
) else if "%choice%"=="2" (
    echo.
    echo Starting stable launcher...
    echo.
    python Launchers\launcher_stable.py
) else if "%choice%"=="3" (
    echo.
    echo Starting demo mode...
    echo.
    python Core\demo_mode.py
) else (
    echo Invalid choice. Running system test by default...
    echo.
    python test_system.py
)

echo.
echo Smart Cursor Control session ended.
echo Check Docs\ folder for help if needed.
pause
