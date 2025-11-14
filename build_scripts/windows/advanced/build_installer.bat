@echo off
rem build_installer.bat - build the app using existing build.bat then create an Inno Setup installer
rem Usage:
rem   build_installer         - Full build + installer
rem   build_installer package - Skip build, just create installer/package from existing dist
setlocal enabledelayedexpansion

rem ============================================================
rem VERSION CONFIGURATION - Update this when releasing new version
rem ============================================================
set "APP_VERSION=2.0.0"
rem ============================================================

rem 1) Run existing build (unless 'package' mode)
if /i "%~1"=="package" (
  echo Skipping build - using existing dist folder...
  if not exist "dist\ZedTV-IPTV-Player\ZedTV-IPTV-Player.exe" (
    echo ERROR: No existing build found in dist folder!
    echo Run without 'package' parameter to build first.
    exit /b 1
  )
) else (
  echo Running project build.bat...
  call build.bat
  if %errorlevel% neq 0 (
    echo build.bat failed. Aborting installer build.
    exit /b 1
  )
)

rem 2) Version info
echo.
echo Using app version: %APP_VERSION%
echo.

rem 3) Check for Inno Setup compiler (ISCC.exe)
set "FALLBACK_ZIP="
where ISCC >nul 2>&1
if %errorlevel% neq 0 (
  echo Inno Setup not found in PATH.
  echo Install Inno Setup 6 and ensure ISCC.exe is on PATH.
  echo Download: https://jrsoftware.org/isdl.php
  echo.
  echo Falling back to ZIP packaging...
  set "FALLBACK_ZIP=1"
)

rem 4) Compile installer with Inno Setup if available
if "%FALLBACK_ZIP%"=="" (
  echo Compiling installer with ISCC.exe ...
  ISCC.exe /DMyAppVersion=%APP_VERSION% installer.iss
  if %errorlevel% neq 0 (
    echo Inno Setup failed.
    exit /b 3
  )
  echo.
  echo ========================================
  echo INSTALLER BUILD COMPLETE!
  echo ========================================
  echo.
  endlocal
  exit /b 0
)

rem 5) Fallback to ZIP package
echo.
echo Creating ZIP distribution package...
echo.
call create_package.bat
if %errorlevel% neq 0 (
  echo.
  echo ERROR: Packaging failed.
  endlocal
  exit /b 5
)
echo.
echo ========================================
echo ZIP PACKAGE CREATED SUCCESSFULLY!
echo ========================================
echo.
endlocal
exit /b 0

