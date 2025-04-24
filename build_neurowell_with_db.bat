@echo off
echo NeuroWell EXE Builder with SQLite Database
echo =======================================

REM Check if virtual environment exists and activate it
if exist venv\Scripts\activate (
    echo Activating virtual environment...
    call venv\Scripts\activate
) else (
    echo No virtual environment found. Using system Python.
)

REM First create the SQLite database
echo Creating SQLite database...
python create_database.py

REM Then run the build script to create the executable
echo Building executable...
python build_exe.py

REM Pause to keep the window open
echo.
echo Press any key to exit...
pause > nul 