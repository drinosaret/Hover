@echo off
echo Building Hover executable...
echo.

REM Check if virtual environment exists
if exist .venv\ (
    echo Using virtual environment...
    .venv\Scripts\python.exe -m PyInstaller hover.spec
    set PYTHON_CMD=.venv\Scripts\python.exe
) else (
    echo Using system Python...
    python -m PyInstaller hover.spec
    set PYTHON_CMD=python
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful! 
    
    REM Extract version and rename executable
    for /f %%i in ('%PYTHON_CMD% -c "import version; print(version.__version__)"') do set VERSION=%%i
    echo Detected version: %VERSION%
    
    if exist "dist\hover.exe" (
        ren "dist\hover.exe" "hover-v%VERSION%.exe"
        echo Executable renamed to: dist\hover-v%VERSION%.exe
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
