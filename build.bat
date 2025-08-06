@echo off
echo Building Hover executable...
echo.

REM Check if virtual environment exists
if exist .venv\ (
    echo Using virtual environment...
    .venv\Scripts\python.exe -m PyInstaller hover.spec
) else (
    echo Using system Python...
    python -m PyInstaller hover.spec
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful! 
    echo Executable created: dist\hover.exe
    echo.
    pause
) else (
    echo.
    echo Build failed!
    echo.
    pause
)
