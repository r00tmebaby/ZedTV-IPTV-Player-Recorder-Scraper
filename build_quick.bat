@echo off
REM Convenience wrapper for Windows quick build script
REM This calls the actual build script in build_scripts/windows/

echo Delegating to build_scripts\windows\build_quick.bat
echo.

call "%~dp0build_scripts\windows\build_quick.bat" %*

