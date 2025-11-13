@echo off
REM Create distribution ZIP package

REM Extract version from __version__.py using Python
for /f "delims=" %%i in ('.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'src'); from __version__ import __version__; print(__version__)"') do set VERSION=%%i

echo ========================================
echo Creating Distribution Package
echo ========================================
echo.
echo Version: %VERSION%
echo.

if not exist "dist\ZedTV-IPTV-Player\ZedTV-IPTV-Player.exe" (
    echo ERROR: Executable not found! Run build.bat first.
    pause
    exit /b 1
)

echo Creating distribution folder...
set DIST_NAME=ZedTV-IPTV-Player-v%VERSION%
if exist "%DIST_NAME%" rmdir /s /q "%DIST_NAME%"
mkdir "%DIST_NAME%"

echo.
echo Copying entire application folder...
xcopy /E /Y /Q "dist\ZedTV-IPTV-Player\*" "%DIST_NAME%\" >nul

echo.
echo Creating documentation...
(
echo ========================================
echo ZedTV IPTV Player v%VERSION%
echo ========================================
echo.
echo INSTALLATION
echo ------------
echo 1. Extract all files to a folder
echo 2. Keep all files together in the ZedTV-IPTV-Player folder
echo 3. Run ZedTV-IPTV-Player.exe
echo.
echo IMPORTANT: Do NOT move just the .exe file!
echo The application needs all files in the folder to work.
echo.
echo.
echo FOLDER STRUCTURE
echo ----------------
echo ZedTV-IPTV-Player.exe    - Main application
echo _internal/               - Application files ^(REQUIRED^)
echo libs/                    - VLC libraries ^(REQUIRED^)
echo MEDIA/                   - Application icons
echo data/                    - Settings ^(auto-created^)
echo records/                 - Recorded streams
echo.
echo.
echo FEATURES
echo --------
echo - Play IPTV streams from M3U/M3U8 files
echo - Xtream Codes API support
echo - Record streams to MP4 format
echo - Fullscreen mode ^(double-click video^)
echo - Hardware-accelerated video playback
echo - Configurable VLC settings
echo - Real-time search/filtering
echo - Category browsing
echo.
echo.
echo QUICK START
echo -----------
echo 1. Run ZedTV-IPTV-Player.exe
echo 2. File → Open to load M3U file
echo    OR
echo    Xtream → Add Account for Xtream provider
echo 3. Select category, then channel
echo 4. Double-click to play
echo.
echo.
echo STARTUP TIME
echo ------------
echo First launch: ~2-3 seconds
echo Subsequent launches: ~1-2 seconds
echo ^(Much faster than single-file mode!^)
echo.
echo.
echo SYSTEM REQUIREMENTS
echo -------------------
echo - Windows 7 or later
echo - 2GB RAM minimum
echo - Internet connection for streaming
echo.
echo.
echo TROUBLESHOOTING
echo ---------------
echo If application won't start:
echo - Make sure all files are extracted
echo - Don't move the .exe away from _internal folder
echo - Check antivirus isn't blocking it
echo.
echo.
echo DISTRIBUTION
echo ------------
echo To share this application:
echo 1. ZIP the entire ZedTV-IPTV-Player folder
echo 2. Users extract the ZIP
echo 3. Users run ZedTV-IPTV-Player.exe from extracted folder
echo.
echo.
echo CREDITS
echo -------
echo Developer: @r00tme
echo Version: %VERSION%
echo Release Date: %date%
echo.
echo Built with:
echo - Python
echo - VLC Media Player
echo - PySimpleGUI
echo - PyInstaller
echo.
) > "%DIST_NAME%\README.txt"

echo.
echo Creating VERSION info...
(
echo Version: %VERSION%
echo Build Date: %date% %time%
echo Platform: Windows
echo.
echo Changelog:
echo - Fixed M3U parsing with exact category matching
echo - Added VLC settings configuration
echo - Improved recording functionality
echo - Added instant search filtering
echo - Enhanced fullscreen mode
echo - Hardware acceleration support
echo - Multiple bug fixes and improvements
) > "%DIST_NAME%\VERSION.txt"

echo.
echo Creating LICENSE file...
(
echo ZedTV IPTV Player
echo.
echo Copyright ^(c^) 2024 @r00tme
echo.
echo This software is provided "as is", without warranty of any kind,
echo express or implied, including but not limited to the warranties
echo of merchantability, fitness for a particular purpose and
echo noninfringement.
echo.
echo VLC Libraries:
echo This application uses VLC libraries which are licensed under
echo the GNU Lesser General Public License ^(LGPL^).
echo For more information, visit: https://www.videolan.org/
) > "%DIST_NAME%\LICENSE.txt"

echo.
echo Checking distribution size...
for /f "tokens=3" %%a in ('dir /s "%DIST_NAME%" ^| find "File(s)"') do set SIZE=%%a
echo Distribution size: %SIZE% bytes

echo.
echo Creating ZIP archive...
if exist "%DIST_NAME%.zip" del "%DIST_NAME%.zip"

REM Use PowerShell to create ZIP
powershell -command "Compress-Archive -Path '%DIST_NAME%' -DestinationPath '%DIST_NAME%.zip' -Force"

if %errorlevel% neq 0 (
    echo WARNING: Could not create ZIP file
    echo You can manually ZIP the '%DIST_NAME%' folder
) else (
    echo.
    echo ========================================
    echo DISTRIBUTION PACKAGE CREATED!
    echo ========================================
    echo.
    echo Package: %DIST_NAME%.zip
    echo Folder: %DIST_NAME%\
    echo.
    echo Contents:
    dir /B "%DIST_NAME%"
    echo.
    echo Distribution package is ready to share!
)

echo.
pause

