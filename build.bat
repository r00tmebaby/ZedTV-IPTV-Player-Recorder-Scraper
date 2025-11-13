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

REM Fast path: `build.bat quick` delegates to build_quick.bat (onedir, no UPX)
if "%~1"=="quick" (
    echo Quick build requested: delegating to build_quick.bat (faster startup - onedir, no UPX)
    call "%~dp0build_quick.bat"
    popd
    endlocal
    exit /b 0
)

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
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
    exit /b 1
)

echo.
echo Step 2: Cleaning old build files...
echo ----------------------------------------
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"


echo.
echo Step 3: Building executable (clean, no .spec)...
echo ----------------------------------------
REM Use onedir build for faster startup; disable UPX; collect VLC; keep spec out of repo
if not exist "build\spec" mkdir "build\spec"
%PY% -m PyInstaller --clean --noconfirm --noupx ^
    --name "ZedTV-IPTV-Player" ^
    --onedir --windowed ^
    --paths "src" ^
    --icon "MEDIA\logo.ico" ^
    --collect-all vlc ^
    --specpath "build\spec" ^
    src\main.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed!
    exit /b 1
)

REM Remove generated .spec to keep workspace clean
for %%F in (ZedTV-IPTV-Player.spec main.spec src.spec) do (
    if exist "build\spec\%%F" del /f /q "build\spec\%%F"
)
if exist "build\spec" rmdir /s /q "build\spec"


echo.
echo Step 3a: Prepare VLC runtime files for PyInstaller detection (optional)...
echo ----------------------------------------
if exist "src\libs\win" (
    echo Copying libvlc DLLs next to build entrypoint so PyInstaller can collect them...
    if not exist "build\tmp_vlc" mkdir "build\tmp_vlc"
    copy /Y "src\libs\win\libvlc.dll" "build\tmp_vlc\libvlc.dll" >nul
    copy /Y "src\libs\win\libvlccore.dll" "build\tmp_vlc\libvlccore.dll" >nul
    echo Copying plugins to temp area...
    if exist "build\tmp_vlc\plugins" rmdir /s /q "build\tmp_vlc\plugins"
    xcopy /E /I /Y /Q "src\libs\win\plugins" "build\tmp_vlc\plugins" >nul
) else (
    echo [WARN] src\libs\win not found; relying on system VLC installation.
)


echo.
echo Step 4: Bundling VLC runtime (DLLs + plugins at root)...
echo ----------------------------------------
if exist "src\libs\win" (
    echo Copying libvlc DLLs to dist root...
    copy /Y "src\libs\win\libvlc.dll" "dist\ZedTV-IPTV-Player\libvlc.dll" >nul
    copy /Y "src\libs\win\libvlccore.dll" "dist\ZedTV-IPTV-Player\libvlccore.dll" >nul
    echo Copying VLC plugins folder to dist root...
    if exist "dist\ZedTV-IPTV-Player\plugins" rmdir /s /q "dist\ZedTV-IPTV-Player\plugins"
    mkdir "dist\ZedTV-IPTV-Player\plugins" >nul
    for %%D in (
        access access_output audio_output codec demux mux packetizer stream_out stream_filter text_renderer spu
        video_output video_filter video_chroma d3d11 d3d9
    ) do (
        if exist "src\libs\win\plugins\%%D" (
            xcopy /E /I /Y /Q "src\libs\win\plugins\%%D" "dist\ZedTV-IPTV-Player\plugins\%%D" >nul
        )
    )
    REM Copy plugins.dat if present (speeds up plugin discovery)
    if exist "src\libs\win\plugins\plugins.dat" copy /Y "src\libs\win\plugins\plugins.dat" "dist\ZedTV-IPTV-Player\plugins\plugins.dat" >nul
) else (
    echo [WARN] src\libs\win not found; relying on system VLC installation.
)


echo.
echo Step 5: Verifying bundled VLC files (onedir)...
echo ----------------------------------------
set VLC_FOUND=0
if exist "dist\ZedTV-IPTV-Player\libvlc.dll" (
    echo [OK] Found libvlc.dll at root
    set VLC_FOUND=1
) else (
    echo [WARN] libvlc.dll not found at root
)
if exist "dist\ZedTV-IPTV-Player\libvlccore.dll" (
    echo [OK] Found libvlccore.dll at root
) else (
    echo [WARN] libvlccore.dll not found at root
)
if exist "dist\ZedTV-IPTV-Player\plugins" (
    echo [OK] Found VLC plugins folder at root
) else (
    echo [WARN] VLC plugins folder not found at root
)
if %VLC_FOUND%==0 (
    echo.
    echo [WARN] VLC libraries not detected in bundle. App may use system VLC or in-app playback may be limited.
)

REM Ensure data folders exist in dist (runtime working directories)
if not exist "dist\ZedTV-IPTV-Player\data" mkdir "dist\ZedTV-IPTV-Player\data"
if not exist "dist\ZedTV-IPTV-Player\data\thumbnails" mkdir "dist\ZedTV-IPTV-Player\data\thumbnails"
if not exist "dist\ZedTV-IPTV-Player\data\epg" mkdir "dist\ZedTV-IPTV-Player\data\epg"
if not exist "dist\ZedTV-IPTV-Player\records" mkdir "dist\ZedTV-IPTV-Player\records"

REM Seed background.jpg: use project src copy if available; fallback to MEDIA\logo.png
if exist "src\data\thumbnails\background.jpg" (
    copy /Y "src\data\thumbnails\background.jpg" "dist\ZedTV-IPTV-Player\data\thumbnails\background.jpg" >nul
) else (
    if exist "MEDIA\logo.png" (
        if not exist "dist\ZedTV-IPTV-Player\data\thumbnails\background.jpg" (
            copy /Y "MEDIA\logo.png" "dist\ZedTV-IPTV-Player\data\thumbnails\background.jpg" >nul
        )
    )
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

if exist "build\tmp_vlc" rmdir /s /q "build\tmp_vlc"

popd
endlocal
