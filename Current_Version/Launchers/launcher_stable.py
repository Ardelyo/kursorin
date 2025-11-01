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
import psutil
import logging
from functools import lru_cache

class PerformanceMonitor:
    """Monitor system performance for stability"""

    def __init__(self):
        self.start_time = time.time()
        self.cpu_usage = []
        self.memory_usage = []

    def check_system_health(self):
        """Check if system has adequate resources"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Store recent readings
            self.cpu_usage.append(cpu_percent)
            self.memory_usage.append(memory_percent)

            # Keep only last 10 readings
            if len(self.cpu_usage) > 10:
                self.cpu_usage.pop(0)
            if len(self.memory_usage) > 10:
                self.memory_usage.pop(0)

            # Check thresholds
            avg_cpu = sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
            avg_memory = sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0

            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'avg_cpu': avg_cpu,
                'avg_memory': avg_memory,
                'healthy': avg_cpu < 80 and avg_memory < 85
            }
        except Exception as e:
            logging.warning(f"Performance monitoring failed: {e}")
            return {'healthy': True}  # Assume healthy if monitoring fails

    def get_uptime(self):
        """Get launcher uptime"""
        return time.time() - self.start_time

class StableLauncher:
    def __init__(self):
        # Performance and stability enhancements
        self.performance_monitor = PerformanceMonitor()
        self.thread_pool = []
        self.retry_count = 3
        self.cache_timeout = 300  # 5 minutes

        # Setup logging for stability tracking
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        self.root = tk.Tk()
        self.root.title("Smart Cursor Control - High Performance Launcher")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        # Optimize UI updates
        self.root.after(100, self._optimize_ui_updates)

        # Center window
        self.center_window()

        self.create_ui()
        self.check_system()

    def _optimize_ui_updates(self):
        """Optimize UI updates for better performance"""
        # Reduce update frequency
        self.root.update_idletasks()
        # Schedule next optimization
        self.root.after(500, self._optimize_ui_updates)

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
        title_label = ttk.Label(self.root, text="Smart Cursor Control",
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

        self.install_button = ttk.Button(buttons_frame, text="Install Dependencies",
                                        command=self.install_dependencies)
        self.install_button.pack(fill=tk.X, pady=(0, 5))

        self.launch_button = ttk.Button(buttons_frame, text="Launch Smart Cursor",
                                       command=self.launch_system, state=tk.DISABLED)
        self.launch_button.pack(fill=tk.X, pady=(0, 5))

        self.demo_button = ttk.Button(buttons_frame, text="Run Demo Mode",
                                     command=self.run_demo, state=tk.DISABLED)
        self.demo_button.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(buttons_frame, text="Exit", command=self.root.quit).pack(fill=tk.X)

        # Log initial status
        self.log_message("Launcher started. Checking system...")

    def log_message(self, message, level="INFO"):
        """Add message to status log with performance monitoring"""
        # Log to both UI and file logger
        timestamp = time.strftime('%H:%M:%S')
        full_message = f"[{timestamp}] {message}"

        # Log to file
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)

        # Update UI efficiently
        try:
            self.status_text.config(state=tk.NORMAL)
            self.status_text.insert(tk.END, full_message + "\n")
            self.status_text.see(tk.END)
            self.status_text.config(state=tk.DISABLED)

            # Limit text size for performance
            if self.status_text.index('end-1c').split('.')[0] > '100':
                self.status_text.delete('1.0', '10.0')

            # Throttle UI updates
            self.root.update_idletasks()

        except tk.TclError:
            # Handle UI destruction gracefully
            pass

        # Monitor performance
        health = self.performance_monitor.check_system_health()
        if not health.get('healthy', True):
            self.logger.warning(f"System health degraded: CPU {health.get('avg_cpu', 0):.1f}%, Memory {health.get('avg_memory', 0):.1f}%")

    @lru_cache(maxsize=1)
    def _check_python_version(self):
        """Cached Python version check"""
        python_version = sys.version_info
        is_valid = python_version.major >= 3 and (python_version.major > 3 or python_version.minor >= 8)
        return is_valid, sys.version.split()[0]

    @lru_cache(maxsize=1)
    def _check_pip(self):
        """Cached pip availability check"""
        try:
            import pip
            return True
        except ImportError:
            return False

    def _check_dependency_with_retry(self, dep, max_retries=2):
        """Check dependency with retry mechanism for stability"""
        for attempt in range(max_retries + 1):
            try:
                if dep == 'cv2':
                    import cv2
                elif dep == 'PIL':
                    import PIL
                else:
                    __import__(dep)
                return True
            except ImportError:
                if attempt < max_retries:
                    time.sleep(0.1)  # Brief pause before retry
                    continue
                return False

    def check_system(self):
        """Check system requirements and dependencies with performance optimizations"""
        self.log_message("Checking Python installation...")

        # Check Python version (cached)
        is_valid_python, version_str = self._check_python_version()
        if not is_valid_python:
            self.log_message("[ERROR]: Python 3.8+ required. Current: " + version_str, "ERROR")
            messagebox.showerror("Python Version Error",
                               f"Python 3.8+ required. You have: {version_str}\n\nPlease install Python 3.8 or higher.")
            return False

        self.log_message("[SUCCESS] Python version OK: " + version_str)

        # Check for pip (cached)
        if not self._check_pip():
            self.log_message("[ERROR]: Pip not available", "ERROR")
            messagebox.showerror("Pip Error", "Pip is not installed. Please install pip first.")
            return False

        self.log_message("[SUCCESS] Pip available")

        # Check system health before dependency checks
        health = self.performance_monitor.check_system_health()
        if not health.get('healthy', True):
            self.log_message(f"[WARNING] System under load (CPU: {health.get('avg_cpu', 0):.1f}%, Memory: {health.get('avg_memory', 0):.1f}%)", "WARNING")

        # Check essential dependencies sequentially for stability
        self.log_message("Checking essential dependencies...")
        essential_deps = ['cv2', 'mediapipe', 'pyautogui', 'PIL', 'numpy', 'mss']

        missing_deps = []
        available_deps = []

        for dep in essential_deps:
            if self._check_dependency_with_retry(dep):
                available_deps.append(dep)
                self.log_message(f"[SUCCESS] {dep} available")
            else:
                missing_deps.append(dep)
                self.log_message(f"[ERROR] {dep} missing", "WARNING")

        if missing_deps:
            self.log_message(f"[WARNING] Missing dependencies: {', '.join(missing_deps)}", "WARNING")
            self.install_button.config(state=tk.NORMAL)
            return False
        else:
            self.log_message("[SUCCESS] All essential dependencies available")
            self.launch_button.config(state=tk.NORMAL)
            self.demo_button.config(state=tk.NORMAL)
            return True

    def install_dependencies(self):
        """Install missing dependencies with enhanced stability and performance"""
        def install_with_retry():
            """Installation with retry mechanism"""
            max_retries = self.retry_count
            for attempt in range(max_retries):
                try:
                    return self._perform_installation()
                except Exception as e:
                    self.logger.warning(f"Installation attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait before retry
                        continue
                    raise e

        def install():
            try:
                # Check system health before installation
                health = self.performance_monitor.check_system_health()
                if not health.get('healthy', True):
                    self.log_message(f"[WARNING] System under high load, installation may be slow", "WARNING")

                self.progress_var.set(0)
                self.progress_label.config(text="Preparing installation...")
                self.install_button.config(state=tk.DISABLED)

                self.log_message("Starting dependency installation with stability checks...")

                # Install from stable requirements
                requirements_file = os.path.join(os.path.dirname(__file__), '..', 'Config', 'requirements_stable.txt')
                if not os.path.exists(requirements_file):
                    requirements_file = os.path.join(os.path.dirname(__file__), '..', 'Config', 'requirements.txt')

                if not os.path.exists(requirements_file):
                    raise FileNotFoundError(f"Requirements file not found: {requirements_file}")

                self.log_message(f"Installing from {requirements_file}...")
                self.progress_var.set(10)

                # Perform installation with retry
                success = install_with_retry()

                if success:
                    self.progress_var.set(100)
                    self.progress_label.config(text="Installation complete!")
                    self.log_message("[SUCCESS] Dependencies installed successfully!")
                    messagebox.showinfo("Success", "Dependencies installed successfully!\n\nClick 'Launch Smart Cursor' to start.")

                    # Clear caches and re-check system
                    self._check_python_version.cache_clear()
                    self._check_pip.cache_clear()
                    self.root.after(1000, lambda: self.check_system())

                else:
                    self.log_message("[ERROR] Installation failed after retries", "ERROR")
                    messagebox.showerror("Installation Failed", "Failed to install dependencies after multiple attempts.")
                    self.install_button.config(state=tk.NORMAL)

            except FileNotFoundError as e:
                self.log_message(f"[ERROR] Requirements file error: {e}", "ERROR")
                messagebox.showerror("File Error", f"Requirements file not found:\n{str(e)}")
                self.install_button.config(state=tk.NORMAL)
            except subprocess.TimeoutExpired:
                self.log_message("[ERROR] Installation timed out", "ERROR")
                messagebox.showerror("Timeout", "Installation took too long. Please try again or check your internet connection.")
                self.install_button.config(state=tk.NORMAL)
            except Exception as e:
                self.log_message(f"[ERROR] Installation error: {e}", "ERROR")
                messagebox.showerror("Error", f"Installation failed: {e}")
                self.install_button.config(state=tk.NORMAL)

        # Run installation in managed thread
        install_thread = threading.Thread(target=install, daemon=True, name="DependencyInstaller")
        install_thread.start()
        self.thread_pool.append(install_thread)

    def _perform_installation(self):
        """Perform the actual installation with progress tracking"""
        requirements_file = os.path.join(os.path.dirname(__file__), '..', 'Config', 'requirements_stable.txt')
        if not os.path.exists(requirements_file):
            requirements_file = os.path.join(os.path.dirname(__file__), '..', 'Config', 'requirements.txt')

        # Use pip install with optimized flags for stability
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', requirements_file,
            '--disable-pip-version-check', '--quiet', '--no-cache-dir',
            '--retries', '3', '--timeout', '30'
        ], capture_output=True, text=True, timeout=600)  # 10 minute timeout

        self.progress_var.set(50)
        self.progress_label.config(text="Installing packages...")

        if result.returncode == 0:
            self.progress_var.set(90)
            self.progress_label.config(text="Verifying installation...")
            return True
        else:
            error_msg = result.stderr or "Unknown error"
            self.log_message(f"Installation stderr: {error_msg}", "ERROR")
            return False

    def launch_system(self):
        """Launch the Smart Cursor system with stability enhancements"""
        def launch_with_monitoring():
            """Launch with performance monitoring and auto-restart capability"""
            try:
                # Check system health before launch
                health = self.performance_monitor.check_system_health()
                if not health.get('healthy', True):
                    self.log_message(f"[WARNING] Launching under high system load", "WARNING")

                self.log_message("Launching Smart Cursor system with stability monitoring...")
                self.root.withdraw()  # Hide launcher

                # Launch the main system
                core_path = os.path.join(os.path.dirname(__file__), '..', 'Core', 'smart_cursor_stable.py')
                if not os.path.exists(core_path):
                    raise FileNotFoundError(f"Core system file not found: {core_path}")

                # Launch with environment optimization
                env = os.environ.copy()
                env['PYTHONUNBUFFERED'] = '1'  # For better logging

                process = subprocess.Popen([sys.executable, core_path],
                                         env=env,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         text=True)

                # Monitor process health
                start_time = time.time()
                while process.poll() is None and (time.time() - start_time) < 300:  # 5 minute timeout
                    time.sleep(0.5)  # Check every 500ms

                    # Check if system is still responsive
                    try:
                        self.root.update_idletasks()
                    except tk.TclError:
                        # UI destroyed, terminate process
                        process.terminate()
                        break

                # Process finished
                return_code = process.poll()
                stdout, stderr = process.communicate()

                # Show launcher again
                try:
                    self.root.deiconify()
                except tk.TclError:
                    pass  # UI already destroyed

                if return_code == 0:
                    self.log_message("[SUCCESS] System closed normally")
                elif return_code is None:
                    self.log_message("[WARNING] System terminated by launcher")
                else:
                    self.log_message(f"[WARNING] System exited with code: {return_code}", "WARNING")
                    if stderr:
                        self.log_message(f"Error output: {stderr[:200]}...", "ERROR")

                return return_code

            except subprocess.TimeoutExpired:
                self.log_message("[WARNING] System launch timed out", "WARNING")
                try:
                    self.root.deiconify()
                except tk.TclError:
                    pass
                messagebox.showwarning("Timeout", "System launch timed out. It may still be running.")
                return -1
            except Exception as e:
                self.log_message(f"[ERROR] Launch failed: {e}", "ERROR")
                try:
                    self.root.deiconify()
                except tk.TclError:
                    pass
                messagebox.showerror("Launch Error", f"Failed to launch system: {e}")
                return -1

        # Launch in managed thread for better stability
        launch_thread = threading.Thread(target=launch_with_monitoring, daemon=True, name="SystemLauncher")
        launch_thread.start()
        self.thread_pool.append(launch_thread)

    def run_demo(self):
        """Run a simple demo mode with stability enhancements"""
        def demo_with_monitoring():
            """Run demo with monitoring and error recovery"""
            try:
                # Check system health before demo
                health = self.performance_monitor.check_system_health()
                if not health.get('healthy', True):
                    self.log_message(f"[WARNING] Running demo under high system load", "WARNING")

                self.log_message("Starting demo mode with stability monitoring...")
                self.root.withdraw()

                # Run demo
                demo_path = os.path.join(os.path.dirname(__file__), '..', 'Core', 'demo_mode.py')
                if not os.path.exists(demo_path):
                    raise FileNotFoundError(f"Demo file not found: {demo_path}")

                # Launch with environment optimization
                env = os.environ.copy()
                env['PYTHONUNBUFFERED'] = '1'

                process = subprocess.Popen([sys.executable, demo_path],
                                         env=env,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         text=True)

                # Monitor demo process
                start_time = time.time()
                while process.poll() is None and (time.time() - start_time) < 120:  # 2 minute timeout for demo
                    time.sleep(0.2)  # Check every 200ms

                    # Check UI responsiveness
                    try:
                        self.root.update_idletasks()
                    except tk.TclError:
                        process.terminate()
                        break

                # Process finished
                return_code = process.poll()
                stdout, stderr = process.communicate()

                # Show launcher again
                try:
                    self.root.deiconify()
                except tk.TclError:
                    pass

                if return_code == 0:
                    self.log_message("[SUCCESS] Demo completed successfully")
                elif return_code is None:
                    self.log_message("[WARNING] Demo terminated by launcher")
                else:
                    self.log_message(f"[WARNING] Demo exited with code: {return_code}", "WARNING")
                    if stderr:
                        self.log_message(f"Demo error: {stderr[:150]}...", "ERROR")

            except FileNotFoundError as e:
                try:
                    self.root.deiconify()
                except tk.TclError:
                    pass
                self.log_message(f"[ERROR] Demo file error: {e}", "ERROR")
                messagebox.showerror("Demo Error", f"Demo file not found: {str(e)}")
            except Exception as e:
                try:
                    self.root.deiconify()
                except tk.TclError:
                    pass
                self.log_message(f"[ERROR] Demo failed: {e}", "ERROR")
                messagebox.showerror("Demo Error", f"Demo failed: {e}")

        # Run demo in managed thread
        demo_thread = threading.Thread(target=demo_with_monitoring, daemon=True, name="DemoRunner")
        demo_thread.start()
        self.thread_pool.append(demo_thread)

    def cleanup_threads(self):
        """Clean up running threads for stability"""
        for thread in self.thread_pool[:]:  # Copy list to avoid modification issues
            if not thread.is_alive():
                self.thread_pool.remove(thread)
            elif thread.is_alive() and thread.daemon:
                # Daemon threads will be cleaned up automatically
                pass

        # Log performance summary
        uptime = self.performance_monitor.get_uptime()
        self.logger.info(f"Launcher uptime: {uptime:.1f} seconds")

        health = self.performance_monitor.check_system_health()
        if health.get('healthy', True):
            self.logger.info("System health: Good")
        else:
            self.logger.warning(f"System health: Degraded (CPU: {health.get('avg_cpu', 0):.1f}%, Memory: {health.get('avg_memory', 0):.1f}%)")

def main():
    """Main function with enhanced stability"""
    launcher = None
    try:
        launcher = StableLauncher()

        # Schedule periodic cleanup
        def periodic_cleanup():
            if launcher:
                launcher.cleanup_threads()
            launcher.root.after(30000, periodic_cleanup)  # Every 30 seconds

        launcher.root.after(30000, periodic_cleanup)

        # Handle graceful shutdown
        def on_closing():
            if launcher:
                launcher.logger.info("Launcher shutting down gracefully")
                launcher.cleanup_threads()
            launcher.root.destroy()

        launcher.root.protocol("WM_DELETE_WINDOW", on_closing)

        launcher.root.mainloop()

    except KeyboardInterrupt:
        if launcher:
            launcher.logger.info("Launcher interrupted by user")
            launcher.cleanup_threads()
    except Exception as e:
        if launcher:
            launcher.logger.error(f"Critical launcher error: {e}")
            launcher.cleanup_threads()
        raise


if __name__ == "__main__":
    main()
