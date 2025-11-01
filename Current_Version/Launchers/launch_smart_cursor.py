#!/usr/bin/env python3
"""
Smart Cursor Control Launcher
Easy-to-use launcher for the Smart Cursor Accessibility System
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import threading

class CursorLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Smart Cursor Control Launcher")
        self.root.geometry("400x300")
        self.root.resizable(False, False)

        # Center window
        self.root.eval('tk::PlaceWindow . center')

        self.create_ui()
        self.check_dependencies()

    def create_ui(self):
        """Create the launcher UI"""
        # Title
        title_label = ttk.Label(self.root, text="🖱️ Smart Cursor Control",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=20)

        subtitle_label = ttk.Label(self.root, text="Accessibility Edition",
                                  font=('Arial', 10))
        subtitle_label.pack(pady=(0, 20))

        # Status frame
        status_frame = ttk.LabelFrame(self.root, text="System Status")
        status_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        self.status_label = ttk.Label(status_frame, text="Checking system...")
        self.status_label.pack(pady=10)

        # Buttons frame
        buttons_frame = ttk.Frame(self.root)
        buttons_frame.pack(fill=tk.X, padx=20)

        self.launch_button = ttk.Button(buttons_frame, text="🚀 Launch Smart Cursor",
                                       command=self.launch_system, state=tk.DISABLED)
        self.launch_button.pack(fill=tk.X, pady=(0, 10))

        self.install_button = ttk.Button(buttons_frame, text="📦 Install Dependencies",
                                        command=self.install_dependencies)
        self.install_button.pack(fill=tk.X, pady=(0, 10))

        self.help_button = ttk.Button(buttons_frame, text="❓ Help & Documentation",
                                     command=self.show_help)
        self.help_button.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(buttons_frame, text="❌ Exit", command=self.root.quit).pack(fill=tk.X)

    def check_dependencies(self):
        """Check if required dependencies are installed"""
        required_packages = [
            'cv2', 'mediapipe', 'pyautogui', 'PIL', 'numpy',
            'sklearn', 'mss', 'pyttsx3', 'speech_recognition',
            'keyboard', 'mouse'
        ]

        missing_packages = []
        for package in required_packages:
            try:
                if package == 'cv2':
                    import cv2
                elif package == 'PIL':
                    import PIL
                elif package == 'sklearn':
                    import sklearn
                else:
                    __import__(package)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            self.status_label.config(text=f"❌ Missing: {', '.join(missing_packages)}",
                                   foreground='red')
            self.install_button.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="✅ All dependencies installed",
                                   foreground='green')
            self.launch_button.config(state=tk.NORMAL)

    def install_dependencies(self):
        """Install missing dependencies"""
        def install():
            try:
                self.status_label.config(text="📦 Installing dependencies...")
                self.install_button.config(state=tk.DISABLED)

                # Run pip install
                requirements_path = os.path.join(os.path.dirname(__file__), '..', 'Config', 'requirements.txt')
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-r', requirements_path
                ], capture_output=True, text=True)

                if result.returncode == 0:
                    self.status_label.config(text="✅ Installation complete!",
                                           foreground='green')
                    self.launch_button.config(state=tk.NORMAL)
                    messagebox.showinfo("Success", "Dependencies installed successfully!")
                else:
                    error_msg = result.stderr or "Unknown error"
                    self.status_label.config(text="❌ Installation failed",
                                           foreground='red')
                    messagebox.showerror("Installation Error",
                                       f"Failed to install dependencies:\n{error_msg}")
                    self.install_button.config(state=tk.NORMAL)

            except Exception as e:
                self.status_label.config(text="❌ Installation error", foreground='red')
                messagebox.showerror("Error", f"Installation failed: {e}")
                self.install_button.config(state=tk.NORMAL)

        # Run installation in separate thread
        threading.Thread(target=install, daemon=True).start()

    def launch_system(self):
        """Launch the Smart Cursor system"""
        try:
            self.status_label.config(text="🚀 Launching system...")
            self.root.withdraw()  # Hide launcher window

            # Launch the main system
            core_path = os.path.join(os.path.dirname(__file__), '..', 'Core', 'smart_cursor_accessibility.py')
            result = subprocess.run([sys.executable, core_path])

            # Show launcher again when system exits
            self.root.deiconify()
            self.status_label.config(text="✅ System closed", foreground='blue')

        except Exception as e:
            self.root.deiconify()
            self.status_label.config(text="❌ Launch failed", foreground='red')
            messagebox.showerror("Launch Error", f"Failed to launch system: {e}")

    def show_help(self):
        """Show help and documentation"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Help - Smart Cursor Control")
        help_window.geometry("500x400")

        help_text = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        help_text.pack(fill=tk.BOTH, expand=True)

        help_content = """Smart Cursor Control - Quick Start Guide

SYSTEM OVERVIEW:
This is an AI-powered cursor control system designed for accessibility.
It uses your webcam to track hand gestures or eye movements to control
the mouse cursor.

GETTING STARTED:
1. Ensure your webcam is working
2. Install all dependencies using the button below
3. Click "Launch Smart Cursor" to start

CONTROL MODES:
• Hand Tracking: Use hand gestures to control cursor
• Eye Tracking: Control with eye gaze (very experimental)
• Web Mode: Optimized for web browsing
• Gaming Mode: Enhanced precision for games

ACCESSIBILITY FEATURES:
• Voice feedback announces actions
• Sound effects for clicks
• Dwell clicking (hold cursor still to click)
• Keyboard shortcuts for all functions

KEYBOARD SHORTCUTS:
Ctrl+Shift+E: Eye Tracking Mode
Ctrl+Shift+H: Hand Tracking Mode
Ctrl+Shift+W: Web Mode
Ctrl+Shift+G: Gaming Mode
Ctrl+Shift+T: Typing Mode
Ctrl+Shift+D: Drawing Mode
Ctrl+Shift+Q: Quit System

TROUBLESHOOTING:
• Good lighting is essential for tracking
• Position camera at eye level
• Calibrate the system for better accuracy
• Check logs for error details

For detailed documentation, see README.md
"""

        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(help_window, command=help_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        help_text.config(yscrollcommand=scrollbar.set)

    def run(self):
        """Run the launcher"""
        self.root.mainloop()


def main():
    """Main function"""
    launcher = CursorLauncher()
    launcher.run()


if __name__ == "__main__":
    main()
