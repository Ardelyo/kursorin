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
        print("❌ Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]}")
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
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")

    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
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
                print("✅ Camera accessible")
                return True
        print("❌ Camera not accessible")
        return False
    except Exception as e:
        print(f"❌ Camera check failed: {e}")
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
        print("\n🚀 Launching Smart Cursor Control...")

        # Add current directory to Python path
        current_dir = Path(__file__).parent
        core_dir = current_dir / "Core"
        modules_dir = core_dir / "modules"

        if str(modules_dir) not in sys.path:
            sys.path.insert(0, str(modules_dir))

        # Import and launch the application
        from main_application import main
        main()

    except ImportError as e:
        print(f"❌ Failed to import application modules: {e}")
        print("Make sure you're running this from the Current_Version directory")
        return False
    except Exception as e:
        print(f"❌ Failed to launch application: {e}")
        logging.error(f"Launch error: {e}")
        return False

    return True


def main():
    """Main launcher function"""
    print("🖱️  Smart Cursor Control - Modular Version")
    print("=" * 50)

    # Check system requirements
    print("\n📋 Checking system requirements...")

    checks_passed = True

    if not check_python_version():
        checks_passed = False

    if not check_dependencies():
        checks_passed = False

    if not check_camera():
        print("⚠️  Camera not accessible - application may not work properly")

    if not checks_passed:
        print("\n❌ System check failed. Please fix the issues above and try again.")
        input("Press Enter to exit...")
        return

    print("\n✅ All checks passed!")

    # Setup logging
    setup_logging()

    # Launch application
    if not launch_application():
        print("\n❌ Failed to launch application")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
