import os
import sys
import subprocess
import platform

def set_environment_variables():
    """Set environment variables that may help with hand detection"""
    # Force CPU usage for MediaPipe (can be more stable than GPU)
    os.environ["MEDIAPIPE_CPU_ONLY"] = "1"
    
    # Higher log level for MediaPipe to reduce noise
    os.environ["GLOG_minloglevel"] = "2"
    
    # Windows-specific environment variables
    if platform.system() == "Windows":
        # These can help with camera access on Windows
        os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "1"
        
        # Ensure mediapipe can find its dependencies
        # Get the current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # If running from an executable, use appropriate path
        if getattr(sys, 'frozen', False):
            # Running as exe
            app_path = os.path.dirname(sys.executable)
        else:
            # Running as script
            app_path = script_dir
            
        # Set DLL path for Windows
        os.environ["PATH"] = app_path + os.pathsep + os.environ.get("PATH", "")
    
    # Print diagnostic info
    print(f"Running on {platform.system()} {platform.release()}")
    print(f"Python version: {platform.python_version()}")

def run_camera_test():
    """Run the camera test to verify webcam access and hand detection"""
    print("\nRunning camera test...")
    
    # Construct the path to camera_test.py
    if getattr(sys, 'frozen', False):
        # Running as exe
        test_script = os.path.join(os.path.dirname(sys.executable), "camera_test.py")
    else:
        # Running as script
        test_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "camera_test.py")
    
    try:
        subprocess.run([sys.executable, test_script])
    except Exception as e:
        print(f"Error running camera test: {e}")

def main():
    print("NeuroWell Launcher")
    print("=================")
    print("This script helps ensure proper environment setup for hand detection.")
    
    # Set environment variables
    set_environment_variables()
    
    # Ask if user wants to run camera test first
    while True:
        choice = input("\nDo you want to run the camera test first? (y/n): ").lower()
        if choice in ['y', 'yes']:
            run_camera_test()
            break
        elif choice in ['n', 'no']:
            break
        else:
            print("Please enter 'y' for yes or 'n' for no.")
    
    # Run the main application
    print("\nStarting NeuroWell application...")
    
    # Construct the path to main.py
    if getattr(sys, 'frozen', False):
        # Running as exe
        main_script = os.path.join(os.path.dirname(sys.executable), "main.py")
    else:
        # Running as script
        main_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    
    try:
        subprocess.run([sys.executable, main_script])
    except Exception as e:
        print(f"Error starting NeuroWell: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Unexpected error: {e}")
        input("Press Enter to exit...") 