@echo off
REM Quick Pipeline Test - Simplified Version

REM Change to project root (two levels up)
pushd "%~dp0..\.."

echo.
echo ========================================
echo Quick Pipeline Test
echo ========================================
echo.

REM Activate venv
call .venv\Scripts\activate.bat

echo Step 1: Installing tools...
pip install --quiet black isort mypy pytest flake8
echo.

echo Step 2: Running Black...
black --check src tests --exclude "(PySimpleGUI\.py|player\.py)"
if errorlevel 1 (echo FAILED: Black) else (echo PASSED: Black)
echo.

echo Step 3: Running isort...
isort --check-only src tests --skip PySimpleGUI.py --skip player.py
if errorlevel 1 (echo FAILED: isort) else (echo PASSED: isort)
echo.

echo Step 4: Running tests...
python -m pytest tests -v
if errorlevel 1 (echo FAILED: Tests) else (echo PASSED: Tests)
echo.

echo Step 5: Version check...
python verify_version_system.py
if errorlevel 1 (echo FAILED: Version) else (echo PASSED: Version)
echo.

echo ========================================
echo Pipeline test complete!
echo ========================================
pause

