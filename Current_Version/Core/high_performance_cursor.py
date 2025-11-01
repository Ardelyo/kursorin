#!/usr/bin/env python3
"""
High Performance Cursor Control Layer
Optimized for maximum speed and accuracy
"""

import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import threading
import queue
import logging
from collections import deque
from typing import Tuple, Optional, List
import math

class KalmanFilter:
    """Simple Kalman filter for cursor smoothing"""
    def __init__(self, process_noise=0.01, measurement_noise=0.1):
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.estimated = np.array([0.0, 0.0])
        self.estimate_error = np.array([1.0, 1.0])
        self.first_measurement = True

    def update(self, measurement: np.ndarray) -> np.ndarray:
        """Update filter with new measurement"""
        if self.first_measurement:
            self.estimated = measurement.copy()
            self.first_measurement = False
            return self.estimated

        # Prediction step
        prediction_error = self.estimate_error + self.process_noise

        # Update step
        kalman_gain = prediction_error / (prediction_error + self.measurement_noise)
        self.estimated = self.estimated + kalman_gain * (measurement - self.estimated)
        self.estimate_error = (1 - kalman_gain) * prediction_error

        return self.estimated.copy()

class GestureRecognizer:
    """Advanced gesture recognition for clicking"""
    def __init__(self):
        self.gesture_history = deque(maxlen=5)
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.3  # seconds

    def detect_gesture(self, hand_landmarks) -> Optional[str]:
        """Detect hand gestures"""
        if not hand_landmarks:
            return None

        try:
            # Get finger tip positions
            thumb_tip = hand_landmarks.landmark[4]
            index_tip = hand_landmarks.landmark[8]
            middle_tip = hand_landmarks.landmark[12]
            ring_tip = hand_landmarks.landmark[16]
            pinky_tip = hand_landmarks.landmark[20]

            # Get finger MCP joints
            thumb_mcp = hand_landmarks.landmark[2]
            index_mcp = hand_landmarks.landmark[5]
            middle_mcp = hand_landmarks.landmark[9]
            ring_mcp = hand_landmarks.landmark[13]
            pinky_mcp = hand_landmarks.landmark[17]

            # Calculate distances for gesture detection
            thumb_index_dist = self._distance(thumb_tip, index_tip)

            # Pinch gesture (thumb and index close)
            if thumb_index_dist < 0.05:
                return "pinch"

            # Fist gesture (all fingers curled)
            fingers_curled = 0
            finger_tips = [index_tip, middle_tip, ring_tip, pinky_tip]
            finger_mcps = [index_mcp, middle_mcp, ring_mcp, pinky_mcp]

            for tip, mcp in zip(finger_tips, finger_mcps):
                if tip.y > mcp.y:  # Finger curled (tip below MCP)
                    fingers_curled += 1

            if fingers_curled >= 3:
                return "fist"

            # Open palm (relaxed hand)
            if fingers_curled <= 1:
                return "open"

        except Exception as e:
            logging.error(f"Gesture detection error: {e}")

        return None

    def _distance(self, point1, point2) -> float:
        """Calculate distance between two landmarks"""
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

    def should_trigger_action(self, gesture: str) -> bool:
        """Check if gesture should trigger action with cooldown"""
        current_time = time.time()
        if current_time - self.last_gesture_time < self.gesture_cooldown:
            return False

        # Add to history
        self.gesture_history.append((gesture, current_time))

        # Check for gesture changes (rising edge)
        if len(self.gesture_history) >= 2:
            prev_gesture, prev_time = self.gesture_history[-2]
            if prev_gesture != gesture:
                self.last_gesture_time = current_time
                return True

        return False

class HighPerformanceCursor:
    """High-performance cursor control with optimized processing"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Optimized MediaPipe settings
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=0.3,  # Lower for speed
            min_tracking_confidence=0.3,   # Lower for speed
            model_complexity=0  # Fastest model
        )
        self.mp_draw = mp.solutions.drawing_utils

        # Advanced filtering and smoothing
        self.kalman_filter = KalmanFilter(process_noise=0.005, measurement_noise=0.05)

        # Gesture recognition
        self.gesture_recognizer = GestureRecognizer()

        # Performance tracking
        self.fps_history = deque(maxlen=60)
        self.latency_history = deque(maxlen=60)
        self.detection_history = deque(maxlen=60)

        # Processing queues for multi-threading
        self.frame_queue = queue.Queue(maxsize=2)
        self.result_queue = queue.Queue(maxsize=2)

        # Control state
        self.last_detection_time = time.time()
        self.cursor_position = np.array([screen_width // 2, screen_height // 2])
        self.last_click_time = 0
        self.click_cooldown = 0.2

        # Processing thread
        self.processing_thread = None
        self.running = False

    def start_processing(self):
        """Start the processing thread"""
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()

    def stop_processing(self):
        """Stop the processing thread"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)

    def process_frame_async(self, frame: np.ndarray) -> Tuple[np.ndarray, bool, Optional[str]]:
        """Process frame asynchronously"""
        if not self.running:
            return self.cursor_position, False, None

        try:
            # Try to get result from queue (non-blocking)
            if not self.result_queue.empty():
                result = self.result_queue.get_nowait()
                self.result_queue.task_done()
                return result

            # Add new frame to processing queue
            if self.frame_queue.empty():
                self.frame_queue.put(frame.copy())

        except queue.Empty:
            pass

        # Return last known position if no new result
        return self.cursor_position, False, None

    def _processing_loop(self):
        """Main processing loop in separate thread"""
        while self.running:
            try:
                # Get frame from queue
                frame = self.frame_queue.get(timeout=0.1)
                start_time = time.time()

                # Process frame
                cursor_pos, detection_found, gesture = self._process_frame_sync(frame)

                # Put result in queue
                result = (cursor_pos, detection_found, gesture)
                try:
                    self.result_queue.put(result, timeout=0.1)
                except queue.Full:
                    # Remove old result if queue full
                    try:
                        self.result_queue.get_nowait()
                        self.result_queue.task_done()
                        self.result_queue.put(result)
                    except queue.Empty:
                        pass

                # Track performance
                processing_time = time.time() - start_time
                self.latency_history.append(processing_time)
                self.fps_history.append(1.0 / processing_time if processing_time > 0 else 60)
                self.detection_history.append(detection_found)

            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Processing loop error: {e}")
                time.sleep(0.01)

    def _process_frame_sync(self, frame: np.ndarray) -> Tuple[np.ndarray, bool, Optional[str]]:
        """Synchronous frame processing with optimizations"""
        # Flip and convert
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        try:
            # Process with MediaPipe
            results = self.holistic.process(frame_rgb)
        except Exception as e:
            logging.error(f"MediaPipe processing error: {e}")
            return self.cursor_position, False, None

        cursor_pos = self.cursor_position.copy()
        detection_found = False
        gesture = None

        # Enhanced hand tracking using index finger tip
        if results.right_hand_landmarks or results.left_hand_landmarks:
            hand_landmarks = results.right_hand_landmarks or results.left_hand_landmarks
            detection_found = True

            try:
                # Use index finger tip for precise control
                index_tip = hand_landmarks.landmark[8]  # Index finger tip

                # Convert to screen coordinates
                raw_x = int(index_tip.x * self.screen_width)
                raw_y = int(index_tip.y * self.screen_height)

                # Apply Kalman filtering for smooth movement
                measurement = np.array([raw_x, raw_y], dtype=np.float32)
                filtered_pos = self.kalman_filter.update(measurement)

                cursor_pos = filtered_pos.astype(int)

                # Detect gestures
                gesture = self.gesture_recognizer.detect_gesture(hand_landmarks)

            except Exception as e:
                logging.error(f"Hand processing error: {e}")

        # Enhanced eye tracking (fallback)
        elif results.face_landmarks:
            detection_found = True
            try:
                # Use nose tip for more stable tracking
                nose_tip = results.face_landmarks.landmark[1]
                raw_x = int(nose_tip.x * self.screen_width)
                raw_y = int(nose_tip.y * self.screen_height)

                measurement = np.array([raw_x, raw_y], dtype=np.float32)
                filtered_pos = self.kalman_filter.update(measurement)
                cursor_pos = filtered_pos.astype(int)

            except Exception as e:
                logging.error(f"Eye processing error: {e}")

        self.cursor_position = cursor_pos
        return cursor_pos, detection_found, gesture

    def handle_gesture_click(self, gesture: str) -> bool:
        """Handle gesture-based clicking"""
        if not gesture:
            return False

        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            return False

        if gesture == "pinch":
            pyautogui.click()
            self.last_click_time = current_time
            logging.info("Gesture click: pinch")
            return True
        elif gesture == "fist":
            pyautogui.rightClick()
            self.last_click_time = current_time
            logging.info("Gesture click: right-click (fist)")
            return True

        return False

    def get_performance_stats(self) -> dict:
        """Get current performance statistics"""
        if not self.fps_history:
            return {"fps": 0, "latency": 0, "detection_rate": 0}

        avg_fps = float(np.mean(list(self.fps_history)))
        avg_latency = float(np.mean(list(self.latency_history)) * 1000)  # ms
        detection_rate = float(np.mean([1 if d else 0 for d in self.detection_history]) * 100)

        return {
            "fps": avg_fps,
            "latency_ms": avg_latency,
            "detection_rate": detection_rate
        }

    def draw_overlays(self, frame: np.ndarray, cursor_pos: np.ndarray,
                     detection_found: bool, gesture: Optional[str]):
        """Draw performance and control overlays"""
        try:
            # Performance stats
            stats = self.get_performance_stats()
            cv2.putText(frame, f"FPS: {stats['fps']:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Latency: {stats['latency_ms']:.1f}ms", (10, 55),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, f"Detection: {stats['detection_rate']:.1f}%", (10, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Detection status
            color = (0, 255, 0) if detection_found else (0, 0, 255)
            cv2.putText(frame, f"Detection: {'OK' if detection_found else 'NONE'}", (10, 105),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Gesture status
            if gesture:
                cv2.putText(frame, f"Gesture: {gesture.upper()}", (10, 130),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

            # Cursor position indicator
            screen_cursor_x = int(float(cursor_pos[0]) * frame.shape[1] / self.screen_width)
            screen_cursor_y = int(float(cursor_pos[1]) * frame.shape[0] / self.screen_height)
            cv2.circle(frame, (screen_cursor_x, screen_cursor_y), 8, (0, 255, 255), 2)
            cv2.circle(frame, (screen_cursor_x, screen_cursor_y), 3, (0, 255, 255), -1)

        except Exception as e:
            logging.error(f"Overlay drawing error: {e}")
