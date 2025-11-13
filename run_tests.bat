@echo off
REM Run all tests using unittest discovery (replaces missing test_suite.py)

echo ========================================
echo Running Test Suite
echo ========================================
echo.

python -m unittest discover -s tests -p "test_*.py"

if %errorlevel% neq 0 (
    echo.
    echo TESTS FAILED!
    pause
    exit /b 1
) else (
    echo.
    echo ALL TESTS PASSED!
    pause
    exit /b 0
)
