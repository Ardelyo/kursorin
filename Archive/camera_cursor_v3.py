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

# Set up logging
logging.basicConfig(filename='cursor_system.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize MediaPipe Holistic for full body tracking
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_draw = mp.solutions.drawing_utils

# Get screen size
screen_width, screen_height = pyautogui.size()

# Cursor trail (drawn on camera feed instead of separate window)
trail_points = []
trail_length = 20

# Modes including eye tracking
modes = ["normal", "browsing", "gaming", "typing", "eye_tracking"]
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

# Eye tracking function
def get_eye_gaze(face_landmarks, img_shape):
    if not face_landmarks:
        return None

    try:
        # Get eye landmarks (approximate gaze)
        left_eye_center = np.mean([[face_landmarks.landmark[33].x, face_landmarks.landmark[33].y],
                                   [face_landmarks.landmark[160].x, face_landmarks.landmark[160].y]], axis=0)
        right_eye_center = np.mean([[face_landmarks.landmark[362].x, face_landmarks.landmark[362].y],
                                    [face_landmarks.landmark[385].x, face_landmarks.landmark[385].y]], axis=0)
        nose_tip = [face_landmarks.landmark[1].x, face_landmarks.landmark[1].y]

        # Simple gaze estimation
        eye_center = np.mean([left_eye_center, right_eye_center], axis=0)
        gaze_vector = np.array(nose_tip) - np.array(eye_center)
        gaze_angle = np.arctan2(gaze_vector[1], gaze_vector[0])

        # Map to screen coordinates
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
watchdog_timeout = 10  # seconds

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
smoothing = 0.3
last_click = 0
click_cooldown = 0.5

# Performance optimizations
frame_skip = 0  # Process every frame
processing_times = []

# Main loop
running = True
try:
    while running:
        start_time = time.time()

        success, img = cap.read()
        last_frame_time = time.time()

        if not success:
            logging.warning("Failed to read frame from webcam")
            time.sleep(0.01)  # Faster retry
            continue

        img = cv2.flip(img, 1)

        # Skip frames for performance if needed
        frame_skip += 1
        if frame_skip % 1 != 0:  # Process every frame
            cv2.imshow('Camera Cursor Control v3 - Holistic', img)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                running = False
            continue

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Process holistic with error handling
        try:
            results = holistic.process(img_rgb)
        except Exception as e:
            logging.error(f"Holistic processing error: {e}")
            continue

        cursor_x, cursor_y = prev_x, prev_y
        detection_found = False

        # Fast landmark drawing (only contours for performance)
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

        # Eye tracking mode - optimized
        if current_mode == "eye_tracking" and results.face_landmarks:
            gaze = get_eye_gaze(results.face_landmarks, img.shape)
            if gaze:
                cursor_x, cursor_y = gaze
                # Reduced smoothing for better responsiveness
                cursor_x = int(prev_x + (cursor_x - prev_x) * 0.7)
                cursor_y = int(prev_y + (cursor_y - prev_y) * 0.7)
                detection_found = True
        else:
            # Hand tracking - optimized
            hand_landmarks = results.right_hand_landmarks or results.left_hand_landmarks
            if hand_landmarks:
                wrist = hand_landmarks.landmark[0]
                cursor_x = int(wrist.x * screen_width)
                cursor_y = int(wrist.y * screen_height)
                # Reduced smoothing for better responsiveness
                cursor_x = int(prev_x + (cursor_x - prev_x) * 0.7)
                cursor_y = int(prev_y + (cursor_y - prev_y) * 0.7)
                detection_found = True

                # Click detection - optimized
                try:
                    index_tip = hand_landmarks.landmark[8]
                    thumb_tip = hand_landmarks.landmark[4]
                    distance = np.sqrt((index_tip.x - thumb_tip.x)**2 + (index_tip.y - thumb_tip.y)**2)

                    if distance < 0.05 and time.time() - last_click > click_cooldown:
                        pyautogui.click()
                        last_click = time.time()
                        # Faster flash effect
                        img[:] = 255
                        cv2.imshow('Camera Cursor Control v3 - Holistic', img)
                        cv2.waitKey(50)
                except Exception as e:
                    logging.error(f"Click detection error: {e}")

        # Detect new mode
        new_mode = detect_context(cursor_x, cursor_y)
        if new_mode != current_mode:
            current_mode = new_mode
            threading.Thread(target=show_popup, args=(f"Switched to {current_mode} mode"), daemon=True).start()

        # Move cursor freely - always update when detection found
        if detection_found:
            try:
                pyautogui.moveTo(cursor_x, cursor_y)
                prev_x, prev_y = cursor_x, cursor_y
            except Exception as e:
                logging.error(f"Cursor movement error: {e}")
        # When detection lost, cursor is FREE - user can use mouse normally

        # Update trail (drawn on camera feed) - optimized
        trail_points.append((cursor_x, cursor_y))
        if len(trail_points) > trail_length:
            trail_points.pop(0)

        # Draw trail efficiently
        try:
            for i, point in enumerate(trail_points[-10:]):  # Only last 10 points for performance
                alpha = (i + 1) / 10
                color = (0, int(255 * alpha), 0) if current_mode != "eye_tracking" else (0, 0, int(255 * alpha))
                cv2.circle(img, (int(point[0] * img.shape[1] / screen_width), int(point[1] * img.shape[0] / screen_height)), 2, color, -1)
        except Exception as e:
            logging.error(f"Trail drawing error: {e}")

        # Display info - optimized
        try:
            fps = 1.0 / (time.time() - start_time) if processing_times else 30
            processing_times.append(time.time() - start_time)
            if len(processing_times) > 10:
                processing_times.pop(0)
            avg_fps = len(processing_times) / sum(processing_times)

            cv2.putText(img, f"Mode: {current_mode}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0, 255, 0) if current_mode != "eye_tracking" else (0, 0, 255), 2)
            cv2.putText(img, f"FPS: {avg_fps:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(img, f"Detection: {'OK' if detection_found else 'FREE'}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 255, 0) if detection_found else (255, 255, 255), 2)
        except Exception as e:
            logging.error(f"Text overlay error: {e}")

        cv2.imshow('Camera Cursor Control v3 - Holistic', img)

        # Exit on 'q' or switch to eye tracking on 'e'
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            running = False
        elif key == ord('e'):
            current_mode = "eye_tracking" if current_mode != "eye_tracking" else "normal"
            threading.Thread(target=show_popup, args=(f"Toggled to {current_mode} mode"), daemon=True).start()

except Exception as e:
    logging.error(f"Main loop error: {e}")
    show_popup(f"System error: {e}", "Error")

finally:
    logging.info("Shutting down system")
    cap.release()
    cv2.destroyAllWindows()
    holistic.close()
    print("System shutdown complete")
