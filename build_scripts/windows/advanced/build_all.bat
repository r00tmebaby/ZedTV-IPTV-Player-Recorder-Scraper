@echo off
REM Master build script - Does everything!

echo ========================================
echo ZedTV IPTV Player
echo MASTER BUILD SCRIPT
echo ========================================
echo.
echo This script will:
echo 1. Run 105 tests
echo 2. Build executable
echo 3. Copy VLC libraries
echo 4. Create distribution package
echo 5. Generate ZIP file
echo.
echo Press Ctrl+C to cancel or
pause

REM Step 1: Tests
call run_tests.bat
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Tests failed! Cannot continue.
    pause
    exit /b 1
)

REM Step 2: Build
echo.
echo.
call build.bat
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

REM Step 3: Package
echo.
echo.
call create_package.bat
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Packaging failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo COMPLETE BUILD FINISHED!
echo ========================================
echo.
echo Your distribution is ready:
echo - Folder: ZedTV-IPTV-Player-v1.4\
echo - ZIP: ZedTV-IPTV-Player-v1.4.zip
echo.
echo Ready to distribute!
echo.
pause

