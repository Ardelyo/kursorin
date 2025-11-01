import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import tkinter as tk
from tkinter import messagebox
import time
import threading
import logging
import signal
import sys
import os
import pickle
from collections import deque
from PIL import Image
import pytesseract
import mss
import json
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Set up logging
logging.basicConfig(filename='cursor_system.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize MediaPipe Holistic for full body tracking
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_draw = mp.solutions.drawing_utils

# Get screen size
screen_width, screen_height = pyautogui.size()

# Cursor trail (drawn on camera feed)
trail_points = deque(maxlen=20)

# Modes including intelligent modes
modes = ["normal", "browsing", "gaming", "typing", "eye_tracking", "presentation", "drawing"]
current_mode = "normal"

# Tkinter popups
def show_popup(message, title="Cursor System"):
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(title, message)
        root.destroy()
    except Exception as e:
        logging.error(f"Popup error: {e}")

# Intelligence Engine Components
class IntelligenceEngine:
    def __init__(self):
        self.user_patterns = {}
        self.context_history = deque(maxlen=100)
        self.screen_analysis_cache = {}
        self.learning_data = []
        self.load_learning_data()

    def load_learning_data(self):
        try:
            if os.path.exists('learning_data.pkl'):
                with open('learning_data.pkl', 'rb') as f:
                    self.learning_data = pickle.load(f)
        except Exception as e:
            logging.error(f"Failed to load learning data: {e}")

    def save_learning_data(self):
        try:
            with open('learning_data.pkl', 'wb') as f:
                pickle.dump(self.learning_data, f)
        except Exception as e:
            logging.error(f"Failed to save learning data: {e}")

    def analyze_screen_context(self):
        """Analyze screen content to determine context"""
        try:
            with mss.mss() as sct:
                # Capture screen
                monitor = sct.monitors[1]  # Primary monitor
                screenshot = sct.grab(monitor)

                # Convert to PIL Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

                # Get window title (basic context)
                try:
                    import win32gui  # type: ignore
                    window_title = win32gui.GetWindowText(win32gui.GetForegroundWindow())
                except:
                    window_title = "unknown"

                # Analyze colors (simple clustering)
                img_array = np.array(img)
                pixels = img_array.reshape(-1, 3)
                pixels_sample = pixels[np.random.choice(len(pixels), min(10000, len(pixels)), replace=False)]

                # Color clustering
                kmeans = KMeans(n_clusters=5, n_init=10)
                kmeans.fit(pixels_sample)
                dominant_colors = kmeans.cluster_centers_

                # Context classification based on analysis
                context = self.classify_context(window_title, dominant_colors, img_array)

                return context

        except Exception as e:
            logging.error(f"Screen analysis error: {e}")
            return "normal"

    def classify_context(self, window_title, dominant_colors, img_array):
        """Classify screen context based on analysis"""
        title_lower = window_title.lower()

        # Browser detection
        if any(word in title_lower for word in ['chrome', 'firefox', 'edge', 'safari', 'browser']):
            return "browsing"

        # Gaming detection (dark colors, high contrast)
        if len(dominant_colors) >= 3:
            brightness = np.mean(dominant_colors)
            contrast = np.std(dominant_colors)
            if brightness < 100 and contrast > 50:  # Dark with high contrast = gaming
                return "gaming"

        # Text-heavy applications (writing, coding)
        if any(word in title_lower for word in ['vscode', 'notepad', 'word', 'excel', 'code']):
            return "typing"

        # Presentation mode (large text, simple layout)
        avg_color = np.mean(img_array, axis=(0, 1))
        if avg_color[0] > 200 and avg_color[1] > 200 and avg_color[2] > 200:  # Very bright = presentation
            return "presentation"

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

        # Keep only recent data (last 1000 entries)
        if len(self.learning_data) > 1000:
            self.learning_data = self.learning_data[-1000:]

    def get_screen_region(self, x, y):
        """Get screen region for cursor position"""
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

    def predict_best_mode(self, context, cursor_pos):
        """Predict the best mode based on learning data"""
        if not self.learning_data:
            return context

        # Find similar situations in learning data
        similar_situations = [
            d for d in self.learning_data
            if d['context'] == context and d['screen_region'] == self.get_screen_region(*cursor_pos)
        ]

        if not similar_situations:
            return context

        # Find most common mode for this situation
        mode_counts = {}
        for situation in similar_situations[-50:]:  # Last 50 similar situations
            mode = situation['mode']
            mode_counts[mode] = mode_counts.get(mode, 0) + 1

        if mode_counts:
            predicted_mode = max(mode_counts, key=mode_counts.get)
            confidence = mode_counts[predicted_mode] / sum(mode_counts.values())

            if confidence > 0.6:  # High confidence threshold
                return predicted_mode

        return context

    def suggest_optimizations(self):
        """Suggest system optimizations based on usage patterns"""
        if len(self.learning_data) < 100:
            return []

        suggestions = []

        # Analyze mode usage
        mode_usage = {}
        for data in self.learning_data:
            mode = data['mode']
            mode_usage[mode] = mode_usage.get(mode, 0) + 1

        total_actions = len(self.learning_data)

        # Suggest frequently used modes
        for mode, count in mode_usage.items():
            percentage = (count / total_actions) * 100
            if percentage > 30 and mode != "normal":
                suggestions.append(f"Consider making '{mode}' mode your default (used {percentage:.1f}% of time)")

        return suggestions

# Initialize Intelligence Engine
intelligence = IntelligenceEngine()

# Eye tracking function
def get_eye_gaze(face_landmarks, img_shape):
    if not face_landmarks:
        return None

    try:
        left_eye_center = np.mean([[face_landmarks.landmark[33].x, face_landmarks.landmark[33].y],
                                   [face_landmarks.landmark[160].x, face_landmarks.landmark[160].y]], axis=0)
        right_eye_center = np.mean([[face_landmarks.landmark[362].x, face_landmarks.landmark[362].y],
                                    [face_landmarks.landmark[385].x, face_landmarks.landmark[385].y]], axis=0)
        nose_tip = [face_landmarks.landmark[1].x, face_landmarks.landmark[1].y]

        eye_center = np.mean([left_eye_center, right_eye_center], axis=0)
        gaze_vector = np.array(nose_tip) - np.array(eye_center)
        gaze_angle = np.arctan2(gaze_vector[1], gaze_vector[0])

        gaze_x = int((gaze_angle / np.pi + 1) * screen_width / 2)
        gaze_y = int((np.linalg.norm(gaze_vector) * 2) * screen_height)

        gaze_x = np.clip(gaze_x, 0, screen_width - 1)
        gaze_y = np.clip(gaze_y, 0, screen_height - 1)

        return gaze_x, gaze_y
    except Exception as e:
        logging.error(f"Eye gaze calculation error: {e}")
        return None

# Detect context
def detect_context(x, y):
    if current_mode == "eye_tracking":
        return "eye_tracking"
    elif x < screen_width // 4:
        return "browsing"
    elif x > 3 * screen_width // 4:
        return "gaming"
    elif y > 3 * screen_height // 4:
        return "typing"
    else:
        return "normal"

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    logging.info("Shutdown signal received")
    global running
    running = False

signal.signal(signal.SIGINT, signal_handler)

# Watchdog timer
last_frame_time = time.time()
watchdog_timeout = 10

def check_watchdog():
    global last_frame_time, running
    while running:
        if time.time() - last_frame_time > watchdog_timeout:
            logging.error("Watchdog timeout: No frames processed")
            running = False
            break
        time.sleep(1)

# Start watchdog thread
watchdog_thread = threading.Thread(target=check_watchdog, daemon=True)
watchdog_thread.start()

# Context analysis thread
last_context_analysis = 0
context_analysis_interval = 5  # seconds

def context_analysis_worker():
    global last_context_analysis, current_mode
    while running:
        if time.time() - last_context_analysis > context_analysis_interval:
            try:
                screen_context = intelligence.analyze_screen_context()
                predicted_mode = intelligence.predict_best_mode(screen_context, (prev_x, prev_y))

                if predicted_mode != current_mode and predicted_mode != "normal":
                    current_mode = predicted_mode
                    threading.Thread(target=show_popup,
                                   args=(f"AI switched to {current_mode} mode based on screen context"), daemon=True).start()

                last_context_analysis = time.time()
            except Exception as e:
                logging.error(f"Context analysis error: {e}")

        time.sleep(1)

# Start context analysis thread
context_thread = threading.Thread(target=context_analysis_worker, daemon=True)
context_thread.start()

# Open webcam with error handling
try:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Cannot open webcam")
except Exception as e:
    logging.error(f"Webcam initialization error: {e}")
    show_popup("Error: Cannot access webcam", "System Error")
    sys.exit(1)

# Variables
prev_x, prev_y = screen_width // 2, screen_height // 2
smoothing = 0.7
last_click = 0
click_cooldown = 0.5

# Performance monitoring
processing_times = deque(maxlen=10)

# Main loop
running = True
try:
    while running:
        start_time = time.time()

        success, img = cap.read()
        last_frame_time = time.time()

        if not success:
            logging.warning("Failed to read frame from webcam")
            time.sleep(0.01)
            continue

        img = cv2.flip(img, 1)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        results = holistic.process(img_rgb)

        cursor_x, cursor_y = prev_x, prev_y
        detection_found = False

        # Fast landmark drawing
        try:
            if results.face_landmarks:
                mp_draw.draw_landmarks(img, results.face_landmarks, mp_holistic.FACEMESH_CONTOURS,
                                     landmark_drawing_spec=mp_draw.DrawingSpec(color=(0,255,0), thickness=1, circle_radius=1))
            if results.pose_landmarks:
                mp_draw.draw_landmarks(img, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
                                     landmark_drawing_spec=mp_draw.DrawingSpec(color=(255,0,0), thickness=1, circle_radius=1))
            if results.left_hand_landmarks:
                mp_draw.draw_landmarks(img, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                                     landmark_drawing_spec=mp_draw.DrawingSpec(color=(0,0,255), thickness=1, circle_radius=1))
            if results.right_hand_landmarks:
                mp_draw.draw_landmarks(img, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                                     landmark_drawing_spec=mp_draw.DrawingSpec(color=(255,255,0), thickness=1, circle_radius=1))
        except Exception as e:
            logging.error(f"Drawing landmarks error: {e}")

        # Eye tracking mode
        if current_mode == "eye_tracking" and results.face_landmarks:
            gaze = get_eye_gaze(results.face_landmarks, img.shape)
            if gaze:
                cursor_x, cursor_y = gaze
                cursor_x = int(prev_x + (cursor_x - prev_x) * smoothing)
                cursor_y = int(prev_y + (cursor_y - prev_y) * smoothing)
                detection_found = True
        else:
            # Hand tracking
            hand_landmarks = results.right_hand_landmarks or results.left_hand_landmarks
            if hand_landmarks:
                wrist = hand_landmarks.landmark[0]
                cursor_x = int(wrist.x * screen_width)
                cursor_y = int(wrist.y * screen_height)
                cursor_x = int(prev_x + (cursor_x - prev_x) * smoothing)
                cursor_y = int(prev_y + (cursor_y - prev_y) * smoothing)
                detection_found = True

                # Click detection
                try:
                    index_tip = hand_landmarks.landmark[8]
                    thumb_tip = hand_landmarks.landmark[4]
                    distance = np.sqrt((index_tip.x - thumb_tip.x)**2 + (index_tip.y - thumb_tip.y)**2)

                    if distance < 0.05 and time.time() - last_click > click_cooldown:
                        pyautogui.click()
                        last_click = time.time()
                        img[:] = 255
                        cv2.imshow('Camera Cursor Control v4 - AI Enhanced', img)
                        cv2.waitKey(50)
                except Exception as e:
                    logging.error(f"Click detection error: {e}")

        # Learn user behavior
        intelligence.learn_user_behavior(cursor_x, cursor_y, current_mode,
                                       intelligence.analyze_screen_context(), time.time())

        # Detect new mode
        new_mode = detect_context(cursor_x, cursor_y)
        if new_mode != current_mode:
            current_mode = new_mode
            threading.Thread(target=show_popup, args=(f"Switched to {current_mode} mode"), daemon=True).start()

        # Move cursor freely
        if detection_found:
            try:
                pyautogui.moveTo(cursor_x, cursor_y)
                prev_x, prev_y = cursor_x, cursor_y
            except Exception as e:
                logging.error(f"Cursor movement error: {e}")

        # Update trail
        trail_points.append((cursor_x, cursor_y))

        # Draw trail efficiently
        try:
            for i, point in enumerate(list(trail_points)[-10:]):
                alpha = (i + 1) / 10
                color = (0, int(255 * alpha), 0) if current_mode != "eye_tracking" else (0, 0, int(255 * alpha))
                cv2.circle(img, (int(point[0] * img.shape[1] / screen_width), int(point[1] * img.shape[0] / screen_height)), 2, color, -1)
        except Exception as e:
            logging.error(f"Trail drawing error: {e}")

        # Display info
        try:
            fps = len(processing_times) / sum(processing_times) if processing_times else 30
            processing_times.append(time.time() - start_time)

            cv2.putText(img, f"Mode: {current_mode} (AI)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 255, 0) if current_mode != "eye_tracking" else (0, 0, 255), 2)
            cv2.putText(img, f"FPS: {fps:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(img, f"AI Learning: {len(intelligence.learning_data)} samples", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
            cv2.putText(img, f"Detection: {'OK' if detection_found else 'FREE'}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 255, 0) if detection_found else (255, 255, 255), 2)
        except Exception as e:
            logging.error(f"Text overlay error: {e}")

        cv2.imshow('Camera Cursor Control v4 - AI Enhanced', img)

        # Handle keys
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            running = False
        elif key == ord('e'):
            current_mode = "eye_tracking" if current_mode != "eye_tracking" else "normal"
            threading.Thread(target=show_popup, args=(f"Toggled to {current_mode} mode"), daemon=True).start()
        elif key == ord('s'):  # Show suggestions
            suggestions = intelligence.suggest_optimizations()
            if suggestions:
                threading.Thread(target=show_popup, args=(f"AI Suggestions:\n" + "\n".join(suggestions)), daemon=True).start()
            else:
                threading.Thread(target=show_popup, args="Not enough data for suggestions yet", daemon=True).start()

except Exception as e:
    logging.error(f"Main loop error: {e}")
    show_popup(f"System error: {e}", "Error")

finally:
    logging.info("Shutting down AI-enhanced system")
    intelligence.save_learning_data()
    cap.release()
    cv2.destroyAllWindows()
    holistic.close()
    print("AI-enhanced system shutdown complete")
