@echo off
setlocal enabledelayedexpansion
echo Building Hover executable...
echo.

REM Check if virtual environment exists
if exist .venv\ (
    echo Using virtual environment...
    .venv\Scripts\python.exe -m PyInstaller hover.spec
    if !ERRORLEVEL! EQU 0 (
        echo.
        echo Build successful! 
        
        REM Extract version and rename executable
        echo Extracting version information...
        .venv\Scripts\python.exe get_version.py > temp_version.txt
        set /p VERSION=<temp_version.txt
        del temp_version.txt
        echo Detected version: !VERSION!
        
        if exist "dist\hover.exe" (
            if not "!VERSION!" == "unknown" if not "!VERSION!" == "" (
                ren "dist\hover.exe" "hover-v!VERSION!.exe"
                echo Executable renamed to: dist\hover-v!VERSION!.exe
            ) else (
                echo Warning: Could not detect version, keeping original name as hover.exe
            )
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
) else (
    echo Using system Python...
    python -m PyInstaller hover.spec
    if !ERRORLEVEL! EQU 0 (
        echo.
        echo Build successful! 
        
        REM Extract version and rename executable
        echo Extracting version information...
        python get_version.py > temp_version.txt
        set /p VERSION=<temp_version.txt
        del temp_version.txt
        echo Detected version: !VERSION!
        
        if exist "dist\hover.exe" (
            if not "!VERSION!" == "unknown" if not "!VERSION!" == "" (
                ren "dist\hover.exe" "hover-v!VERSION!.exe"
                echo Executable renamed to: dist\hover-v!VERSION!.exe
            ) else (
                echo Warning: Could not detect version, keeping original name as hover.exe
            )
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
)
