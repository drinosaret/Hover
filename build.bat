@echo off
setlocal enabledelayedexpansion

echo Cleaning previous builds...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "__pycache__" rd /s /q "__pycache__"

echo Building Hover executable...
echo.

REM Extract version information
python -c "from version import __version__; print(__version__)" > temp_version.txt
set /p VERSION=<temp_version.txt
del temp_version.txt
echo Detected version: !VERSION!

REM No manifest needed

REM Check if virtual environment exists
if exist .venv\ (
    echo Using virtual environment...
    .venv\Scripts\python.exe -m PyInstaller hover.spec
) else (
    echo Using system Python...
    python -m PyInstaller hover.spec
)

if !ERRORLEVEL! EQU 0 (
    echo.
    echo Build successful!
    
    REM Rename the executable with version
    if exist "dist\hover.exe" (
        ren "dist\hover.exe" "hover-v!VERSION!.exe"
        echo Created executable: dist\hover-v!VERSION!.exe
    ) else (
        echo Warning: hover.exe not found in dist folder
    )
    echo.
    pause
) else (
    echo.
    echo Build failed!
    echo.
    pause
)


