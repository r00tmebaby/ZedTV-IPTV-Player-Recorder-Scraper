@echo off
REM Convenience wrapper for Windows build script
REM This calls the actual build script in build_scripts/windows/

echo Delegating to build_scripts\windows\build.bat
echo.

call "%~dp0build_scripts\windows\build.bat" %*

