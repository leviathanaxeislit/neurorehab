# NeuroWell - Building an Executable

This document explains how to build a standalone executable version of the NeuroWell application.

## Prerequisites

1. Python 3.8 or later installed
2. All required dependencies installed (see `requirements.txt`)
3. Windows operating system (for .exe output)

## Building the Executable

### Method 1: Using the Batch File (Recommended for Windows Users)

1. Simply double-click the `build_neurowell_exe.bat` file
2. The script will:
   - Activate your virtual environment if it exists (recommended)
   - Install PyInstaller if not already installed
   - Build the executable
   - Create a batch file to run the executable

### Method 2: Using Python Directly

1. Open a command prompt in the `native app` directory
2. Activate your virtual environment (if you're using one):
   ```
   venv\Scripts\activate
   ```
3. Run the build script:
   ```
   python build_exe.py
   ```

## Output Files

After running the build script, you'll find:

1. `dist/NeuroWell.exe` - The standalone executable file
2. `Run_NeuroWell.bat` - A batch file to easily run the executable

## Customizing the Build

You can modify `build_exe.py` to customize how the executable is built:

- Change `--onefile` to `--onedir` if you prefer a directory with multiple files instead of a single executable
- Add more `--add-data` entries if your application needs additional files
- Add any other PyInstaller options as needed

## Troubleshooting

### Images Directory Not Found

If you get an error like "Unable to find 'images' when adding binary and data files":

1. Create an 'images' directory in the 'native app' folder if it doesn't exist
2. Place any required images in this directory
3. The script will now automatically detect if the images directory exists and include it in the build

### Missing DLLs or Modules

If the executable fails to run due to missing DLLs or modules:

1. Edit `build_exe.py`
2. Add the specific modules to PyInstaller's hidden imports:
   ```python
   command.append("--hidden-import=MODULE_NAME")
   ```
3. Rebuild the executable

### OpenCV Issues

If you encounter issues with OpenCV:

1. Edit `build_exe.py`
2. Add the following to the command:
   ```python
   command.append("--hidden-import=cv2")
   command.append("--hidden-import=cv2.cv2")
   ```

### MediaPipe Issues

If you encounter issues with MediaPipe:

1. Edit `build_exe.py`
2. Add the following to the command:
   ```python
   command.append("--hidden-import=mediapipe")
   ```

## Additional Notes

- The executable may take some time to start the first time it runs
- Antivirus software may initially flag the executable (this is normal for PyInstaller-built applications)
- If you make changes to the application code, you'll need to rebuild the executable 