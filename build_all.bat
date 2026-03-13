@echo off
chcp 65001 >nul
echo ========================================
echo   AutoDoor All Versions Build Script
echo ========================================
echo.

echo [1/2] Building standard version...
call build_standard.bat

echo.
echo [2/2] Building DD version...
call build_dd.bat

echo.
echo ========================================
echo   All versions build complete!
echo ========================================
echo.
echo Output:
echo   - dist\autodoor\     (Standard - PyAutoGUI)
echo   - dist\autodoor_dd\  (DD - DD Virtual Keyboard)
echo.
pause
