@echo off
REM Quick build without tests - for development iterations

echo ========================================
echo ZedTV IPTV Player - Quick Build
echo ========================================
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
    --paths "src" ^
    --icon="MEDIA\logo.ico" ^
    --add-data="MEDIA;MEDIA" ^
    --add-data="src/libs;libs" ^
    --collect-all=vlc ^
    src\main.py

if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Copying VLC libraries...
if exist "src\libs\win" (
    if not exist "dist\ZedTV-IPTV-Player\libs\win" mkdir "dist\ZedTV-IPTV-Player\libs\win"
    xcopy /E /Y /Q "src\libs\win" "dist\ZedTV-IPTV-Player\libs\win\" >nul
)

echo.
echo Creating folders...
if not exist "dist\ZedTV-IPTV-Player\data" mkdir "dist\ZedTV-IPTV-Player\data"
if not exist "dist\ZedTV-IPTV-Player\records" mkdir "dist\ZedTV-IPTV-Player\records"

echo.
echo BUILD COMPLETE!
echo Executable: dist\ZedTV-IPTV-Player\ZedTV-IPTV-Player.exe
echo.
pause
