@echo off
REM Legacy PyInstaller build script (for compatibility)
REM Use build.bat or build_nuitka.bat for the newer Nuitka builds

echo ========================================
echo ZedTV IPTV Player - PyInstaller Build
echo ========================================
echo.
echo WARNING: This is the legacy PyInstaller build script.
echo For better performance, consider using:
echo   build_nuitka.bat (recommended)
echo   build.bat (now uses Nuitka too)
echo.
echo Continue with PyInstaller build? (y/N)
set /p CHOICE="> "
if /i not "%CHOICE%"=="y" (
    echo Build cancelled.
    exit /b 0
)

setlocal enableextensions enabledelayedexpansion

set PROJDIR=%~dp0
pushd %PROJDIR%

REM Use venv Python if present
if exist ".venv\Scripts\python.exe" (
    set PY=.venv\Scripts\python.exe
    set PIP=.venv\Scripts\pip.exe
) else (
    set PY=python
    set PIP=pip
)

echo.
echo Installing PyInstaller and dependencies...
%PIP% install -r requirements.txt >nul 2>&1
%PIP% install pyinstaller >nul 2>&1

echo.
echo Cleaning old build files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo Building with PyInstaller...
if not exist "build\spec" mkdir "build\spec"
%PY% -m PyInstaller --clean --noconfirm --noupx ^
    --name "ZedTV-IPTV-Player" ^
    --onedir --windowed ^
    --paths "src" ^
    --collect-all vlc ^
    --specpath "build\spec" ^
    src\main.py

if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed!
    exit /b 1
)

REM Clean up spec files
for %%F in (ZedTV-IPTV-Player.spec main.spec src.spec) do (
    if exist "build\spec\%%F" del /f /q "build\spec\%%F"
)
if exist "build\spec" rmdir /s /q "build\spec"

echo.
echo Adding VLC runtime files...
if exist "src\libs\win" (
    copy /Y "src\libs\win\libvlc.dll" "dist\ZedTV-IPTV-Player\libvlc.dll" >nul
    copy /Y "src\libs\win\libvlccore.dll" "dist\ZedTV-IPTV-Player\libvlccore.dll" >nul
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
    if exist "src\libs\win\plugins\plugins.dat" copy /Y "src\libs\win\plugins\plugins.dat" "dist\ZedTV-IPTV-Player\plugins\plugins.dat" >nul
)

REM Create runtime directories
if not exist "dist\ZedTV-IPTV-Player\data" mkdir "dist\ZedTV-IPTV-Player\data"
if not exist "dist\ZedTV-IPTV-Player\data\thumbnails" mkdir "dist\ZedTV-IPTV-Player\data\thumbnails"
if not exist "dist\ZedTV-IPTV-Player\data\epg" mkdir "dist\ZedTV-IPTV-Player\data\epg"
if not exist "dist\ZedTV-IPTV-Player\records" mkdir "dist\ZedTV-IPTV-Player\records"

if exist "src\data\thumbnails\background.jpg" (
    copy /Y "src\data\thumbnails\background.jpg" "dist\ZedTV-IPTV-Player\data\thumbnails\background.jpg" >nul
) else (
    if exist "MEDIA\logo.png" (
        copy /Y "MEDIA\logo.png" "dist\ZedTV-IPTV-Player\data\thumbnails\background.jpg" >nul
    )
)

echo.
echo ========================================
echo PYINSTALLER BUILD COMPLETE!
echo ========================================
echo.
echo Executable: dist\ZedTV-IPTV-Player\ZedTV-IPTV-Player.exe
echo.
echo Note: For better performance, try build_nuitka.bat next time!
echo.

popd
endlocal
