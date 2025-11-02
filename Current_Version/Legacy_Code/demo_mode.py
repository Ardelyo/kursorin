#!/usr/bin/env python3
"""
Smart Cursor Control - Demo Mode
Simple demonstration mode that works even with limited dependencies
"""

import cv2
import numpy as np
import tkinter as tk
from tkinter import messagebox
import time
import sys

def run_demo():
    """Run a simple demo of the cursor system"""
    print("Starting Smart Cursor Demo Mode...")
    print("This mode demonstrates basic camera tracking without full cursor control.")

    # Try to open camera
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            raise Exception("Cannot open camera")
    except Exception as e:
        messagebox.showerror("Demo Error",
                           f"Cannot access camera: {e}\n\n"
                           "Please ensure:\n"
                           "1. Camera is connected\n"
                           "2. Camera is not used by other apps\n"
                           "3. Camera permissions are granted")
        return

    print("Camera opened successfully!")
    messagebox.showinfo("Demo Started",
                       "Demo mode started!\n\n"
                       "You'll see your camera feed with basic tracking.\n"
                       "Press 'Q' to quit the demo.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame")
                break

            # Flip frame horizontally
            frame = cv2.flip(frame, 1)

            # Add demo text
            cv2.putText(frame, "SMART CURSOR DEMO MODE", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Press 'Q' to exit demo", (50, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, "This is basic camera tracking", (50, 150),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

            # Show frame
            cv2.imshow('Smart Cursor - Demo Mode', frame)

            # Check for quit key
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

            time.sleep(0.03)  # ~30 FPS

    except KeyboardInterrupt:
        print("Demo interrupted")
    except Exception as e:
        print(f"Demo error: {e}")
        messagebox.showerror("Demo Error", f"Demo encountered an error: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Demo completed!")

if __name__ == "__main__":
    run_demo()
