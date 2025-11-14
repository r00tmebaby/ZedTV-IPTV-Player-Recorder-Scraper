@echo off
REM Convenience wrapper for Windows quick test script
REM This calls the actual test script in build_scripts/windows/

call "%~dp0build_scripts\windows\quick_test.bat" %*
@echo off
REM Convenience wrapper for Windows test script
REM This calls the actual test script in build_scripts/windows/

call "%~dp0build_scripts\windows\run_tests.bat" %*

