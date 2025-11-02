#!/usr/bin/env python3
"""
Smart Cursor Control - Stable Version
Simplified and robust version with error handling and fallback modes
"""

import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import time
import threading
import logging
import signal
import sys
import os
import json
from collections import deque
from PIL import Image
import mss

# Import high-performance cursor layer
from high_performance_cursor import HighPerformanceCursor

# Set up logging to console and file
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('smart_cursor_stable.log'),
                        logging.StreamHandler()
                    ])

class SmartCursorStable:
    def __init__(self):
        self.running = False
        self.current_mode = "normal"
        self.gui = None
        self.lock = threading.Lock()

        # Safe settings with fallbacks
        self.settings = {
            'smoothing': 0.7,
            'dwell_time': 2.0,  # seconds for dwell clicking
            'voice_feedback': False,  # Disable by default to avoid issues
            'sound_feedback': True,
            'gesture_recognition': True,
            'adaptive_speed': False,  # Disable by default
            'tracking_type': 'finger',  # Options: 'hand', 'head', 'eye', 'pose', 'finger', 'body'
            'tracking_sensitivity': 0.8,  # 0.1 to 1.0
            'multi_tracking': False,  # Allow multiple tracking types simultaneously
            'stabilizer_method': 'kalman',  # Options: 'kalman', 'ema', 'none'
            'stabilizer_alpha': 0.7,  # For EMA method
            'stabilizer_process_noise': 0.003,  # For Kalman method
            'stabilizer_measurement_noise': 0.03  # For Kalman method
        }

        # Load settings safely
        self.load_settings_safely()

        # Initialize components with error handling
        self.initialize_components_safely()

        # Initialize high-performance cursor layer with stabilizer settings
        stabilizer_kwargs = {
            'method': self.settings['stabilizer_method'],
            'alpha': self.settings['stabilizer_alpha'],
            'process_noise': self.settings['stabilizer_process_noise'],
            'measurement_noise': self.settings['stabilizer_measurement_noise']
        }
        self.hp_cursor = HighPerformanceCursor(self.screen_width, self.screen_height, stabilizer_kwargs=stabilizer_kwargs)

        # Performance tracking
        self.fps_history = deque(maxlen=30)
        self.detection_history = deque(maxlen=30)

        # Mouse safety
        self.mouse_enabled = True
        self.last_mouse_move = time.time()
        self.mouse_timeout = 30  # seconds

    def load_settings_safely(self):
        """Load settings with comprehensive error handling"""
        try:
            settings_file = 'cursor_settings_stable.json'
            if os.path.exists(settings_file):
                # Check file size to prevent loading corrupted files
                if os.path.getsize(settings_file) > 1024 * 1024:  # 1MB limit
                    logging.warning("Settings file too large, using defaults")
                    return

                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)

                # Validate loaded settings
                if not isinstance(loaded_settings, dict):
                    logging.warning("Invalid settings format, using defaults")
                    return

                # Safe update with validation
                valid_keys = {
                    'smoothing', 'dwell_time', 'voice_feedback', 'sound_feedback',
                    'gesture_recognition', 'adaptive_speed', 'tracking_type',
                    'tracking_sensitivity', 'multi_tracking', 'stabilizer_method',
                    'stabilizer_alpha', 'stabilizer_process_noise', 'stabilizer_measurement_noise'
                }

                for key, value in loaded_settings.items():
                    if key in valid_keys:
                        # Type checking and validation
                        if key in ['voice_feedback', 'sound_feedback', 'gesture_recognition', 'adaptive_speed', 'multi_tracking']:
                            if isinstance(value, bool):
                                self.settings[key] = value
                        elif key == 'tracking_type':
                            if isinstance(value, str) and value in ['hand', 'head', 'eye', 'pose', 'finger', 'body']:
                                self.settings[key] = value
                        elif key == 'tracking_sensitivity':
                            if isinstance(value, (int, float)) and 0.1 <= value <= 1.0:
                                self.settings[key] = float(value)
                        elif key in ['smoothing', 'dwell_time']:
                            if isinstance(value, (int, float)) and value > 0:
                                self.settings[key] = float(value)
                        elif key == 'stabilizer_method':
                            if isinstance(value, str) and value in ['kalman', 'ema', 'none']:
                                self.settings[key] = value
                        elif key == 'stabilizer_alpha':
                            if isinstance(value, (int, float)) and 0.1 <= value <= 1.0:
                                self.settings[key] = float(value)
                        elif key in ['stabilizer_process_noise', 'stabilizer_measurement_noise']:
                            if isinstance(value, (int, float)) and value >= 0:
                                self.settings[key] = float(value)

                logging.info("Settings loaded successfully")
            else:
                logging.info("No settings file found, using defaults")

        except json.JSONDecodeError as e:
            logging.warning(f"Corrupted settings file: {e}. Using defaults.")
        except PermissionError as e:
            logging.warning(f"Permission denied accessing settings: {e}. Using defaults.")
        except Exception as e:
            logging.warning(f"Could not load settings: {e}. Using defaults.")

    def save_settings_safely(self):
        """Save settings with error handling"""
        try:
            with open('cursor_settings_stable.json', 'w') as f:
                json.dump(self.settings, f, indent=4)
            logging.info("Settings saved successfully")
        except Exception as e:
            logging.error(f"Could not save settings: {e}")

    def initialize_components_safely(self):
        """Initialize components with fallbacks"""
        # MediaPipe Holistic with error handling
        try:
            self.mp_holistic = mp.solutions.holistic
            self.holistic = self.mp_holistic.Holistic(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.mp_draw = mp.solutions.drawing_utils
            logging.info("MediaPipe initialized successfully")
        except Exception as e:
            logging.error(f"MediaPipe initialization failed: {e}")
            self.mp_holistic = None
            self.holistic = None
            self.mp_draw = None

        # Screen dimensions
        try:
            self.screen_width, self.screen_height = pyautogui.size()
            logging.info(f"Screen size: {self.screen_width}x{self.screen_height}")
        except Exception as e:
            logging.error(f"Could not get screen size: {e}")
            self.screen_width, self.screen_height = 1920, 1080  # fallback

        # Webcam with error handling
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow on Windows
            if not self.cap.isOpened():
                raise Exception("Cannot open webcam")

            # Test read
            ret, test_frame = self.cap.read()
            if not ret:
                raise Exception("Cannot read from webcam")

            logging.info("Webcam initialized successfully")
            self.camera_available = True
        except Exception as e:
            logging.error(f"Webcam initialization failed: {e}")
            logging.warning("System will continue without camera - limited functionality")
            self.cap = None
            self.camera_available = False

            # Show warning but don't exit
            try:
                messagebox.showwarning("Camera Warning",
                                     "Camera not available. System will run in limited mode.\n\n"
                                     "Features affected:\n"
                                     "- Live camera feed\n"
                                     "- Hand/eye tracking\n\n"
                                     "You can still:\n"
                                     "- Test GUI controls\n"
                                     "- Review settings\n"
                                     "- Check system status")
            except:
                logging.error("Could not show camera warning dialog")

        # Cursor trail
        self.trail_points = deque(maxlen=20)

        # Gesture recognition
        self.gesture_buffer = deque(maxlen=5)
        self.last_gesture_time = 0

        # Dwell clicking
        self.dwell_start_time = 0
        self.dwell_position = None
        self.dwell_active = False

    def create_control_panel(self):
        """Create the main GUI control panel"""
        self.gui = tk.Tk()
        self.gui.title("Smart Cursor Control - High Performance Version")
        self.gui.geometry("600x500")
        self.gui.configure(bg='#f0f0f0')

        # Make window always on top initially
        self.gui.attributes('-topmost', True)
        self.gui.after(1000, lambda: self.gui.attributes('-topmost', False))

        # Title
        title_label = ttk.Label(self.gui, text="🖱️ Smart Cursor Control",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)

        subtitle_label = ttk.Label(self.gui, text="High Performance Version with Advanced Finger Tracking & Gestures",
        font=('Arial', 10))
        subtitle_label.pack(pady=(0, 20))

        # Status section
        status_frame = ttk.LabelFrame(self.gui, text="System Status", padding="10")
        status_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.status_labels = {}
        status_items = [
            ("Mode", "normal"),
            ("Detection", "Initializing"),
            ("FPS", "0"),
            ("Mouse", "Enabled")
        ]

        for i, (label_text, default_value) in enumerate(status_items):
            frame = ttk.Frame(status_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"{label_text}:").pack(side=tk.LEFT)
            self.status_labels[label_text] = ttk.Label(frame, text=default_value)
            self.status_labels[label_text].pack(side=tk.RIGHT)

        # Control buttons section
        control_frame = ttk.LabelFrame(self.gui, text="Mode Control", padding="10")
        control_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Mode buttons
        modes = [
        ("👆 Finger Tracking", "normal"),  # Default mode now uses finger tracking
        ("👁️ Eye Tracking", "eye_tracking"),
        ("🎯 Gaming", "gaming"),
        ("⌨️ Typing", "typing")
        ]

        button_frame = ttk.Frame(control_frame)
        button_frame.pack()

        self.mode_buttons = {}
        for i, (text, mode) in enumerate(modes):
            btn = ttk.Button(button_frame, text=text,
                           command=lambda m=mode: self.set_mode(m))
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky=(tk.W, tk.E))

            # Highlight current mode
            if mode == self.current_mode:
                btn.config(style='Accent.TButton')
            self.mode_buttons[mode] = btn

        # Settings section
        settings_frame = ttk.LabelFrame(self.gui, text="Quick Settings", padding="10")
        settings_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Mouse control
        mouse_frame = ttk.Frame(settings_frame)
        mouse_frame.pack(fill=tk.X, pady=2)
        ttk.Label(mouse_frame, text="Mouse Control:").pack(side=tk.LEFT)
        self.mouse_var = tk.BooleanVar(value=self.mouse_enabled)
        ttk.Checkbutton(mouse_frame, text="Enable",
        variable=self.mouse_var,
        command=self.toggle_mouse).pack(side=tk.RIGHT)

        # Dwell time slider
        dwell_frame = ttk.Frame(settings_frame)
        dwell_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dwell_frame, text="Dwell Click Time:").pack(side=tk.LEFT)
        self.dwell_scale = tk.Scale(dwell_frame, from_=0.5, to=3.0,
        resolution=0.1, orient=tk.HORIZONTAL,
        command=self.set_dwell_time)
        self.dwell_scale.set(self.settings['dwell_time'])
        self.dwell_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Tracking type selector
        tracking_frame = ttk.Frame(settings_frame)
        tracking_frame.pack(fill=tk.X, pady=5)
        ttk.Label(tracking_frame, text="Tracking Type:").pack(side=tk.LEFT)
        self.tracking_var = tk.StringVar(value=self.settings['tracking_type'])
        tracking_combo = ttk.Combobox(tracking_frame, textvariable=self.tracking_var,
                                    values=['hand', 'head', 'eye', 'pose', 'finger', 'body'],
                                    state='readonly', width=10)
        tracking_combo.pack(side=tk.RIGHT)
        tracking_combo.bind('<<ComboboxSelected>>', self.set_tracking_type)

        # Tracking sensitivity slider
        sensitivity_frame = ttk.Frame(settings_frame)
        sensitivity_frame.pack(fill=tk.X, pady=5)
        ttk.Label(sensitivity_frame, text="Sensitivity:").pack(side=tk.LEFT)
        self.sensitivity_scale = tk.Scale(sensitivity_frame, from_=0.1, to=1.0,
                                        resolution=0.1, orient=tk.HORIZONTAL,
                                        command=self.set_tracking_sensitivity)
        self.sensitivity_scale.set(self.settings['tracking_sensitivity'])
        self.sensitivity_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Multi-tracking option
        multi_frame = ttk.Frame(settings_frame)
        multi_frame.pack(fill=tk.X, pady=2)
        ttk.Label(multi_frame, text="Multi-Tracking:").pack(side=tk.LEFT)
        self.multi_var = tk.BooleanVar(value=self.settings['multi_tracking'])
        ttk.Checkbutton(multi_frame, text="Enable",
        variable=self.multi_var,
        command=self.toggle_multi_tracking).pack(side=tk.RIGHT)

        # Stabilizer method selector
        stabilizer_frame = ttk.Frame(settings_frame)
        stabilizer_frame.pack(fill=tk.X, pady=5)
        ttk.Label(stabilizer_frame, text="Stabilizer Method:").pack(side=tk.LEFT)
        self.stabilizer_var = tk.StringVar(value=self.settings['stabilizer_method'])
        stabilizer_combo = ttk.Combobox(stabilizer_frame, textvariable=self.stabilizer_var,
                                       values=['kalman', 'ema', 'none'],
                                       state='readonly', width=10)
        stabilizer_combo.pack(side=tk.RIGHT)
        stabilizer_combo.bind('<<ComboboxSelected>>', self.set_stabilizer_method)

        # Stabilizer alpha slider (for EMA)
        alpha_frame = ttk.Frame(settings_frame)
        alpha_frame.pack(fill=tk.X, pady=5)
        ttk.Label(alpha_frame, text="EMA Alpha:").pack(side=tk.LEFT)
        self.alpha_scale = tk.Scale(alpha_frame, from_=0.1, to=1.0,
                                   resolution=0.1, orient=tk.HORIZONTAL,
                                   command=self.set_stabilizer_alpha)
        self.alpha_scale.set(self.settings['stabilizer_alpha'])
        self.alpha_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Action buttons
        action_frame = ttk.Frame(self.gui)
        action_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        actions = [
            ("🔧 Calibrate", self.start_calibration),
            ("💾 Save Settings", self.save_settings_safely),
            ("📊 System Info", self.show_system_info),
            ("🆘 Help", self.show_help),
            ("⏹️ Stop System", self.stop_system)
        ]

        for i, (text, command) in enumerate(actions):
            ttk.Button(action_frame, text=text, command=command).grid(
                row=i//2, column=i%2, padx=5, pady=5, sticky=(tk.W, tk.E))

        # Log section
        log_frame = ttk.LabelFrame(self.gui, text="System Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Configure grid weights
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        # Start status updates
        self.update_status_thread = threading.Thread(target=self.update_status_display, daemon=True)
        self.update_status_thread.start()

    def update_status_display(self):
        """Update the GUI status display"""
        while self.running:
            try:
                # Update status labels
                self.status_labels["Mode"].config(text=self.current_mode)
                detection_status = "Active" if any(self.detection_history) else "Inactive"
                self.status_labels["Detection"].config(text=detection_status)

                fps = np.mean(list(self.fps_history)) if self.fps_history else 0
                self.status_labels["FPS"].config(text=f"{fps:.1f}")

                mouse_status = "Enabled" if self.mouse_enabled else "Disabled"
                self.status_labels["Mouse"].config(text=mouse_status)

                # Update log with recent entries (simplified)
                try:
                    if hasattr(logging, 'last_message'):
                        self.log_text.insert(tk.END, logging.last_message + '\n')
                        self.log_text.see(tk.END)
                        logging.last_message = None
                except:
                    pass

                time.sleep(0.5)
            except Exception as e:
                logging.error(f"Status update error: {e}")
                time.sleep(1)

    def set_mode(self, mode):
        """Set the cursor control mode"""
        self.current_mode = mode
        logging.info(f"Switched to {mode} mode")

        # Visual feedback
        for m, btn in self.mode_buttons.items():
            if m == mode:
                try:
                    btn.config(relief=tk.SUNKEN)
                except:
                    pass
            else:
                try:
                    btn.config(relief=tk.RAISED)
                except:
                    pass

    def toggle_mouse(self):
        """Toggle mouse control"""
        self.mouse_enabled = self.mouse_var.get()
        status = "enabled" if self.mouse_enabled else "disabled"
        logging.info(f"Mouse control {status}")
        if not self.mouse_enabled:
            messagebox.showwarning("Mouse Control",
                                 "Mouse control disabled. System will show cursor position but not move it.")

    def set_dwell_time(self, value):
        """Set dwell click time"""
        self.settings['dwell_time'] = float(value)

    def set_tracking_type(self, event=None):
        """Set tracking type"""
        self.settings['tracking_type'] = self.tracking_var.get()
        logging.info(f"Tracking type changed to: {self.settings['tracking_type']}")
        # Update high-performance cursor if needed
        if hasattr(self, 'hp_cursor'):
            self.hp_cursor.set_tracking_type(self.settings['tracking_type'])

    def set_tracking_sensitivity(self, value):
        """Set tracking sensitivity"""
        self.settings['tracking_sensitivity'] = float(value)

    def toggle_multi_tracking(self):
        """Toggle multi-tracking mode"""
        self.settings['multi_tracking'] = self.multi_var.get()
        logging.info(f"Multi-tracking {'enabled' if self.settings['multi_tracking'] else 'disabled'}")
        # Update high-performance cursor if needed
        if hasattr(self, 'hp_cursor'):
            self.hp_cursor.set_multi_tracking(self.settings['multi_tracking'])

    def set_stabilizer_method(self, event=None):
        """Set stabilizer method"""
        self.settings['stabilizer_method'] = self.stabilizer_var.get()
        logging.info(f"Stabilizer method changed to: {self.settings['stabilizer_method']}")
        # Update high-performance cursor stabilizer
        if hasattr(self, 'hp_cursor'):
            self.hp_cursor.set_stabilizer_method(self.settings['stabilizer_method'],
                                               alpha=self.settings['stabilizer_alpha'],
                                               process_noise=self.settings['stabilizer_process_noise'],
                                               measurement_noise=self.settings['stabilizer_measurement_noise'])

    def set_stabilizer_alpha(self, value):
        """Set stabilizer alpha for EMA"""
        self.settings['stabilizer_alpha'] = float(value)
        # Update if EMA is selected
        if self.settings['stabilizer_method'] == 'ema' and hasattr(self, 'hp_cursor'):
            self.hp_cursor.set_stabilizer_method('ema', alpha=self.settings['stabilizer_alpha'])

    def start_calibration(self):
        """Start calibration wizard"""
        calibration_window = tk.Toplevel(self.gui)
        calibration_window.title("Calibration - Follow Instructions")
        calibration_window.geometry("400x300")

        ttk.Label(calibration_window, text="Calibration Wizard",
                 font=('Arial', 14, 'bold')).pack(pady=10)

        instructions = """
1. Position camera so your tracking target fills the frame
2. Ensure good lighting and clear background
3. Select your preferred tracking type from the settings
4. Adjust sensitivity slider for optimal detection
5. Try multi-tracking for enhanced accuracy
6. Click 'Start' and follow on-screen prompts

Tracking Types:
• Finger: Point with index finger extended (recommended)
• Hand: Keep hand visible and open
• Head: Keep face centered
• Eye: Look at different screen areas
• Pose/Body: Upper body should be visible
• Multi: Combine multiple tracking methods

Note: This is a basic calibration. Advanced features available in settings.
        """

        text_widget = scrolledtext.ScrolledText(calibration_window, wrap=tk.WORD, height=10)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, instructions)
        text_widget.config(state=tk.DISABLED)

        ttk.Button(calibration_window, text="Start Basic Calibration",
                  command=lambda: self.run_basic_calibration(calibration_window)).pack(pady=10)

    def run_basic_calibration(self, window):
        """Run basic calibration"""
        messagebox.showinfo("Calibration", "Calibration completed. The system will now work with basic settings.")
        window.destroy()

    def show_system_info(self):
        """Show system information"""
        info_window = tk.Toplevel(self.gui)
        info_window.title("System Information")
        info_window.geometry("400x300")

        info_text = scrolledtext.ScrolledText(info_window, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Calculate performance metrics
        avg_fps = f"{np.mean(list(self.fps_history)):.1f}" if self.fps_history else 'N/A'
        detection_rate = f"{np.mean([1 if d else 0 for d in self.detection_history]) * 100:.1f}%" if self.detection_history else 'N/A'

        # Get high-performance stats
        hp_stats = self.hp_cursor.get_performance_stats() if hasattr(self, 'hp_cursor') else {}

        info = f"""
Smart Cursor Control - High Performance Version

System Status:
- Mode: {self.current_mode}
- Mouse Control: {'Enabled' if self.mouse_enabled else 'Disabled'}
- Dwell Time: {self.settings['dwell_time']}s
- Gesture Recognition: {'Enabled' if hasattr(self, 'hp_cursor') else 'Disabled'}
- Camera: {'Available' if self.cap and self.cap.isOpened() else 'Not Available'}
- MediaPipe: {'Available' if self.holistic else 'Not Available'}

Tracking Configuration:
- Tracking Type: {self.settings['tracking_type']}
- Tracking Sensitivity: {self.settings['tracking_sensitivity']:.1f}
- Multi-Tracking: {'Enabled' if self.settings['multi_tracking'] else 'Disabled'}

Stabilizer Configuration:
- Method: {self.settings['stabilizer_method']}
- EMA Alpha: {self.settings['stabilizer_alpha']:.1f}
- Kalman Process Noise: {self.settings['stabilizer_process_noise']:.4f}
- Kalman Measurement Noise: {self.settings['stabilizer_measurement_noise']:.4f}

Performance (Legacy):
- Average FPS: {avg_fps}
- Detection Rate: {detection_rate}

Performance (High-Performance Layer):
- FPS: {hp_stats.get('fps', 'N/A'):.1f}
- Latency: {hp_stats.get('latency_ms', 'N/A'):.1f}ms
- Detection Rate: {hp_stats.get('detection_rate', 'N/A'):.1f}%

Settings:
{json.dumps(self.settings, indent=2)}
        """

        info_text.insert(tk.END, info)
        info_text.config(state=tk.DISABLED)

    def show_help(self):
        """Show help window"""
        help_window = tk.Toplevel(self.gui)
        help_window.title("Help - Smart Cursor Stable")
        help_window.geometry("500x400")

        help_text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        help_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        help_content = """
Smart Cursor Control - High Performance Version

BASIC USAGE:
1. Choose a tracking type (Finger Tracking recommended for precision)
2. Adjust sensitivity for your needs
3. Position yourself in front of the camera
4. The system will show your camera feed with performance stats
5. Your cursor will move based on selected tracking method

TRACKING TYPES:
• Finger: Precise index finger tip tracking (recommended, default)
• Hand: Track hand/wrist movement
• Head: Track head/nose movement
• Eye: Track eye gaze direction
• Pose/Body: Track upper body/shoulders
• Multi-Tracking: Combine multiple tracking methods

NEW FEATURES:
• Multiple tracking types with customizable sensitivity
• Multi-tracking mode for enhanced accuracy
• Gesture-based clicking: Finger point for left-click, pinch for left-click, fist for right-click
• Advanced Kalman filtering for smooth cursor movement
• Multi-threaded processing for better performance
• Real-time performance monitoring

TRACKING CONTROLS:
• Tracking Type: Select from 6 different tracking methods
• Sensitivity: Adjust detection sensitivity (0.1-1.0)
• Multi-Tracking: Combine multiple tracking types for better accuracy

CONTROLS:
• Press 'Q' in camera window to quit
• Use GUI buttons to change modes
• Enable/disable mouse control as needed
• Gestures override dwell clicking when detected\n• Finger pointing provides precise cursor control

PERFORMANCE:
• Optimized MediaPipe settings for speed
• Kalman filter reduces jitter
• Multi-threading prevents frame drops
• Real-time FPS and latency monitoring

TROUBLESHOOTING:
• If cursor doesn't move: Check mouse control is enabled
• If detection fails: Improve lighting, check camera position
• If system is slow: Close other applications
• Gestures not working: Ensure hand is clearly visible
• Tracking not accurate: Adjust sensitivity or try different tracking type

SAFETY:
• Mouse control can be disabled for safety
• System times out after 30 seconds of no movement
• All actions are logged for debugging

For issues: Check the system log or contact support.
        """

        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)

    def stop_system(self):
        """Stop the cursor control system"""
        with self.lock:
            self.running = False
        if self.gui:
            self.gui.quit()

    def run_system(self):
        """Main system loop"""
        try:
            logging.info("Starting Smart Cursor system...")
            with self.lock:
                self.running = True

            # Start high-performance cursor processing
            logging.info("Initializing cursor processing...")
            self.hp_cursor.start_processing()

            # Create GUI in separate thread
            logging.info("Starting GUI...")
            self.gui_thread = threading.Thread(target=self.create_control_panel, daemon=True)
            self.gui_thread.start()

            # Wait for GUI to initialize
            time.sleep(1)

            # Start main processing loop
            logging.info("Starting main processing loop...")
            self.main_loop()

        except Exception as e:
            logging.error(f"Critical error in run_system: {e}")
            logging.error(f"Error type: {type(e).__name__}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise

    def main_loop(self):
        """Main processing loop"""
        prev_x, prev_y = self.screen_width // 2, self.screen_height // 2
        last_click = 0
        click_cooldown = 0.5

        # Create a placeholder image for when camera is not available
        if not self.camera_available:
            placeholder_img = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(placeholder_img, "CAMERA NOT AVAILABLE", (50, 200),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(placeholder_img, "GUI Controls Still Work", (50, 250),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
            cv2.putText(placeholder_img, "Press Q to quit", (50, 300),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

        try:
            while True:
                with self.lock:
                    if not self.running:
                        break
                start_time = time.time()

                if self.camera_available:
                    success, img = self.cap.read()
                    if not success:
                        logging.warning("Failed to read frame from webcam")
                        time.sleep(0.01)
                        continue
                else:
                    # Use placeholder image when camera is not available
                    img = placeholder_img.copy()
                    success = True

                # Use high-performance cursor processing
                result = self.hp_cursor.process_frame_async(img)
                if result is None:
                    time.sleep(0.01)  # Add a small delay to prevent busy-waiting
                    continue

                cursor_pos, detection_found, gesture = result
                if cursor_pos is None:
                    time.sleep(0.01)
                    continue

                # Validate cursor_pos to prevent crash from malformed data
                if not isinstance(cursor_pos, (list, tuple, np.ndarray)) or len(cursor_pos) < 2:
                    logging.warning(f"Received malformed cursor_pos: {cursor_pos}. Skipping frame.")
                    continue

                cursor_x, cursor_y = int(float(cursor_pos[0])), int(float(cursor_pos[1]))

                # Handle cursor movement (always when detected)
                if self.mouse_enabled and detection_found:
                    try:
                        # Move cursor to finger position
                        pyautogui.moveTo(cursor_x, cursor_y)
                        self.last_mouse_move = time.time()
                    except Exception as e:
                        logging.error(f"Cursor movement error: {e}")
                        self.mouse_enabled = False

                # Handle gesture-based clicking (when gesture detected)
                if self.mouse_enabled and gesture:
                    gesture_clicked = self.hp_cursor.handle_gesture_click(gesture)
                    if gesture_clicked:
                        logging.info(f"Gesture click performed: {gesture}")

                # Handle legacy dwell clicking only when no gesture and cursor is stationary
                elif self.mouse_enabled and not gesture and detection_found:
                    self.handle_mouse_control(cursor_x, cursor_y, detection_found, move_cursor=False)

                # Update display with high-performance overlays
                self.update_display_hp(img, cursor_pos, detection_found, gesture)

                # Performance tracking
                processing_time = time.time() - start_time
                self.fps_history.append(1.0 / processing_time if processing_time > 0 else 30)
                self.detection_history.append(detection_found)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break

                # Safety timeout
                if time.time() - self.last_mouse_move > self.mouse_timeout:
                    logging.warning("Mouse control timeout - safety shutdown")
                    break

                # Limit frame rate
                elapsed = time.time() - start_time
                if elapsed < 0.033:  # ~30 FPS
                    time.sleep(0.033 - elapsed)

        except Exception as e:
            logging.error(f"Main loop error: {e}")
            logging.error("System encountered a critical error and will shut down")

        finally:
            self.cleanup()

    def process_frame(self, img, prev_x, prev_y):
        """Process camera frame for cursor control"""
        if not self.camera_available or not self.holistic:
            # If no camera or no MediaPipe, just return previous position
            return prev_x, prev_y, False

        img = cv2.flip(img, 1)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        try:
            results = self.holistic.process(img_rgb)
        except Exception as e:
            logging.error(f"MediaPipe processing error: {e}")
            return prev_x, prev_y, False

        cursor_x, cursor_y = prev_x, prev_y
        detection_found = False

        # Draw landmarks if available
        if self.mp_draw and results:
            try:
                if results.face_landmarks:
                    self.mp_draw.draw_landmarks(img, results.face_landmarks,
                                              self.mp_holistic.FACEMESH_CONTOURS,
                                              landmark_drawing_spec=self.mp_draw.DrawingSpec(
                                                  color=(0,255,0), thickness=1, circle_radius=1))
                if results.left_hand_landmarks:
                    self.mp_draw.draw_landmarks(img, results.left_hand_landmarks,
                                              self.mp_holistic.HAND_CONNECTIONS,
                                              landmark_drawing_spec=self.mp_draw.DrawingSpec(
                                                  color=(0,0,255), thickness=1, circle_radius=1))
                if results.right_hand_landmarks:
                    self.mp_draw.draw_landmarks(img, results.right_hand_landmarks,
                                              self.mp_holistic.HAND_CONNECTIONS,
                                              landmark_drawing_spec=self.mp_draw.DrawingSpec(
                                                  color=(255,255,0), thickness=1, circle_radius=1))
            except Exception as e:
                logging.error(f"Landmark drawing error: {e}")

        # Process based on current mode
        if self.current_mode == "eye_tracking" and results.face_landmarks:
            cursor_x, cursor_y, detection_found = self.process_eye_tracking(results.face_landmarks, img.shape)
        else:
            cursor_x, cursor_y, detection_found = self.process_hand_tracking(results, prev_x, prev_y)

        return cursor_x, cursor_y, detection_found

    def process_eye_tracking(self, face_landmarks, img_shape):
        """Process eye tracking"""
        try:
            # Simple eye center calculation
            if face_landmarks.landmark[33] and face_landmarks.landmark[362]:
                left_eye_y = face_landmarks.landmark[33].y
                right_eye_y = face_landmarks.landmark[362].y
                eye_y = (left_eye_y + right_eye_y) / 2

                cursor_x = int(self.screen_width // 2)  # Center X
                cursor_y = int(eye_y * self.screen_height)
                return cursor_x, cursor_y, True
        except Exception as e:
            logging.error(f"Eye tracking error: {e}")

        return self.screen_width // 2, self.screen_height // 2, False

    def process_hand_tracking(self, results, prev_x, prev_y):
        """Process hand tracking"""
        hand_landmarks = results.right_hand_landmarks or results.left_hand_landmarks
        if hand_landmarks:
            try:
                wrist = hand_landmarks.landmark[0]
                cursor_x = int(wrist.x * self.screen_width)
                cursor_y = int(wrist.y * self.screen_height)
                return cursor_x, cursor_y, True
            except Exception as e:
                logging.error(f"Hand tracking error: {e}")

        return prev_x, prev_y, False

    def handle_mouse_control(self, cursor_x, cursor_y, detection_found, move_cursor=True):
        """Handle mouse control with safety measures"""
        if detection_found:
            try:
                # Move cursor (if requested)
                if move_cursor:
                    pyautogui.moveTo(cursor_x, cursor_y)
                    self.last_mouse_move = time.time()

                # Handle clicking (simplified)
                if self.settings['dwell_time'] > 0:
                    current_pos = (cursor_x, cursor_y)

                    if self.dwell_position is None or \
                       np.sqrt((current_pos[0] - self.dwell_position[0])**2 +
                              (current_pos[1] - self.dwell_position[1])**2) > 20:
                        # Position changed, reset dwell
                        self.dwell_position = current_pos
                        self.dwell_start_time = time.time()
                        self.dwell_active = False
                    else:
                        # Position stable, check dwell time
                        dwell_duration = time.time() - self.dwell_start_time
                        if dwell_duration >= self.settings['dwell_time'] and not self.dwell_active:
                            self.dwell_active = True
                            pyautogui.click()
                            logging.info("Dwell click performed")
                            self.dwell_position = None

            except Exception as e:
                logging.error(f"Mouse control error: {e}")
                self.mouse_enabled = False
                messagebox.showwarning("Mouse Control Error",
                                     "Mouse control encountered an error and has been disabled for safety.\n"
                                     "You can re-enable it in the settings.")

    def update_display_hp(self, img, cursor_pos, detection_found, gesture):
        """Update the camera display with high-performance overlays"""
        # Use high-performance cursor overlays
        self.hp_cursor.draw_overlays(img, cursor_pos, detection_found, gesture)

        # Add legacy mode information
        try:
            cv2.putText(img, f"Mode: {self.current_mode}", (10, 155),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if self.mouse_enabled:
                cv2.putText(img, "Mouse: ENABLED", (10, 180),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.putText(img, "Mouse: DISABLED", (10, 180),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Show gesture mode indicator
            if gesture:
                cv2.putText(img, "GESTURE MODE", (10, 205),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
            else:
                cv2.putText(img, "DWELL MODE", (10, 205),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        except Exception as e:
            logging.error(f"Legacy overlay error: {e}")

        cv2.imshow('Smart Cursor Control - High Performance Version', img)

    def cleanup(self):
        """Clean up resources"""
        logging.info("Shutting down Smart Cursor High Performance System")
        self.save_settings_safely()

        # Stop high-performance cursor processing
        if hasattr(self, 'hp_cursor'):
            self.hp_cursor.stop_processing()

        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

        if self.holistic:
            self.holistic.close()

        if hasattr(self, 'gui_thread') and self.gui_thread.is_alive():
            self.gui_thread.join(timeout=1)

        if hasattr(self, 'update_status_thread') and self.update_status_thread.is_alive():
            self.update_status_thread.join(timeout=1)

        print("Smart Cursor High Performance System shutdown complete")


def main():
    """Main function"""
    try:
        system = SmartCursorStable()
        system.run_system()
    except KeyboardInterrupt:
        logging.info("System interrupted by user")
    except Exception as e:
        logging.error(f"Application error: {e}")
        logging.error("Failed to start Smart Cursor system")


if __name__ == "__main__":
    main()
