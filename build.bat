@echo off
REM Build script for ZedTV IPTV Player
REM This script tests the application and creates an executable

setlocal enableextensions enabledelayedexpansion

echo ========================================
echo ZedTV IPTV Player - Build System
echo ========================================
echo.

REM Resolve project root
set PROJDIR=%~dp0
pushd %PROJDIR%

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Use venv Python if present
if exist ".venv\Scripts\python.exe" (
    set PY=.venv\Scripts\python.exe
    set PIP=.venv\Scripts\pip.exe
) else (
    set PY=python
    set PIP=pip
)

echo Step 0: Installing project dependencies...
echo ----------------------------------------
%PIP% install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Could not install dependencies from requirements.txt
)

REM Ensure pytest and pyinstaller are installed
%PIP% install pytest pyinstaller >nul 2>&1


echo Step 1: Running tests (pytest)...
echo ----------------------------------------
%PY% -m pytest -q
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Tests failed! Fix the errors before building.
    pause
    exit /b 1
)

echo.
echo Step 2: Cleaning old build files...
echo ----------------------------------------
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"


echo.
echo Step 3: Building executable from spec...
echo ----------------------------------------
%PY% -m PyInstaller --clean ZedTV-IPTV-Player.spec
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed using spec!
    pause
    exit /b 1
)


echo.
echo Step 4: Verifying bundled VLC files...
echo ----------------------------------------
set VLC_FOUND=0
REM Check _internal folder (PyInstaller default location)
if exist "dist\ZedTV-IPTV-Player\_internal\libvlc.dll" (
    echo [OK] Found libvlc.dll in _internal
    set VLC_FOUND=1
) else (
    echo [WARN] libvlc.dll not in _internal
)
if exist "dist\ZedTV-IPTV-Player\_internal\libvlccore.dll" (
    echo [OK] Found libvlccore.dll in _internal
) else (
    echo [WARN] libvlccore.dll not in _internal
)
if exist "dist\ZedTV-IPTV-Player\_internal\plugins" (
    echo [OK] Found plugins folder in _internal
) else if exist "dist\ZedTV-IPTV-Player\plugins" (
    echo [OK] Found plugins folder at root
    set VLC_FOUND=1
) else (
    echo [WARN] plugins folder not found
)
if %VLC_FOUND%==0 (
    echo.
    echo [ERROR] VLC libraries not properly bundled!
    echo Check PyInstaller spec file.
)


echo.
echo Step 5: Copying MEDIA files...
echo ----------------------------------------
if exist "MEDIA" (
    if not exist "dist\ZedTV-IPTV-Player\MEDIA" mkdir "dist\ZedTV-IPTV-Player\MEDIA"
    xcopy /E /Y /Q "MEDIA\*.*" "dist\ZedTV-IPTV-Player\MEDIA\" >nul
)


echo.
echo ========================================
echo BUILD SUCCESSFUL!
echo ========================================
echo.
echo Executable created: dist\ZedTV-IPTV-Player\ZedTV-IPTV-Player.exe
echo.
echo Package contents:
dir /B "dist\ZedTV-IPTV-Player"
echo.
echo IMPORTANT: The entire ZedTV-IPTV-Player folder is needed!
echo Do NOT move just the .exe file.
echo.
echo Press any key to exit...
pause >nul

popd
endlocal
