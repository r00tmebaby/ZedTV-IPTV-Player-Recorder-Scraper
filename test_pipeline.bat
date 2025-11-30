@echo off
REM ========================================
REM Local CI/CD Pipeline Tester
REM Tests: Linting, Type Checking, Unit Tests, and Build
REM ========================================

setlocal enabledelayedexpansion
set ERROR_COUNT=0
set SUCCESS_COUNT=0

echo.
echo ============================================================
echo   ZedTV IPTV Player - Local Pipeline Test
echo ============================================================
echo.
echo This script will run all CI/CD pipeline steps locally:
echo   1. Code formatting check (black)
echo   2. Import sorting check (isort)
echo   3. Type checking (mypy)
echo   4. Unit tests
echo   5. Build application
echo.
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found at .venv
    echo Please run: python -m venv .venv
    echo Then: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo.

REM ========================================
REM STEP 0: Install/Update Testing Tools
REM ========================================
echo ============================================================
echo STEP 0: Checking testing tools...
echo ============================================================
echo.

echo Installing/updating linting and testing tools...
pip install --quiet --upgrade mypy isort black pytest flake8 2>nul
if errorlevel 1 (
    echo WARNING: Some tools may not have been installed properly
) else (
    echo ✓ Testing tools ready
)
echo.

REM ========================================
REM STEP 1: Black - Code Formatting Check
REM ========================================
echo ============================================================
echo STEP 1: Running Black (Code Formatting Check)
echo ============================================================
echo.

echo Checking code formatting with black...
black --check src tests --exclude "(PySimpleGUI\.py|player\.py)" 2>&1
if errorlevel 1 (
    echo.
    echo ✗ FAILED: Code formatting issues found
    echo.
    echo To fix automatically, run:
    echo   black src tests --exclude "(PySimpleGUI\.py|player\.py)"
    echo.
    set /a ERROR_COUNT+=1
) else (
    echo.
    echo ✓ PASSED: Code formatting is correct
    echo.
    set /a SUCCESS_COUNT+=1
)

REM ========================================
REM STEP 2: isort - Import Sorting Check
REM ========================================
echo ============================================================
echo STEP 2: Running isort (Import Sorting Check)
echo ============================================================
echo.

echo Checking import sorting with isort...
isort --check-only src tests --skip PySimpleGUI.py --skip player.py 2>&1
if errorlevel 1 (
    echo.
    echo ✗ FAILED: Import sorting issues found
    echo.
    echo To fix automatically, run:
    echo   isort src tests --skip PySimpleGUI.py --skip player.py
    echo.
    set /a ERROR_COUNT+=1
) else (
    echo.
    echo ✓ PASSED: Import sorting is correct
    echo.
    set /a SUCCESS_COUNT+=1
)

REM ========================================
REM STEP 3: MyPy - Type Checking
REM ========================================
echo ============================================================
echo STEP 3: Running MyPy (Type Checking)
echo ============================================================
echo.

echo Checking types with mypy...
mypy src 2>&1
set MYPY_RESULT=%errorlevel%
echo.
if %MYPY_RESULT% equ 0 (
    echo ✓ PASSED: No type errors found
    set /a SUCCESS_COUNT+=1
) else (
    echo ⚠ WARNING: Type checking found issues
    echo Note: Type checking errors don't fail the build
    echo.
)

REM ========================================
REM STEP 4: Flake8 - Linting (Optional)
REM ========================================
echo ============================================================
echo STEP 4: Running Flake8 (Code Linting - Optional)
echo ============================================================
echo.

echo Checking code quality with flake8...
flake8 src tests 2>&1
if errorlevel 1 (
    echo.
    echo ⚠ WARNING: Linting issues found
    echo Note: Linting warnings don't fail the build
    echo.
) else (
    echo.
    echo ✓ PASSED: No linting issues
    echo.
)

REM ========================================
REM STEP 5: Unit Tests
REM ========================================
echo ============================================================
echo STEP 5: Running Unit Tests
echo ============================================================
echo.

echo Running all unit tests...
python -m pytest tests -v --tb=short 2>&1
if errorlevel 1 (
    echo.
    echo ✗ FAILED: Unit tests failed
    echo.
    set /a ERROR_COUNT+=1
) else (
    echo.
    echo ✓ PASSED: All unit tests passed
    echo.
    set /a SUCCESS_COUNT+=1
)


REM ========================================
REM STEP 7: Build Application
REM ========================================
echo ============================================================
echo STEP 7: Building Application
echo ============================================================
echo.

if %ERROR_COUNT% gtr 0 (
    echo ⚠ WARNING: There are %ERROR_COUNT% failed checks
    echo.
    set /p BUILD_ANYWAY="Do you want to build anyway? (y/N): "
    if /i not "!BUILD_ANYWAY!"=="y" (
        echo.
        echo Build skipped due to failed checks.
        goto :summary
    )
)

echo Building application with PyInstaller...
echo.
call build.bat
if errorlevel 1 (
    echo.
    echo ✗ FAILED: Build failed
    echo.
    set /a ERROR_COUNT+=1
) else (
    echo.
    echo ✓ PASSED: Build successful
    echo.
    set /a SUCCESS_COUNT+=1
)

REM ========================================
REM SUMMARY
REM ========================================
:summary
echo.
echo ============================================================
echo   PIPELINE TEST SUMMARY
echo ============================================================
echo.
echo Tests Passed:    %SUCCESS_COUNT%
echo Tests Failed:    %ERROR_COUNT%
echo.

if %ERROR_COUNT% equ 0 (
    echo ✓✓✓ ALL CHECKS PASSED! ✓✓✓
    echo.
    echo Your code is ready to:
    echo   - Commit to Git
    echo   - Push to repository
    echo   - Deploy to production
    echo.

    REM Check if executable exists
    if exist "dist\ZedTV-IPTV-Player\ZedTV-IPTV-Player.exe" (
        echo Built executable location:
        echo   dist\ZedTV-IPTV-Player\ZedTV-IPTV-Player.exe
        echo.
        set /p RUN_APP="Do you want to run the application now? (y/N): "
        if /i "!RUN_APP!"=="y" (
            start "" "dist\ZedTV-IPTV-Player\ZedTV-IPTV-Player.exe"
        )
    )

    exit /b 0
) else (
    echo ✗✗✗ SOME CHECKS FAILED ✗✗✗
    echo.
    echo Please review the errors above and fix them before:
    echo   - Committing to Git
    echo   - Pushing to repository
    echo   - Deploying to production
    echo.
    exit /b 1
)

