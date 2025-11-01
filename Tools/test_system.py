#!/usr/bin/env python3
"""
Test script for Camera Cursor System v3
Tests basic functionality without running full system
"""

import cv2
import mediapipe as mp
import numpy as np
import sys
import time

def test_imports():
    """Test if all required modules can be imported"""
    try:
        import pyautogui
        import tkinter
        import logging
        import signal
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_webcam():
    """Test webcam access"""
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                print("✅ Webcam access successful")
                return True
            else:
                print("❌ Cannot read from webcam")
                return False
        else:
            print("❌ Cannot open webcam")
            return False
    except Exception as e:
        print(f"❌ Webcam error: {e}")
        return False

def test_mediapipe():
    """Test MediaPipe Holistic initialization"""
    try:
        mp_holistic = mp.solutions.holistic
        holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        # Test with a dummy frame
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        dummy_rgb = cv2.cvtColor(dummy_frame, cv2.COLOR_BGR2RGB)
        results = holistic.process(dummy_rgb)

        holistic.close()
        print("✅ MediaPipe Holistic working")
        return True
    except Exception as e:
        print(f"❌ MediaPipe error: {e}")
        return False

def test_screen_size():
    """Test screen size detection"""
    try:
        import pyautogui
        width, height = pyautogui.size()
        print(f"✅ Screen size: {width}x{height}")
        return True
    except Exception as e:
        print(f"❌ Screen size error: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("🧪 Testing Camera Cursor System v3...")
    print("=" * 40)

    tests = [
        ("Imports", test_imports),
        ("Webcam", test_webcam),
        ("MediaPipe", test_mediapipe),
        ("Screen Size", test_screen_size),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        time.sleep(0.5)  # Small delay between tests

    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! System should work correctly.")
        print("💡 Run 'python camera_cursor_v3.py' to start the system")
        return True
    else:
        print("⚠️  Some tests failed. Check dependencies and hardware.")
        print("🔧 Make sure you have:")
        print("   - Working webcam")
        print("   - Python 3.x")
        print("   - All packages from requirements.txt installed")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
