@echo off
echo Testing version extraction...
echo.

REM Method 1: Using Python (RECOMMENDED)
echo Method 1: Python extraction
for /f "delims=" %%i in ('.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'src'); from __version__ import __version__; print(__version__)"') do set VERSION=%%i
echo Extracted VERSION=%VERSION%
echo.

REM Verify it worked
if "%VERSION%"=="" (
    echo ERROR: Version extraction failed!
) else (
    echo SUCCESS: Version is %VERSION%
    echo Package would be named: ZedTV-IPTV-Player-v%VERSION%
)

echo.
pause

