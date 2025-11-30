@echo off
echo ==========================================
echo      Kursorin Project Cleanup Tool
echo ==========================================
echo.

echo [1/4] Moving scattered documentation to docs/...
move "EYE_TRACKING_PLAN.md" docs\ >nul 2>&1
move "FOLDER_GUIDE.md" docs\ >nul 2>&1
move "GAMING_MODE_PLAN.md" docs\ >nul 2>&1
move "TYPING_MODE_PLAN.md" docs\ >nul 2>&1
move "RENCANA_PEROMBAKAN.md" docs\ >nul 2>&1
move "FIXES_APPLIED.md" docs\ >nul 2>&1
move "QUICK_START.md" docs\ >nul 2>&1
move "TROUBLESHOOTING.md" docs\ >nul 2>&1
move "evolution_plan.md" docs\ >nul 2>&1
move "plan.md" docs\ >nul 2>&1

echo [2/4] Moving configuration files to config/...
move "cursor_settings_stable.json" config\ >nul 2>&1
move "smart_cursor_settings.json" config\ >nul 2>&1
move "ui_settings.json" config\ >nul 2>&1

echo [3/4] Deleting log files...
del "smart_cursor.log" >nul 2>&1
del "smart_cursor_stable.log" >nul 2>&1

echo [4/4] Removing legacy folders...
rmdir /S /Q "Current_Version" >nul 2>&1
rmdir /S /Q "Archive" >nul 2>&1
rmdir /S /Q "Tools" >nul 2>&1
rmdir /S /Q "Logs" >nul 2>&1
rmdir /S /Q "Legacy_Code" >nul 2>&1

echo.
echo ==========================================
echo           Cleanup Completed!
echo ==========================================
echo Note: If some files/folders remain, they might be open in your editor.
echo Please close them and run this script again.
echo.
pause
