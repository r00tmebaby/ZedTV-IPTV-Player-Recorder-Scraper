@echo off
REM Quick build without tests - for development iterations

echo ========================================
echo ZedTV IPTV Player - Quick Build (Windows)
echo ========================================
echo.

REM Change to project root (two levels up)
pushd "%~dp0..\.."
echo Project root: %CD%
echo.

echo Installing dependencies (quick)...
pip install -r requirements.txt >nul 2>&1

echo Cleaning old build...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "ZedTV-IPTV-Player.spec" del "ZedTV-IPTV-Player.spec"

echo.
echo Building executable...
pyinstaller --name="ZedTV-IPTV-Player" ^
    --onedir ^
    --windowed ^
    --noupx ^
    --paths "src" ^
    --icon="MEDIA\logo.ico" ^
    --collect-all=vlc ^
    src\main.py

if %errorlevel% neq 0 (
    echo Build failed!
    exit /b 1
)

echo.
echo Copying VLC runtime to dist root...
if exist "src\libs\win" (
    copy /Y "src\libs\win\libvlc.dll" "dist\ZedTV-IPTV-Player\libvlc.dll" >nul
    copy /Y "src\libs\win\libvlccore.dll" "dist\ZedTV-IPTV-Player\libvlccore.dll" >nul
    if exist "dist\ZedTV-IPTV-Player\plugins" rmdir /s /q "dist\ZedTV-IPTV-Player\plugins"
    xcopy /E /I /Y /Q "src\libs\win\plugins" "dist\ZedTV-IPTV-Player\plugins" >nul
)

echo.
echo Creating folders...
if not exist "dist\ZedTV-IPTV-Player\data" mkdir "dist\ZedTV-IPTV-Player\data"
if not exist "dist\ZedTV-IPTV-Player\data\thumbnails" mkdir "dist\ZedTV-IPTV-Player\data\thumbnails"
if not exist "dist\ZedTV-IPTV-Player\data\epg" mkdir "dist\ZedTV-IPTV-Player\data\epg"
if not exist "dist\ZedTV-IPTV-Player\records" mkdir "dist\ZedTV-IPTV-Player\records"

REM Seed background image
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
echo BUILD COMPLETE!
echo Executable: dist\ZedTV-IPTV-Player\ZedTV-IPTV-Player.exe
echo.
