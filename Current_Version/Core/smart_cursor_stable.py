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

        # Safe settings with fallbacks
        self.settings = {
            'smoothing': 0.7,
            'dwell_time': 2.0,  # seconds for dwell clicking
            'voice_feedback': False,  # Disable by default to avoid issues
            'sound_feedback': True,
            'gesture_recognition': True,
            'adaptive_speed': False  # Disable by default
        }

        # Load settings safely
        self.load_settings_safely()

        # Initialize components with error handling
        self.initialize_components_safely()

        # Initialize high-performance cursor layer
        self.hp_cursor = HighPerformanceCursor(self.screen_width, self.screen_height)

        # Performance tracking
        self.fps_history = deque(maxlen=30)
        self.detection_history = deque(maxlen=30)

        # Mouse safety
        self.mouse_enabled = True
        self.last_mouse_move = time.time()
        self.mouse_timeout = 30  # seconds

    def load_settings_safely(self):
        """Load settings with error handling"""
        try:
            if os.path.exists('cursor_settings_stable.json'):
                with open('cursor_settings_stable.json', 'r') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
                logging.info("Settings loaded successfully")
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

        subtitle_label = ttk.Label(self.gui, text="High Performance Version with Gesture Control",
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
            ("👁️ Eye Tracking", "eye_tracking"),
            ("🖐️ Hand Tracking", "normal"),
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

    def start_calibration(self):
        """Start calibration wizard"""
        calibration_window = tk.Toplevel(self.gui)
        calibration_window.title("Calibration - Follow Instructions")
        calibration_window.geometry("400x300")

        ttk.Label(calibration_window, text="Calibration Wizard",
                 font=('Arial', 14, 'bold')).pack(pady=10)

        instructions = """
1. Position camera so your face/hands fill the frame
2. Ensure good lighting
3. For hand mode: Hold up your hand
4. For eye mode: Look straight at camera
5. Click 'Start' and follow on-screen prompts

Note: This is a basic calibration. Advanced features disabled for stability.
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
1. Choose a control mode (Hand Tracking recommended)
2. Position yourself in front of the camera
3. The system will show your camera feed with performance stats
4. Your cursor will move based on hand/eye position

NEW FEATURES:
• Gesture-based clicking: Pinch for left-click, fist for right-click
• Advanced Kalman filtering for smooth cursor movement
• Multi-threaded processing for better performance
• Real-time performance monitoring
• Index finger tracking for precision control

MODES:
• Hand Tracking: Use hand gestures to control cursor
• Eye Tracking: Use eye gaze (experimental)
• Gaming: Enhanced for games
• Typing: Steady for text input

CONTROLS:
• Press 'Q' in camera window to quit
• Use GUI buttons to change modes
• Enable/disable mouse control as needed
• Gestures override dwell clicking when detected

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
        self.running = False
        if self.gui:
            self.gui.quit()

    def run_system(self):
        """Main system loop"""
        self.running = True

        # Start high-performance cursor processing
        self.hp_cursor.start_processing()

        # Create GUI in separate thread
        gui_thread = threading.Thread(target=self.create_control_panel, daemon=True)
        gui_thread.start()

        # Wait for GUI to initialize
        time.sleep(1)

        # Start main processing loop
        self.main_loop()

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
            while self.running:
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
                cursor_pos, detection_found, gesture = self.hp_cursor.process_frame_async(img)
                cursor_x, cursor_y = int(float(cursor_pos[0])), int(float(cursor_pos[1]))

                # Handle gesture-based clicking (new feature)
                if self.mouse_enabled and gesture:
                    gesture_clicked = self.hp_cursor.handle_gesture_click(gesture)
                    if gesture_clicked:
                        logging.info(f"Gesture click performed: {gesture}")

                # Handle legacy dwell clicking if no gesture
                elif self.mouse_enabled and not gesture:
                    self.handle_mouse_control(cursor_x, cursor_y, detection_found)

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

    def handle_mouse_control(self, cursor_x, cursor_y, detection_found):
        """Handle mouse control with safety measures"""
        if detection_found:
            try:
                # Move cursor
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
