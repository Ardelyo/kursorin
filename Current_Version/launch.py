#!/usr/bin/env python3
"""
Smart Cursor Control Launcher
Checks dependencies and launches the modular application
"""

import sys
import os
import subprocess
import logging
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"OK: Python {sys.version.split()[0]}")
    return True


def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'opencv-python',
        'mediapipe',
        'pyautogui',
        'numpy',
        'Pillow',
        'tkinter'  # Usually comes with Python
    ]

    missing_packages = []

    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'opencv-python':
                import cv2
            elif package == 'Pillow':
                import PIL
            else:
                __import__(package.replace('-', '_'))
            print(f"OK: {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"MISSING: {package}")

    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("\nTo install missing packages, run:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    return True


def check_camera():
    """Check if camera is available"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                print("OK: Camera accessible")
                return True
        print("WARNING: Camera not accessible")
        return False
    except Exception as e:
        print(f"ERROR: Camera check failed: {e}")
        return False


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('smart_cursor.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def launch_application():
    """Launch the main application"""
    try:
        print("\\nLaunching Smart Cursor Control...")

        # Add the modules directory to Python path
        current_dir = Path(__file__).parent
        modules_dir = current_dir / "Core" / "modules"

        if str(modules_dir) not in sys.path:
            sys.path.insert(0, str(modules_dir))

        # Import and launch the application
        import main_application
        main_application.main()

    except Exception as e:
        print(f"ERROR: Failed to launch application: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def main():
    """Main launcher function"""
    print("Smart Cursor Control - Modular Version")
    print("=" * 50)

    # Check system requirements
    print("\\nChecking system requirements...")

    checks_passed = True

    if not check_python_version():
        checks_passed = False

    if not check_dependencies():
        checks_passed = False

    if not check_camera():
        print("WARNING: Camera not accessible - application may not work properly")

    if not checks_passed:
        print("\\nERROR: System check failed. Please fix the issues above and try again.")
        input("Press Enter to exit...")
        return

    print("\\nSUCCESS: All checks passed!")

    # Setup logging
    setup_logging()

    # Launch application
    if not launch_application():
        print("\\nERROR: Failed to launch application")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
