#!/usr/bin/env python3
"""
Test script to verify that all modules can be imported correctly
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test importing all modules"""
    print("Testing module imports...")

    # Add modules directory to path
    current_dir = Path(__file__).parent
    modules_dir = current_dir / "Core" / "modules"

    if str(modules_dir) not in sys.path:
        sys.path.insert(0, str(modules_dir))

    print(f"Modules directory: {modules_dir}")

    try:
        # Test imports
        print("Importing settings_manager...")
        import settings_manager
        print("OK - settings_manager imported")

        print("Importing gui_components...")
        import gui_components
        print("OK - gui_components imported")

        print("Importing cursor_control...")
        import cursor_control
        print("OK - cursor_control imported")

        print("Importing gesture_recognition...")
        import gesture_recognition
        print("OK - gesture_recognition imported")

        print("Importing tracking_engines...")
        import tracking_engines
        print("OK - tracking_engines imported")

        print("Importing performance_optimizer...")
        import performance_optimizer
        print("OK - performance_optimizer imported")

        print("Importing main_application...")
        import main_application
        print("OK - main_application imported")

        print("\nSUCCESS: All imports successful!")

        # Test creating instances
        print("\nTesting class instantiation...")
        settings = settings_manager.SettingsManager()
        print("OK - SettingsManager created")

        return True

    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n🚀 Ready to run the application!")
    else:
        print("\n❌ Import test failed")
        sys.exit(1)
