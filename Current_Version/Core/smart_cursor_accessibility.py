#!/usr/bin/env python3
"""
Smart Cursor Control System for Accessibility
Enhanced version with GUI control panel, AI intelligence, and disability-friendly features
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
import pickle
import json
from collections import deque
from PIL import Image, ImageTk
import mss
import speech_recognition as sr
import pyttsx3
from sklearn.cluster import KMeans
import winsound  # For Windows sound feedback
import keyboard  # For keyboard shortcuts
import mouse  # Enhanced mouse control

# Set up logging
logging.basicConfig(filename='smart_cursor_accessibility.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class SmartCursorAccessibility:
    def __init__(self):
        self.running = False
        self.current_mode = "normal"
        self.intelligence_engine = IntelligenceEngine()
        self.voice_engine = VoiceEngine()
        self.gui = None

        # Enhanced settings for accessibility
        self.settings = {
            'smoothing': 0.8,
            'sensitivity': 1.0,
            'dwell_time': 1.5,  # seconds for dwell clicking
            'voice_feedback': True,
            'sound_feedback': True,
            'high_contrast': False,
            'large_buttons': True,
            'gesture_recognition': True,
            'web_tracking': True,
            'adaptive_speed': True
        }

        # Load settings
        self.load_settings()

        # Initialize components
        self.initialize_components()

        # Calibration data
        self.calibration_data = {
            'screen_corners': None,
            'eye_calibration': None,
            'hand_calibration': None
        }

        # Performance tracking
        self.fps_history = deque(maxlen=30)
        self.detection_history = deque(maxlen=30)

    def load_settings(self):
        """Load user settings from file"""
        try:
            if os.path.exists('cursor_settings.json'):
                with open('cursor_settings.json', 'r') as f:
                    self.settings.update(json.load(f))
        except Exception as e:
            logging.error(f"Failed to load settings: {e}")

    def save_settings(self):
        """Save user settings to file"""
        try:
            with open('cursor_settings.json', 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")

    def initialize_components(self):
        """Initialize all system components"""
        # MediaPipe Holistic
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils

        # Screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()

        # Webcam
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise Exception("Cannot open webcam")

        # Cursor trail
        self.trail_points = deque(maxlen=30)

        # Gesture recognition
        self.gesture_buffer = deque(maxlen=10)
        self.last_gesture_time = 0

        # Dwell clicking
        self.dwell_start_time = 0
        self.dwell_position = None
        self.dwell_active = False

        # Adaptive features
        self.movement_history = deque(maxlen=50)
        self.speed_multiplier = 1.0

    def create_control_panel(self):
        """Create the main GUI control panel"""
        self.gui = tk.Tk()
        self.gui.title("Smart Cursor Control - Accessibility Edition")
        self.gui.geometry("800x600")
        self.gui.configure(bg='#2E3440' if self.settings['high_contrast'] else '#ECEFF4')

        # Style configuration
        style = ttk.Style()
        if self.settings['high_contrast']:
            style.configure('TButton', font=('Arial', 12, 'bold'), padding=10)
            style.configure('TLabel', font=('Arial', 10, 'bold'), background='#2E3440', foreground='#ECEFF4')
        else:
            style.configure('TButton', font=('Arial', 10), padding=8)
            style.configure('TLabel', font=('Arial', 9))

        # Main frame
        main_frame = ttk.Frame(self.gui, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="🖱️ Smart Cursor Control",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        self.status_labels = {}
        status_items = [
            ("Mode", "normal"),
            ("Detection", "Initializing"),
            ("FPS", "0"),
            ("AI Samples", "0")
        ]

        for i, (label_text, default_value) in enumerate(status_items):
            ttk.Label(status_frame, text=f"{label_text}:").grid(row=0, column=i*2, sticky=tk.W, padx=(0, 5))
            self.status_labels[label_text] = ttk.Label(status_frame, text=default_value)
            self.status_labels[label_text].grid(row=0, column=i*2+1, sticky=tk.W, padx=(0, 20))

        # Control buttons section
        control_frame = ttk.LabelFrame(main_frame, text="Quick Controls", padding="10")
        control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # Mode buttons
        modes = [
            ("👁️ Eye Tracking", "eye_tracking"),
            ("🖐️ Hand Tracking", "normal"),
            ("🌐 Web Mode", "browsing"),
            ("🎮 Gaming", "gaming"),
            ("⌨️ Typing", "typing"),
            ("🎨 Drawing", "drawing")
        ]

        self.mode_buttons = {}
        for i, (text, mode) in enumerate(modes):
            btn = ttk.Button(control_frame, text=text,
                           command=lambda m=mode: self.set_mode(m))
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky=(tk.W, tk.E))
            self.mode_buttons[mode] = btn

        # Settings section
        settings_frame = ttk.LabelFrame(main_frame, text="Accessibility Settings", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Voice feedback
        self.voice_var = tk.BooleanVar(value=self.settings['voice_feedback'])
        ttk.Checkbutton(settings_frame, text="Voice Feedback",
                        variable=self.voice_var,
                        command=self.toggle_voice_feedback).grid(row=0, column=0, sticky=tk.W)

        # Sound feedback
        self.sound_var = tk.BooleanVar(value=self.settings['sound_feedback'])
        ttk.Checkbutton(settings_frame, text="Sound Feedback",
                        variable=self.sound_var,
                        command=self.toggle_sound_feedback).grid(row=1, column=0, sticky=tk.W)

        # High contrast
        self.contrast_var = tk.BooleanVar(value=self.settings['high_contrast'])
        ttk.Checkbutton(settings_frame, text="High Contrast Mode",
                        variable=self.contrast_var,
                        command=self.toggle_high_contrast).grid(row=2, column=0, sticky=tk.W)

        # Large buttons
        self.large_var = tk.BooleanVar(value=self.settings['large_buttons'])
        ttk.Checkbutton(settings_frame, text="Large Buttons",
                        variable=self.large_var,
                        command=self.toggle_large_buttons).grid(row=3, column=0, sticky=tk.W)

        # Dwell time slider
        ttk.Label(settings_frame, text="Dwell Click Time (seconds):").grid(row=4, column=0, sticky=tk.W, pady=(10, 0))
        self.dwell_scale = tk.Scale(settings_frame, from_=0.5, to=3.0, resolution=0.1,
                                   orient=tk.HORIZONTAL, command=self.set_dwell_time)
        self.dwell_scale.set(self.settings['dwell_time'])
        self.dwell_scale.grid(row=5, column=0, sticky=(tk.W, tk.E))

        # Action buttons section
        action_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        action_frame.grid(row=3, column=2, sticky=(tk.N, tk.S), pady=(0, 10))

        action_buttons = [
            ("🔧 Calibrate", self.start_calibration),
            ("💾 Save Settings", self.save_settings),
            ("📊 Statistics", self.show_statistics),
            ("🆘 Help", self.show_help),
            ("⏹️ Stop System", self.stop_system)
        ]

        for i, (text, command) in enumerate(action_buttons):
            ttk.Button(action_frame, text=text, command=command).grid(
                row=i, column=0, pady=2, sticky=(tk.W, tk.E))

        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="System Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.gui.columnconfigure(0, weight=1)
        self.gui.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        settings_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        # Keyboard shortcuts
        self.setup_keyboard_shortcuts()

        # Start status updates
        self.update_status_thread = threading.Thread(target=self.update_status_display, daemon=True)
        self.update_status_thread.start()

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for accessibility"""
        shortcuts = {
            'ctrl+shift+e': lambda: self.set_mode('eye_tracking'),
            'ctrl+shift+h': lambda: self.set_mode('normal'),
            'ctrl+shift+w': lambda: self.set_mode('browsing'),
            'ctrl+shift+g': lambda: self.set_mode('gaming'),
            'ctrl+shift+t': lambda: self.set_mode('typing'),
            'ctrl+shift+d': lambda: self.set_mode('drawing'),
            'ctrl+shift+s': self.save_settings,
            'ctrl+shift+q': self.stop_system,
            'ctrl+shift+c': self.start_calibration
        }

        for shortcut, action in shortcuts.items():
            keyboard.add_hotkey(shortcut, action)

    def update_status_display(self):
        """Update the GUI status display"""
        while self.running:
            try:
                # Update status labels
                self.status_labels["Mode"].config(text=self.current_mode)
                self.status_labels["Detection"].config(
                    text="Active" if any(self.detection_history) else "Inactive")
                self.status_labels["FPS"].config(
                    text=f"{np.mean(list(self.fps_history)):.1f}" if self.fps_history else "0")
                self.status_labels["AI Samples"].config(
                    text=str(len(self.intelligence_engine.learning_data)))

                # Update log with recent entries
                if hasattr(logging, 'last_message'):
                    self.log_text.insert(tk.END, logging.last_message + '\n')
                    self.log_text.see(tk.END)

                time.sleep(0.5)
            except Exception as e:
                logging.error(f"Status update error: {e}")
                time.sleep(1)

    def set_mode(self, mode):
        """Set the cursor control mode"""
        self.current_mode = mode
        self.voice_engine.speak(f"Switched to {mode} mode")
        self.log_message(f"Mode changed to: {mode}")

        # Visual feedback
        for m, btn in self.mode_buttons.items():
            if m == mode:
                btn.config(style='Accent.TButton')
            else:
                btn.config(style='TButton')

    def toggle_voice_feedback(self):
        """Toggle voice feedback"""
        self.settings['voice_feedback'] = self.voice_var.get()
        self.voice_engine.enabled = self.settings['voice_feedback']

    def toggle_sound_feedback(self):
        """Toggle sound feedback"""
        self.settings['sound_feedback'] = self.sound_var.get()

    def toggle_high_contrast(self):
        """Toggle high contrast mode"""
        self.settings['high_contrast'] = self.contrast_var.get()
        messagebox.showinfo("Settings", "High contrast mode will apply after restart")

    def toggle_large_buttons(self):
        """Toggle large buttons"""
        self.settings['large_buttons'] = self.large_var.get()
        messagebox.showinfo("Settings", "Button size will apply after restart")

    def set_dwell_time(self, value):
        """Set dwell click time"""
        self.settings['dwell_time'] = float(value)

    def start_calibration(self):
        """Start calibration wizard"""
        calibration_window = CalibrationWizard(self.gui, self)
        calibration_window.run()

    def show_statistics(self):
        """Show system statistics"""
        stats_window = tk.Toplevel(self.gui)
        stats_window.title("System Statistics")
        stats_window.geometry("400x300")

        # Create statistics display
        stats_text = scrolledtext.ScrolledText(stats_window, wrap=tk.WORD)
        stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Generate statistics
        stats = self.generate_statistics()
        stats_text.insert(tk.END, stats)
        stats_text.config(state=tk.DISABLED)

    def generate_statistics(self):
        """Generate system statistics"""
        stats = "Smart Cursor Statistics\n"
        stats += "=" * 30 + "\n\n"

        stats += f"Current Mode: {self.current_mode}\n"
        stats += f"AI Learning Samples: {len(self.intelligence_engine.learning_data)}\n"
        stats += f"Average FPS: {np.mean(list(self.fps_history)):.1f}\n"
        stats += f"Detection Rate: {np.mean([1 if d else 0 for d in self.detection_history]) * 100:.1f}%\n"
        stats += f"Voice Feedback: {'Enabled' if self.settings['voice_feedback'] else 'Disabled'}\n"
        stats += f"Sound Feedback: {'Enabled' if self.settings['sound_feedback'] else 'Disabled'}\n"
        stats += f"Dwell Time: {self.settings['dwell_time']}s\n"

        # Mode usage statistics
        if self.intelligence_engine.learning_data:
            mode_counts = {}
            for data in self.intelligence_engine.learning_data:
                mode = data['mode']
                mode_counts[mode] = mode_counts.get(mode, 0) + 1

            stats += "\nMode Usage:\n"
            total = sum(mode_counts.values())
            for mode, count in sorted(mode_counts.items()):
                percentage = (count / total) * 100
                stats += f"  {mode}: {percentage:.1f}%\n"

        return stats

    def show_help(self):
        """Show help window"""
        help_window = tk.Toplevel(self.gui)
        help_window.title("Help - Smart Cursor Control")
        help_window.geometry("600x400")

        help_text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        help_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        help_content = """
Smart Cursor Control - Accessibility Edition

OVERVIEW:
This system allows you to control your computer cursor using hand gestures,
eye tracking, and intelligent AI assistance. Designed specifically for users
with disabilities.

MODES:
• Normal: Standard hand tracking
• Eye Tracking: Control cursor with eye gaze
• Browsing: Optimized for web navigation
• Gaming: Enhanced precision for games
• Typing: Steady cursor for text input
• Drawing: High precision for creative work

CONTROLS:
• Use GUI buttons or keyboard shortcuts
• Keyboard shortcuts: Ctrl+Shift+[E/H/W/G/T/D]
• Voice commands available when enabled
• Dwell clicking: Hold cursor still to click

ACCESSIBILITY FEATURES:
• Voice feedback for mode changes
• Sound feedback for actions
• High contrast mode available
• Large buttons option
• Adjustable dwell time
• Gesture recognition
• Adaptive cursor speed

CALIBRATION:
Run calibration to improve accuracy for your setup.

TROUBLESHOOTING:
• Ensure good lighting for camera
• Position camera at eye level
• Calibrate regularly for best results
• Check system requirements

For technical support, check the system logs.
        """

        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)

    def log_message(self, message):
        """Log message to GUI and file"""
        logging.info(message)
        # Store last message for GUI updates
        logging.last_message = f"{time.strftime('%H:%M:%S')} - {message}"

    def stop_system(self):
        """Stop the cursor control system"""
        self.running = False
        if self.gui:
            self.gui.quit()

    def run_system(self):
        """Main system loop"""
        self.running = True

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

        try:
            while self.running:
                start_time = time.time()

                success, img = self.cap.read()
                if not success:
                    time.sleep(0.01)
                    continue

                # Process frame
                cursor_x, cursor_y, detection_found = self.process_frame(img, prev_x, prev_y)

                # Apply intelligent smoothing and prediction
                if detection_found:
                    cursor_x, cursor_y = self.apply_intelligence(cursor_x, cursor_y, prev_x, prev_y)
                    prev_x, prev_y = cursor_x, cursor_y

                # Handle clicking
                self.handle_clicking(cursor_x, cursor_y, detection_found)

                # Update trail and display
                self.update_display(img, cursor_x, cursor_y, detection_found)

                # Performance tracking
                processing_time = time.time() - start_time
                self.fps_history.append(1.0 / processing_time if processing_time > 0 else 30)
                self.detection_history.append(detection_found)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break

                # Limit frame rate for stability
                elapsed = time.time() - start_time
                if elapsed < 0.033:  # ~30 FPS
                    time.sleep(0.033 - elapsed)

        except Exception as e:
            logging.error(f"Main loop error: {e}")
            messagebox.showerror("Error", f"System error: {e}")

        finally:
            self.cleanup()

    def process_frame(self, img, prev_x, prev_y):
        """Process camera frame for cursor control"""
        img = cv2.flip(img, 1)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        results = self.holistic.process(img_rgb)

        cursor_x, cursor_y = prev_x, prev_y
        detection_found = False

        # Draw landmarks
        self.draw_landmarks(img, results)

        # Process based on current mode
        if self.current_mode == "eye_tracking" and results.face_landmarks:
            cursor_x, cursor_y, detection_found = self.process_eye_tracking(results.face_landmarks, img.shape)
        else:
            cursor_x, cursor_y, detection_found = self.process_hand_tracking(results, prev_x, prev_y)

        return cursor_x, cursor_y, detection_found

    def draw_landmarks(self, img, results):
        """Draw MediaPipe landmarks on image"""
        try:
            if results.face_landmarks:
                self.mp_draw.draw_landmarks(img, results.face_landmarks,
                                          self.mp_holistic.FACEMESH_CONTOURS,
                                          landmark_drawing_spec=self.mp_draw.DrawingSpec(
                                              color=(0,255,0), thickness=1, circle_radius=1))
            if results.pose_landmarks:
                self.mp_draw.draw_landmarks(img, results.pose_landmarks,
                                          self.mp_holistic.POSE_CONNECTIONS,
                                          landmark_drawing_spec=self.mp_draw.DrawingSpec(
                                              color=(255,0,0), thickness=1, circle_radius=1))
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

    def process_eye_tracking(self, face_landmarks, img_shape):
        """Process eye tracking for cursor control"""
        gaze = self.get_eye_gaze(face_landmarks, img_shape)
        if gaze:
            cursor_x, cursor_y = gaze
            return cursor_x, cursor_y, True
        return None, None, False

    def process_hand_tracking(self, results, prev_x, prev_y):
        """Process hand tracking for cursor control"""
        hand_landmarks = results.right_hand_landmarks or results.left_hand_landmarks
        if hand_landmarks:
            # Get wrist position
            wrist = hand_landmarks.landmark[0]
            cursor_x = int(wrist.x * self.screen_width)
            cursor_y = int(wrist.y * self.screen_height)

            # Apply smoothing
            cursor_x = int(prev_x + (cursor_x - prev_x) * self.settings['smoothing'])
            cursor_y = int(prev_y + (cursor_y - prev_y) * self.settings['smoothing'])

            # Gesture recognition
            if self.settings['gesture_recognition']:
                self.recognize_gesture(hand_landmarks)

            return cursor_x, cursor_y, True
        return prev_x, prev_y, False

    def get_eye_gaze(self, face_landmarks, img_shape):
        """Calculate eye gaze direction"""
        try:
            left_eye_center = np.mean([
                [face_landmarks.landmark[33].x, face_landmarks.landmark[33].y],
                [face_landmarks.landmark[160].x, face_landmarks.landmark[160].y]
            ], axis=0)

            right_eye_center = np.mean([
                [face_landmarks.landmark[362].x, face_landmarks.landmark[362].y],
                [face_landmarks.landmark[385].x, face_landmarks.landmark[385].y]
            ], axis=0)

            nose_tip = [face_landmarks.landmark[1].x, face_landmarks.landmark[1].y]

            eye_center = np.mean([left_eye_center, right_eye_center], axis=0)
            gaze_vector = np.array(nose_tip) - np.array(eye_center)
            gaze_angle = np.arctan2(gaze_vector[1], gaze_vector[0])

            gaze_x = int((gaze_angle / np.pi + 1) * self.screen_width / 2)
            gaze_y = int((np.linalg.norm(gaze_vector) * 2) * self.screen_height)

            gaze_x = np.clip(gaze_x, 0, self.screen_width - 1)
            gaze_y = np.clip(gaze_y, 0, self.screen_height - 1)

            return gaze_x, gaze_y
        except Exception as e:
            logging.error(f"Eye gaze calculation error: {e}")
            return None

    def recognize_gesture(self, hand_landmarks):
        """Recognize hand gestures for additional commands"""
        try:
            # Simple gesture recognition - thumb and index pinch for click
            index_tip = hand_landmarks.landmark[8]
            thumb_tip = hand_landmarks.landmark[4]
            distance = np.sqrt((index_tip.x - thumb_tip.x)**2 + (index_tip.y - thumb_tip.y)**2)

            # Open palm gesture (all fingers extended)
            finger_tips = [8, 12, 16, 20]  # Index, middle, ring, pinky tips
            finger_pips = [6, 10, 14, 18]  # Corresponding PIP joints

            open_palm = True
            for tip, pip in zip(finger_tips, finger_pips):
                if hand_landmarks.landmark[tip].y > hand_landmarks.landmark[pip].y:
                    open_palm = False
                    break

            current_time = time.time()
            if current_time - self.last_gesture_time > 1.0:  # Gesture cooldown
                if distance < 0.05:
                    self.perform_gesture_action("pinch")
                    self.last_gesture_time = current_time
                elif open_palm:
                    self.perform_gesture_action("open_palm")
                    self.last_gesture_time = current_time

        except Exception as e:
            logging.error(f"Gesture recognition error: {e}")

    def perform_gesture_action(self, gesture):
        """Perform action based on recognized gesture"""
        if gesture == "pinch":
            pyautogui.click()
            self.voice_engine.speak("Click")
            if self.settings['sound_feedback']:
                winsound.Beep(800, 100)
        elif gesture == "open_palm":
            pyautogui.rightClick()
            self.voice_engine.speak("Right click")
            if self.settings['sound_feedback']:
                winsound.Beep(600, 100)

    def apply_intelligence(self, cursor_x, cursor_y, prev_x, prev_y):
        """Apply AI intelligence to cursor movement"""
        # Adaptive smoothing based on movement speed
        if self.settings['adaptive_speed'] and len(self.movement_history) > 5:
            recent_speeds = [np.sqrt((x2-x1)**2 + (y2-y1)**2) for (x1,y1,x2,y2) in
                           list(self.movement_history)[-5:]]
            avg_speed = np.mean(recent_speeds)

            # Adjust smoothing based on speed
            if avg_speed > 50:  # Fast movement
                smoothing = max(0.3, self.settings['smoothing'] - 0.2)
            elif avg_speed < 10:  # Slow movement
                smoothing = min(0.95, self.settings['smoothing'] + 0.1)
            else:
                smoothing = self.settings['smoothing']
        else:
            smoothing = self.settings['smoothing']

        # Apply smoothing
        cursor_x = int(prev_x + (cursor_x - prev_x) * smoothing)
        cursor_y = int(prev_y + (cursor_y - prev_y) * smoothing)

        # Update movement history
        self.movement_history.append((prev_x, prev_y, cursor_x, cursor_y))

        return cursor_x, cursor_y

    def handle_clicking(self, cursor_x, cursor_y, detection_found):
        """Handle clicking mechanisms"""
        # Dwell clicking
        if detection_found and self.settings['dwell_time'] > 0:
            current_pos = (cursor_x, cursor_y)

            if self.dwell_position is None or \
               np.sqrt((current_pos[0] - self.dwell_position[0])**2 +
                      (current_pos[1] - self.dwell_position[1])**2) > 10:  # 10 pixel threshold
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
                    self.voice_engine.speak("Dwell click")
                    if self.settings['sound_feedback']:
                        winsound.Beep(1000, 200)
                    # Reset for next dwell
                    self.dwell_position = None

        # Learn from user behavior
        self.intelligence_engine.learn_user_behavior(
            cursor_x, cursor_y, self.current_mode,
            self.intelligence_engine.analyze_screen_context(), time.time()
        )

        # Move cursor
        if detection_found:
            try:
                pyautogui.moveTo(cursor_x, cursor_y)
            except Exception as e:
                logging.error(f"Cursor movement error: {e}")

    def update_display(self, img, cursor_x, cursor_y, detection_found):
        """Update the camera display with information"""
        # Update trail
        self.trail_points.append((cursor_x, cursor_y))

        # Draw trail
        try:
            for i, point in enumerate(list(self.trail_points)[-15:]):
                alpha = (i + 1) / 15
                if self.current_mode == "eye_tracking":
                    color = (0, 0, int(255 * alpha))
                else:
                    color = (0, int(255 * alpha), 0)
                cv2.circle(img, (int(point[0] * img.shape[1] / self.screen_width),
                               int(point[1] * img.shape[0] / self.screen_height)), 2, color, -1)
        except Exception as e:
            logging.error(f"Trail drawing error: {e}")

        # Draw dwell indicator
        if self.dwell_active:
            cv2.circle(img, (img.shape[1]//2, img.shape[0]//2), 50, (0, 255, 255), 3)

        # Display information
        try:
            fps = np.mean(list(self.fps_history)) if self.fps_history else 0
            cv2.putText(img, f"Mode: {self.current_mode} (AI)", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(img, f"FPS: {fps:.1f}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(img, f"AI Learning: {len(self.intelligence_engine.learning_data)}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
            cv2.putText(img, f"Detection: {'OK' if detection_found else 'FREE'}", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if detection_found else (255, 255, 255), 2)

            if self.dwell_active:
                cv2.putText(img, "DWELL ACTIVE", (10, 150),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        except Exception as e:
            logging.error(f"Text overlay error: {e}")

        cv2.imshow('Smart Cursor Control - Accessibility Edition', img)

    def cleanup(self):
        """Clean up resources"""
        logging.info("Shutting down Smart Cursor Accessibility System")
        self.intelligence_engine.save_learning_data()
        self.save_settings()
        self.cap.release()
        cv2.destroyAllWindows()
        self.holistic.close()
        print("Smart Cursor Accessibility System shutdown complete")


class IntelligenceEngine:
    """AI engine for intelligent cursor behavior"""
    def __init__(self):
        self.learning_data = []
        self.context_history = deque(maxlen=100)
        self.load_learning_data()

    def load_learning_data(self):
        try:
            if os.path.exists('smart_cursor_learning.pkl'):
                with open('smart_cursor_learning.pkl', 'rb') as f:
                    self.learning_data = pickle.load(f)
        except Exception as e:
            logging.error(f"Failed to load learning data: {e}")

    def save_learning_data(self):
        try:
            with open('smart_cursor_learning.pkl', 'wb') as f:
                pickle.dump(self.learning_data, f)
        except Exception as e:
            logging.error(f"Failed to save learning data: {e}")

    def analyze_screen_context(self):
        """Analyze screen content to determine context"""
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

                # Get window title
                try:
                    import win32gui
                    window_title = win32gui.GetWindowText(win32gui.GetForegroundWindow())
                except:
                    window_title = "unknown"

                title_lower = window_title.lower()

                # Context detection
                if any(word in title_lower for word in ['chrome', 'firefox', 'edge', 'safari', 'browser']):
                    return "browsing"
                elif any(word in title_lower for word in ['vscode', 'notepad', 'word', 'excel', 'code']):
                    return "typing"
                elif any(word in title_lower for word in ['game', 'gaming', 'steam']):
                    return "gaming"
                else:
                    return "normal"

        except Exception as e:
            logging.error(f"Screen analysis error: {e}")
            return "normal"

    def learn_user_behavior(self, cursor_x, cursor_y, mode, context, timestamp):
        """Learn user behavior patterns"""
        behavior_data = {
            'cursor_pos': (cursor_x, cursor_y),
            'mode': mode,
            'context': context,
            'timestamp': timestamp,
            'screen_region': self.get_screen_region(cursor_x, cursor_y)
        }

        self.learning_data.append(behavior_data)

        # Keep only recent data
        if len(self.learning_data) > 2000:
            self.learning_data = self.learning_data[-2000:]

    def get_screen_region(self, x, y):
        """Get screen region for cursor position"""
        screen_width, screen_height = pyautogui.size()
        if x < screen_width // 4:
            return "left"
        elif x > 3 * screen_width // 4:
            return "right"
        elif y < screen_height // 4:
            return "top"
        elif y > 3 * screen_height // 4:
            return "bottom"
        else:
            return "center"


class VoiceEngine:
    """Voice feedback engine"""
    def __init__(self):
        self.enabled = True
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 180)
            self.engine.setProperty('volume', 0.8)
        except Exception as e:
            logging.error(f"Voice engine initialization error: {e}")
            self.enabled = False

    def speak(self, text):
        """Speak text if voice is enabled"""
        if self.enabled and self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logging.error(f"Voice speak error: {e}")


class CalibrationWizard:
    """Calibration wizard for improving accuracy"""
    def __init__(self, parent, system):
        self.parent = parent
        self.system = system
        self.window = None

    def run(self):
        """Run the calibration wizard"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Calibration Wizard")
        self.window.geometry("500x400")

        # Instructions
        ttk.Label(self.window, text="Calibration Wizard",
                 font=('Arial', 14, 'bold')).pack(pady=10)

        instructions = """
Follow these steps to calibrate your Smart Cursor:

1. Eye Calibration:
   - Select Eye Tracking mode
   - Look at each corner of the screen for 3 seconds
   - The system will learn your eye movements

2. Hand Calibration:
   - Select Hand Tracking mode
   - Move your hand to each corner of the camera view
   - Hold each position for 2 seconds

3. Screen Calibration:
   - Move cursor to each screen corner using your method
   - Click 'Calibrate' button at each corner

Click 'Start Calibration' to begin.
        """

        text_widget = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, height=15)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, instructions)
        text_widget.config(state=tk.DISABLED)

        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Start Calibration",
                  command=self.start_calibration).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Skip",
                  command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

    def start_calibration(self):
        """Start the calibration process"""
        # Simple calibration - just show message for now
        messagebox.showinfo("Calibration", "Calibration started. Follow the on-screen instructions.")
        # TODO: Implement actual calibration logic
        self.window.destroy()


def main():
    """Main function"""
    try:
        system = SmartCursorAccessibility()
        system.run_system()
    except Exception as e:
        logging.error(f"Application error: {e}")
        messagebox.showerror("Error", f"Failed to start Smart Cursor: {e}")


if __name__ == "__main__":
    main()
