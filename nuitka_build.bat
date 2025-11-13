@echo off
REM Experimental high-performance build using Nuitka (C compilation)
REM Produces a standalone folder with compiled binaries; typically faster cold start than PyInstaller.
REM Requirements: Python 3.12+, pip, MSVC Build Tools (or Visual Studio), and sufficient disk space.
REM Usage: nuitka_build.bat [quick]

setlocal enableextensions enabledelayedexpansion

set PROJDIR=%~dp0
pushd %PROJDIR%

set PY=python
set PIP=pip

for /f "tokens=*" %%v in ('%PY% -c "import sys;print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"') do set PYVER=%%v

REM Guard unsupported Nuitka micro version (3.13.4) per error feedback
if "%PYVER%"=="3.13.4" (
  echo FATAL: Python 3.13.4 has a CPython bug incompatible with Nuitka. Use 3.13.5 or 3.12.x.^
  echo Tip: py -3.12 -m venv .venv && .venv\Scripts\activate && run build again.
  exit /b 1
)

if "%~1"=="quick" (
  set EXTRA_FLAGS=--noinclude-ipython-mode --remove-output --disable-ccache
) else (
  set EXTRA_FLAGS=--lto=yes --show-progress --report=build_report.html
)

echo ========================================
echo Nuitka Build - ZedTV IPTV Player
echo ========================================

echo Step 1: Install Nuitka + runtime deps (trimmed)...
%PIP% install --quiet --upgrade pip >nul 2>&1
%PIP% install --quiet nuitka ordered-set zstandard >nul 2>&1
if %errorlevel% neq 0 (
  echo ERROR: Failed to install Nuitka dependencies.
  exit /b 1
)

REM Use trimmed requirements file to avoid kivy build issues
if exist requirements_nuitka.txt (
  echo Using trimmed requirements_nuitka.txt (no Kivy)...
  %PIP% install --quiet -r requirements_nuitka.txt
) else (
  echo requirements_nuitka.txt missing; falling back to requirements.txt
  %PIP% install --quiet -r requirements.txt
)

REM Create output dir clean
if exist dist_nuitka rmdir /s /q dist_nuitka
mkdir dist_nuitka

REM Build command notes:
REM --standalone: produce folder with dependencies
REM --nofollow-import-to=tests: exclude tests
REM --enable-plugin=tk-inter: PySimpleGUI uses tkinter
REM --include-data-dir: copy resource dirs
REM --include-data-files: copy single files
REM --python-flag=no_site: marginal startup improvement
REM --company-name etc: embed metadata (optional)

set CMD=%PY% -m nuitka --standalone --assume-yes-for-downloads ^
  --enable-plugin=tk-inter ^
  --nofollow-import-to=tests ^
  --include-data-dir=MEDIA=MEDIA ^
  --include-data-dir=src\libs\win=libs\win ^
  --include-data-files=MEDIA\logo.ico=logo.ico ^
  --include-package=core --include-package=ui --include-package=utils --include-package=services --include-package=parsing --include-package=media ^
  --python-flag=no_site ^
  --output-dir=dist_nuitka ^
  --remove-output ^
  %EXTRA_FLAGS% ^
  src\main.py

echo Step 2: Compiling with Nuitka (this can take several minutes on first run)...
%CMD%
if %errorlevel% neq 0 (
  echo ERROR: Nuitka build failed.
  exit /b 1
)

REM Copy VLC DLLs to top-level if present for faster discovery
if exist "src\libs\win\libvlc.dll" copy /Y "src\libs\win\libvlc.dll" "dist_nuitka\main.dist\libvlc.dll" >nul
if exist "src\libs\win\libvlccore.dll" copy /Y "src\libs\win\libvlccore.dll" "dist_nuitka\main.dist\libvlccore.dll" >nul
if exist "src\libs\win\plugins" xcopy /E /I /Y /Q "src\libs\win\plugins" "dist_nuitka\main.dist\plugins" >nul

REM Rename main.exe to ZedTV-IPTV-Player.exe for consistency
if exist "dist_nuitka\main.dist\main.exe" (
  move /Y "dist_nuitka\main.dist\main.exe" "dist_nuitka\main.dist\ZedTV-IPTV-Player.exe" >nul
)

echo.
echo Build complete.
echo Folder: dist_nuitka\main.dist
if exist "dist_nuitka\main.dist\ZedTV-IPTV-Player.exe" (
  echo Run: dist_nuitka\main.dist\ZedTV-IPTV-Player.exe
) else (
  echo Executable not found - check build_report.html
)

echo Startup tips:
echo  - First run still warms DLLs; subsequent runs should be faster than PyInstaller.
echo  - Use the 'quick' argument for a faster dev compile: nuitka_build.bat quick

echo Done.
popd
endlocal
