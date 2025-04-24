import os
import sys
import subprocess
import shutil
from pathlib import Path
import pkg_resources
import time
import random
import string
import sqlite3

def check_if_exe_running(exe_name="NeuroWell.exe"):
    """Check if the executable is currently running"""
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == exe_name:
                return True
        return False
    except ImportError:
        # If psutil isn't available, return False and let the main function handle it
        return False

def try_delete_file(file_path, max_attempts=3, delay=1):
    """Try to delete a file multiple times with delay between attempts"""
    for attempt in range(max_attempts):
        try:
            if file_path.exists():
                os.remove(file_path)
            return True
        except PermissionError:
            if attempt < max_attempts - 1:
                print(f"File is locked, retrying in {delay} seconds... (attempt {attempt+1}/{max_attempts})")
                time.sleep(delay)
            else:
                return False
    return True

def ensure_database_exists():
    """Ensure the SQLite database exists and is properly seeded"""
    db_path = Path("neurowell.db")
    
    if not db_path.exists():
        print("SQLite database not found. Creating one with sample data...")
        try:
            # First try to import and run the dedicated script
            try:
                from create_database import create_database
                create_database()
                return True
            except ImportError:
                print("Could not import create_database module. Creating simple database...")
                
            # If that fails, create a simple database directly
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create basic patients table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                speech_score REAL,
                emoji_score REAL,
                snake_score REAL,
                ball_score REAL
            )
            ''')
            
            # Add some sample data
            patients = [
                ('John Smith', 68, 'Male', 75.5, 82.0, 65.0, 70.0),
                ('Mary Johnson', 72, 'Female', 68.0, 75.5, 60.0, 62.5),
                ('Robert Davis', 65, 'Male', 80.0, 78.5, 72.0, 75.0)
            ]
            
            cursor.executemany('''
            INSERT INTO patients 
            (name, age, gender, speech_score, emoji_score, snake_score, ball_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', patients)
            
            conn.commit()
            conn.close()
            print("Simple database created successfully.")
            return True
            
        except Exception as e:
            print(f"Error creating database: {e}")
            return False
    
    return True

def build_exe():
    """
    Build an executable version of the NeuroWell application using PyInstaller.
    """
    print("NeuroWell Application - EXE Builder")
    print("===================================")
    
    # Check for psutil, install if not available
    try:
        import psutil
        print("psutil is already installed.")
    except ImportError:
        print("Installing psutil...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        # Try importing again
        try:
            import psutil
            print("psutil installed successfully.")
        except ImportError:
            print("Warning: Could not install psutil. Some file locking checks will be skipped.")
    
    # Check if PyInstaller is installed, if not install it
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyInstaller"])
        print("PyInstaller installed successfully.")
    
    # Check if the executable is currently running
    if check_if_exe_running("NeuroWell.exe"):
        print("\nWARNING: NeuroWell.exe is currently running!")
        print("The build will fail if the executable is in use.")
        print("Please close the application before continuing.")
        input("Press Enter to continue once you've closed the application, or Ctrl+C to cancel...")
    
    # Create spec file directory if it doesn't exist
    spec_dir = Path("build_specs")
    spec_dir.mkdir(exist_ok=True)
    
    # Generate path to main script
    main_script = Path("main.py").absolute()
    
    # Check if the main script exists
    if not main_script.exists():
        print(f"Error: Could not find {main_script}")
        return
    
    # Check if the previous build exists and try to remove it
    dist_dir = Path("dist").absolute()
    exe_path = dist_dir / "NeuroWell.exe"
    
    if exe_path.exists():
        print(f"Previous build found at {exe_path}")
        
        if not try_delete_file(exe_path):
            print("\nERROR: Cannot delete the existing executable. It may be in use.")
            print("Options:")
            print("1. Close any running instances of NeuroWell and try again")
            print("2. Use a different output name for this build")
            
            choice = input("Enter option (1 or 2, default: 1): ").strip() or "1"
            
            if choice == "1":
                print("Please close all instances of NeuroWell and try again.")
                return
            else:
                # Generate a unique name
                random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
                output_name = f"NeuroWell_{random_suffix}"
                print(f"Using alternative name: {output_name}")
        else:
            output_name = "NeuroWell"
    else:
        output_name = "NeuroWell"
    
    # Define icon path (use default if not available)
    icon_path = Path("images/logo.ico").absolute()
    icon_exists = icon_path.exists()
    icon_param = f"--icon={icon_path}" if icon_exists else ""
    if not icon_exists:
        print("Note: No icon file found at", icon_path)
    
    # Process data directories
    data_params = []
    
    # Check for images directory
    images_dir = Path("images").absolute()
    if images_dir.exists() and images_dir.is_dir():
        print(f"Adding images directory: {images_dir}")
        data_params.append(f"--add-data={images_dir}{os.pathsep}images")
    else:
        print(f"Warning: Images directory not found at {images_dir}")
        print("Creating empty images directory to prevent errors...")
        images_dir.mkdir(exist_ok=True)
        data_params.append(f"--add-data={images_dir}{os.pathsep}images")
    
    # Ensure SQLite database exists and add it to the package
    if ensure_database_exists():
        db_path = Path("neurowell.db").absolute()
        print(f"Adding SQLite database: {db_path}")
        data_params.append(f"--add-data={db_path}{os.pathsep}.")
    else:
        print("WARNING: Could not create or find SQLite database.")
    
    # Add MediaPipe hand detection models
    try:
        import mediapipe
        mediapipe_path = Path(mediapipe.__file__).parent
        
        # Add only the necessary mediapipe directories to avoid model_maker errors
        print(f"Adding MediaPipe package (excluding model_maker): {mediapipe_path}")
        
        # Add subdirectories individually instead of the entire mediapipe package
        important_dirs = [
            "modules",          # Contains hand landmark models
            "calculators",      # Core MediaPipe calculators
            "python",           # Python interface
            "tasks",            # Task-specific modules
            "framework",        # Framework components
            "graphs",           # Graph configurations
            "util"              # Utility functions
        ]
        
        for subdir in important_dirs:
            dir_path = mediapipe_path / subdir
            if dir_path.exists() and dir_path.is_dir():
                print(f"  Adding MediaPipe subdirectory: {subdir}")
                data_params.append(f"--add-data={dir_path}{os.pathsep}mediapipe/{subdir}")
            
    except ImportError:
        print("Warning: MediaPipe not found, hand detection may not work")
    
    # Add cvzone directory
    try:
        import cvzone
        cvzone_path = Path(cvzone.__file__).parent
        print(f"Adding complete cvzone package: {cvzone_path}")
        data_params.append(f"--add-data={cvzone_path}{os.pathsep}cvzone")
    except ImportError:
        print("Warning: cvzone not found, hand tracking may not work")
    
    # Get all installed packages for comprehensive dependency collection
    print("Identifying all installed packages...")
    installed_packages = [dist.key for dist in pkg_resources.working_set]
    key_packages = [
        "pyqt5", "opencv-python", "mediapipe", "cvzone", "pandas", 
        "numpy", "matplotlib", "pillow", "pyaudio", "speechrecognition", "sqlite3"
    ]
    
    # Convert to lowercase for comparison
    installed_packages_lower = [pkg.lower() for pkg in installed_packages]
    
    # Check if key packages are installed
    print("Checking for key packages:")
    for pkg in key_packages:
        if pkg.lower() in installed_packages_lower or pkg.lower() == "sqlite3":  # sqlite3 is built-in
            print(f"✓ {pkg} is installed")
        else:
            print(f"✗ {pkg} is NOT installed - some features may not work")
    
    # Define comprehensive hidden imports for libraries
    hidden_imports = [
        # PyQt5 core
        "PyQt5", "PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui",
        "PyQt5.sip", "PyQt5.QtPrintSupport",
        
        # OpenCV
        "cv2", "cv2.cv2", 
        
        # MediaPipe - comprehensive imports
        "mediapipe", "mediapipe.python", "mediapipe.python.solution_base",
        "mediapipe.python.solutions", "mediapipe.python.solutions.hands",
        "mediapipe.python.solutions.drawing_utils", 
        "mediapipe.python.solutions.drawing_styles",
        "mediapipe.tasks.python", "mediapipe.framework.formats",
        
        # Data processing
        "pandas", "numpy", "numpy.core.multiarray",
        
        # Database
        "sqlite3",
        
        # Visualization
        "matplotlib", "matplotlib.backends.backend_qt5agg",
        "matplotlib.pyplot", "matplotlib.figure", "matplotlib.backends.backend_agg",
        
        # Image processing
        "PIL", "PIL._tkinter_finder", "PIL.Image", "PIL.ImageDraw", "PIL.ImageFont",
        
        # Audio processing
        "pyaudio", "speech_recognition", "sounddevice",
        
        # cvzone and its components
        "cvzone", "cvzone.HandTrackingModule", "cvzone.FaceMeshModule",
        "cvzone.FaceDetectionModule", "cvzone.SelfiSegmentationModule",
        "cvzone.ColorModule", "cvzone.PoseModule", "cvzone.Utils",
        
        # Other potential imports
        "random", "csv", "datetime", "json", "os", "sys", "math", "time",
        "requests", "urllib", "threading", "queue"
    ]
    
    # Convert hidden imports to command line parameters
    hidden_import_params = [f"--hidden-import={imp}" for imp in hidden_imports]
    
    # Exclude problematic modules
    excluded_modules = ["mediapipe.model_maker"]
    exclude_params = [f"--exclude-module={mod}" for mod in excluded_modules]
    
    # Define packaging mode - ask user for preference
    print("\nPackaging Options:")
    print("1. Single file (--onefile): Creates a single executable file")
    print("   + Advantage: Simple to distribute")
    print("   - Disadvantage: Slower startup, may have issues with some dependencies")
    print("\n2. Directory (--onedir): Creates a directory with executable and dependencies")
    print("   + Advantage: Faster startup, better compatibility")
    print("   - Disadvantage: Must distribute the entire directory")
    
    packaging_mode = input("\nChoose packaging mode (1 for onefile, 2 for onedir) [Default: 1]: ").strip()
    
    if packaging_mode == "2":
        packaging_option = "--onedir"
        print("Selected: Directory mode (--onedir)")
    else:
        packaging_option = "--onefile"
        print("Selected: Single file mode (--onefile)")
    
    # Build the PyInstaller command with more comprehensive options
    command = [
        sys.executable, 
        "-m", 
        "PyInstaller",
        f"--name={output_name}",
        packaging_option,
        "--windowed",  # No console window
        "--noconfirm",  # Overwrite existing build
        "--clean",  # Clean PyInstaller cache
        "--log-level=INFO",
        f"--specpath={spec_dir}",
        "--distpath=dist_temp",  # Use temporary directory to avoid permission issues
        *data_params,
        *hidden_import_params,
        *exclude_params,  # Add exclude parameters
        "--collect-submodules=mediapipe",  # Only collect submodules rather than all files
        "--collect-all=cvzone",     # Ensure all cvzone files are collected
        "--collect-all=PIL",        # Ensure all PIL files are collected
        "--collect-all=cv2",        # Ensure all OpenCV files are collected  
        "--collect-all=numpy",      # Ensure all NumPy files are collected
        "--collect-all=pandas",     # Ensure all Pandas files are collected
        "--collect-all=matplotlib", # Ensure all Matplotlib files are collected
        "--collect-all=PyQt5"       # Ensure all PyQt5 files are collected
    ]
    
    # Add icon if available
    if icon_param:
        command.append(icon_param)
    
    # Add main script
    command.append(str(main_script))
    
    # Run the PyInstaller command
    print("\nBuilding executable...")
    print(f"Command: {' '.join(command)}")
    
    try:
        subprocess.check_call(command)
        print("\nExecutable built successfully!")
        
        # Move the build from temporary directory to final location
        temp_dist = Path("dist_temp").absolute()
        final_dist = Path("dist").absolute()
        
        # Create final dist directory if it doesn't exist
        final_dist.mkdir(exist_ok=True)
        
        if packaging_option == "--onedir":
            temp_app_dir = temp_dist / output_name
            final_app_dir = final_dist / output_name
            
            # Remove the destination directory if it exists
            if final_app_dir.exists() and final_app_dir.is_dir():
                shutil.rmtree(final_app_dir, ignore_errors=True)
            
            # Move the directory
            print(f"Moving application from {temp_app_dir} to {final_app_dir}")
            shutil.move(str(temp_app_dir), str(final_app_dir))
            
            print(f"The application can be found in the 'dist/{output_name}' directory.")
            print(f"To run it, execute 'dist/{output_name}/{output_name}.exe'")
            
            # Create batch file for directory mode
            batch_path = Path(f"Run_{output_name}.bat")
            with open(batch_path, "w") as f:
                f.write("@echo off\n")
                f.write(f"echo Starting {output_name} Application...\n")
                f.write(f"start dist\\{output_name}\\{output_name}.exe\n")
        else:
            temp_exe = temp_dist / f"{output_name}.exe"
            final_exe = final_dist / f"{output_name}.exe"
            
            # Try to delete the destination file if it exists
            if final_exe.exists():
                try:
                    os.remove(final_exe)
                except PermissionError:
                    # If still can't delete, use a different name
                    random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                    final_exe = final_dist / f"{output_name}_{random_suffix}.exe"
            
            # Move the file
            print(f"Moving executable from {temp_exe} to {final_exe}")
            shutil.move(str(temp_exe), str(final_exe))
            
            print(f"The executable can be found at '{final_exe}'")
            
            # Create batch file for single file mode
            batch_path = Path(f"Run_{output_name}.bat")
            with open(batch_path, "w") as f:
                f.write("@echo off\n")
                f.write(f"echo Starting {output_name} Application...\n")
                f.write(f"start {final_exe}\n")
        
        # Clean up temporary directory
        if temp_dist.exists():
            shutil.rmtree(temp_dist, ignore_errors=True)
        
        print(f"\nCreated batch file: {batch_path}")
        print("Done!")
        
    except subprocess.CalledProcessError as e:
        print(f"\nError building executable: {e}")
        return

if __name__ == "__main__":
    build_exe() 