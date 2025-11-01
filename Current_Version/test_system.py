#!/usr/bin/env python3
"""
Smart Cursor Control - System Test
Test script to verify the system works correctly
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import time

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")

    required_modules = [
        'cv2', 'mediapipe', 'pyautogui', 'PIL', 'numpy', 'mss'
    ]

    failed_imports = []

    for module in required_modules:
        try:
            if module == 'cv2':
                import cv2
                print(f"✅ {module} imported successfully")
            elif module == 'PIL':
                import PIL
                print(f"✅ {module} imported successfully")
            else:
                __import__(module)
                print(f"✅ {module} imported successfully")
        except ImportError as e:
            print(f"❌ {module} import failed: {e}")
            failed_imports.append(module)

    if failed_imports:
        print(f"\n⚠️  Some modules failed to import: {', '.join(failed_imports)}")
        print("The system may work in limited mode without these modules.")
    else:
        print("\n✅ All essential modules imported successfully!")

    return len(failed_imports) == 0

def test_camera():
    """Test camera access"""
    print("\nTesting camera access...")

    try:
        import cv2
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print("✅ Camera accessible and working")
                cap.release()
                return True
            else:
                print("❌ Camera opened but cannot read frames")
                cap.release()
                return False
        else:
            print("❌ Cannot open camera")
            return False

    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def test_gui():
    """Test GUI creation"""
    print("\nTesting GUI creation...")

    try:
        root = tk.Tk()
        root.title("Test Window")
        root.geometry("300x200")

        label = tk.Label(root, text="GUI Test Successful!")
        label.pack(pady=20)

        # Close after 1 second
        root.after(1000, root.destroy)
        root.mainloop()

        print("✅ GUI creation successful")
        return True

    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        return False

def test_mouse_control():
    """Test mouse control library"""
    print("\nTesting mouse control...")

    try:
        import pyautogui

        # Get current position (safe test)
        current_pos = pyautogui.position()
        print(f"✅ Mouse position accessible: {current_pos}")
        return True

    except Exception as e:
        print(f"❌ Mouse control test failed: {e}")
        return False

def run_full_test():
    """Run complete system test"""
    print("🔍 Smart Cursor Control - System Test")
    print("=" * 50)

    results = {
        'imports': test_imports(),
        'camera': test_camera(),
        'gui': test_gui(),
        'mouse': test_mouse_control()
    }

    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print("=" * 50)

    all_passed = True
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test.upper():<10}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 50)

    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("The Smart Cursor system should work correctly.")
        print("\n🚀 You can now run:")
        print("   python Launchers/launcher_stable.py")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("The system may work in limited mode.")
        print("Check the error messages above for details.")
        print("\n🔧 Try running:")
        print("   python Core/demo_mode.py")
        print("   (to test camera separately)")

    print("\n📖 For help, check Docs/QUICK_START.md")
    print("=" * 50)

    return all_passed

if __name__ == "__main__":
    try:
        success = run_full_test()
        input("\nPress Enter to close...")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        sys.exit(1)
