#!/usr/bin/env python3
"""
Smart Cursor Control - Stable Launcher
Robust launcher with error handling and clear feedback
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import threading
import time

class StableLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Smart Cursor Control - Stable Launcher")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        # Center window
        self.center_window()

        self.create_ui()
        self.check_system()

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_ui(self):
        """Create the launcher UI"""
        # Title
        title_label = ttk.Label(self.root, text="🖱️ Smart Cursor Control",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)

        subtitle_label = ttk.Label(self.root, text="Stable Accessibility Edition",
                                  font=('Arial', 10))
        subtitle_label.pack(pady=(0, 20))

        # Status frame
        status_frame = ttk.LabelFrame(self.root, text="System Status")
        status_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.status_text = scrolledtext.ScrolledText(status_frame, height=8, width=50, wrap=tk.WORD)
        self.status_text.pack(pady=5, padx=5)
        self.status_text.config(state=tk.DISABLED)

        # Progress frame
        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.progress_label = ttk.Label(progress_frame, text="Ready to check system...")
        self.progress_label.pack()

        # Buttons frame
        buttons_frame = ttk.Frame(self.root)
        buttons_frame.pack(fill=tk.X, padx=20)

        self.install_button = ttk.Button(buttons_frame, text="📦 Install Dependencies",
                                        command=self.install_dependencies)
        self.install_button.pack(fill=tk.X, pady=(0, 5))

        self.launch_button = ttk.Button(buttons_frame, text="🚀 Launch Smart Cursor",
                                       command=self.launch_system, state=tk.DISABLED)
        self.launch_button.pack(fill=tk.X, pady=(0, 5))

        self.demo_button = ttk.Button(buttons_frame, text="🎯 Run Demo Mode",
                                     command=self.run_demo, state=tk.DISABLED)
        self.demo_button.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(buttons_frame, text="❌ Exit", command=self.root.quit).pack(fill=tk.X)

        # Log initial status
        self.log_message("Launcher started. Checking system...")

    def log_message(self, message):
        """Add message to status log"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()

    def check_system(self):
        """Check system requirements and dependencies"""
        self.log_message("Checking Python installation...")

        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            self.log_message("❌ ERROR: Python 3.8+ required. Current: " + sys.version)
            messagebox.showerror("Python Version Error",
                               f"Python 3.8+ required. You have: {sys.version}\n\nPlease install Python 3.8 or higher.")
            return False

        self.log_message("✅ Python version OK: " + sys.version.split()[0])

        # Check for pip
        try:
            import pip
            self.log_message("✅ Pip available")
        except ImportError:
            self.log_message("❌ ERROR: Pip not available")
            messagebox.showerror("Pip Error", "Pip is not installed. Please install pip first.")
            return False

        # Check essential dependencies
        self.log_message("Checking essential dependencies...")
        essential_deps = ['cv2', 'mediapipe', 'pyautogui', 'PIL', 'numpy', 'mss']

        missing_deps = []
        for dep in essential_deps:
            try:
                if dep == 'cv2':
                    import cv2
                elif dep == 'PIL':
                    import PIL
                else:
                    __import__(dep)
                self.log_message(f"✅ {dep} available")
            except ImportError:
                missing_deps.append(dep)
                self.log_message(f"❌ {dep} missing")

        if missing_deps:
            self.log_message(f"⚠️  Missing dependencies: {', '.join(missing_deps)}")
            self.install_button.config(state=tk.NORMAL)
            return False
        else:
            self.log_message("✅ All essential dependencies available")
            self.launch_button.config(state=tk.NORMAL)
            self.demo_button.config(state=tk.NORMAL)
            return True

    def install_dependencies(self):
        """Install missing dependencies"""
        def install():
            try:
                self.progress_var.set(0)
                self.progress_label.config(text="Installing dependencies...")
                self.install_button.config(state=tk.DISABLED)

                self.log_message("Starting dependency installation...")

                # Install from stable requirements
                requirements_file = os.path.join(os.path.dirname(__file__), '..', 'Config', 'requirements_stable.txt')
                if not os.path.exists(requirements_file):
                    requirements_file = os.path.join(os.path.dirname(__file__), '..', 'Config', 'requirements.txt')

                self.log_message(f"Installing from {requirements_file}...")

                # Use pip install with progress tracking
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-r', requirements_file,
                    '--disable-pip-version-check', '--quiet'
                ], capture_output=True, text=True, timeout=300)

                self.progress_var.set(50)

                if result.returncode == 0:
                    self.progress_var.set(100)
                    self.progress_label.config(text="Installation complete!")
                    self.log_message("✅ Dependencies installed successfully!")
                    messagebox.showinfo("Success", "Dependencies installed successfully!\n\nClick 'Launch Smart Cursor' to start.")

                    # Re-check system
                    self.root.after(1000, lambda: self.check_system())

                else:
                    self.log_message("❌ Installation failed")
                    error_msg = result.stderr or "Unknown error"
                    self.log_message(f"Error details: {error_msg}")
                    messagebox.showerror("Installation Failed",
                                       f"Failed to install dependencies:\n\n{error_msg}")
                    self.install_button.config(state=tk.NORMAL)

            except subprocess.TimeoutExpired:
                self.log_message("❌ Installation timed out")
                messagebox.showerror("Timeout", "Installation took too long. Please try again.")
                self.install_button.config(state=tk.NORMAL)
            except Exception as e:
                self.log_message(f"❌ Installation error: {e}")
                messagebox.showerror("Error", f"Installation failed: {e}")
                self.install_button.config(state=tk.NORMAL)

        # Run installation in separate thread
        threading.Thread(target=install, daemon=True).start()

    def launch_system(self):
        """Launch the Smart Cursor system"""
        try:
            self.log_message("Launching Smart Cursor system...")
            self.root.withdraw()  # Hide launcher

            # Launch the main system
            core_path = os.path.join(os.path.dirname(__file__), '..', 'Core', 'smart_cursor_stable.py')
            result = subprocess.run([sys.executable, core_path],
                                  timeout=60)  # 60 second timeout

            # Show launcher again
            self.root.deiconify()
            if result.returncode == 0:
                self.log_message("✅ System closed normally")
            else:
                self.log_message(f"⚠️  System exited with code: {result.returncode}")

        except subprocess.TimeoutExpired:
            self.root.deiconify()
            self.log_message("⚠️  System launch timed out")
            messagebox.showwarning("Timeout", "System launch timed out. It may still be running.")
        except Exception as e:
            self.root.deiconify()
            self.log_message(f"❌ Launch failed: {e}")
            messagebox.showerror("Launch Error", f"Failed to launch system: {e}")

    def run_demo(self):
        """Run a simple demo mode"""
        try:
            self.log_message("Starting demo mode...")
            self.root.withdraw()

            # Run demo
            demo_path = os.path.join(os.path.dirname(__file__), '..', 'Core', 'demo_mode.py')
            result = subprocess.run([sys.executable, demo_path])

            self.root.deiconify()
            if result.returncode == 0:
                self.log_message("✅ Demo completed")
            else:
                self.log_message(f"⚠️  Demo exited with code: {result.returncode}")

        except Exception as e:
            self.root.deiconify()
            self.log_message(f"❌ Demo failed: {e}")
            messagebox.showerror("Demo Error", f"Demo failed: {e}")

def main():
    """Main function"""
    launcher = StableLauncher()
    launcher.root.mainloop()


if __name__ == "__main__":
    main()
