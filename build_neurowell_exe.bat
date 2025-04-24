@echo off
echo NeuroWell EXE Builder
echo ====================

REM Check if virtual environment exists and activate it
if exist venv\Scripts\activate (
    echo Activating virtual environment...
    call venv\Scripts\activate
) else (
    echo No virtual environment found. Using system Python.
)

REM Run the build script
echo Running build script...
python build_exe.py

REM Pause to keep the window open
echo.
echo Press any key to exit...
pause > nul 