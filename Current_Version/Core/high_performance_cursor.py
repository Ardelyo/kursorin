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

        # Tracking settings
        self.tracking_type = 'hand'  # Default tracking type
        self.tracking_sensitivity = 0.8
        self.multi_tracking = False

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

    def set_tracking_type(self, tracking_type: str):
        """Set the tracking type with validation"""
        valid_types = ['hand', 'head', 'eye', 'pose', 'finger', 'body']
        if tracking_type not in valid_types:
            logging.warning(f"Invalid tracking type '{tracking_type}', using default 'hand'")
            self.tracking_type = 'hand'
        else:
            self.tracking_type = tracking_type
        logging.info(f"High-performance cursor tracking type set to: {self.tracking_type}")

    def set_tracking_sensitivity(self, sensitivity: float):
        """Set tracking sensitivity with validation"""
        try:
            self.tracking_sensitivity = max(0.1, min(1.0, float(sensitivity)))
        except (ValueError, TypeError):
            logging.warning(f"Invalid sensitivity value '{sensitivity}', using default 0.8")
            self.tracking_sensitivity = 0.8

    def set_multi_tracking(self, enabled: bool):
        """Enable or disable multi-tracking with validation"""
        try:
            self.multi_tracking = bool(enabled)
            logging.info(f"Multi-tracking {'enabled' if self.multi_tracking else 'disabled'}")
        except (ValueError, TypeError):
            logging.warning(f"Invalid multi-tracking value '{enabled}', using default False")
            self.multi_tracking = False

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
        """Main processing loop in separate thread with enhanced error handling"""
        consecutive_errors = 0
        max_consecutive_errors = 5

        while self.running:
            try:
                # Get frame from queue with timeout
                try:
                    frame = self.frame_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Validate frame
                if frame is None or frame.size == 0:
                    logging.warning("Received invalid frame, skipping")
                    continue

                start_time = time.time()

                # Process frame with error handling
                try:
                    cursor_pos, detection_found, gesture = self._process_frame_sync(frame)
                    consecutive_errors = 0  # Reset error counter on success
                except Exception as e:
                    consecutive_errors += 1
                    logging.error(f"Frame processing error ({consecutive_errors}/{max_consecutive_errors}): {e}")

                    if consecutive_errors >= max_consecutive_errors:
                        logging.error("Too many consecutive processing errors, resetting state")
                        self.cursor_position = np.array([self.screen_width // 2, self.screen_height // 2])
                        consecutive_errors = 0

                    time.sleep(0.01)
                    continue

                # Put result in queue with error handling
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

                # Track performance with bounds checking
                processing_time = time.time() - start_time
                if processing_time > 0:
                    fps = min(60.0, 1.0 / processing_time)  # Cap FPS at 60
                    self.fps_history.append(fps)
                    self.latency_history.append(min(1.0, processing_time))  # Cap latency at 1 second
                else:
                    self.fps_history.append(60.0)
                    self.latency_history.append(0.001)

                self.detection_history.append(detection_found)

            except Exception as e:
                logging.error(f"Critical processing loop error: {e}")
                time.sleep(0.1)  # Longer pause on critical errors

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

        # Process based on tracking type
        if self.multi_tracking:
            # Multi-tracking mode: combine multiple tracking types
            positions = []
            confidences = []

            # Try all available tracking methods
            tracking_methods = ['hand', 'finger', 'head', 'eye', 'pose', 'body']
            for method in tracking_methods:
                pos, conf = self._get_tracking_position(method, results)
                if conf > 0:
                    positions.append(pos)
                    confidences.append(conf)

            if positions:
                detection_found = True
                # Weighted average based on confidence
                total_conf = sum(confidences)
                if total_conf > 0:
                    weighted_pos = np.zeros(2)
                    for pos, conf in zip(positions, confidences):
                        weighted_pos += pos * (conf / total_conf)
                    cursor_pos = weighted_pos.astype(int)
        else:
            # Single tracking mode
            cursor_pos, detection_found = self._get_tracking_position(self.tracking_type, results)

        # Apply Kalman filtering for smooth movement if detection found
        if detection_found:
            try:
                measurement = np.array(cursor_pos, dtype=np.float32)
                filtered_pos = self.kalman_filter.update(measurement)
                cursor_pos = filtered_pos.astype(int)
            except Exception as e:
                logging.error(f"Kalman filter error: {e}")

        # Detect gestures if hand tracking is active
        if (results.right_hand_landmarks or results.left_hand_landmarks) and \
           (self.tracking_type in ['hand', 'finger'] or self.multi_tracking):
            hand_landmarks = results.right_hand_landmarks or results.left_hand_landmarks
            gesture = self.gesture_recognizer.detect_gesture(hand_landmarks)

        self.cursor_position = cursor_pos
        return cursor_pos, detection_found, gesture

    def _get_tracking_position(self, tracking_type: str, results) -> Tuple[np.ndarray, float]:
        """Get cursor position for specific tracking type with error handling"""
        try:
            # Validate input parameters
            if results is None:
                return self.cursor_position, 0.0

            if tracking_type == 'hand':
                # Hand tracking using wrist
                hand_landmarks = getattr(results, 'right_hand_landmarks', None) or getattr(results, 'left_hand_landmarks', None)
                if hand_landmarks and hasattr(hand_landmarks, 'landmark') and len(hand_landmarks.landmark) > 0:
                    wrist = hand_landmarks.landmark[0]
                    if hasattr(wrist, 'x') and hasattr(wrist, 'y'):
                        x = max(0, min(self.screen_width, int(wrist.x * self.screen_width)))
                        y = max(0, min(self.screen_height, int(wrist.y * self.screen_height)))
                        return np.array([x, y]), self.tracking_sensitivity

            elif tracking_type == 'finger':
                # Finger tracking using index finger tip
                hand_landmarks = getattr(results, 'right_hand_landmarks', None) or getattr(results, 'left_hand_landmarks', None)
                if hand_landmarks and hasattr(hand_landmarks, 'landmark') and len(hand_landmarks.landmark) > 8:
                    index_tip = hand_landmarks.landmark[8]
                    if hasattr(index_tip, 'x') and hasattr(index_tip, 'y'):
                        x = max(0, min(self.screen_width, int(index_tip.x * self.screen_width)))
                        y = max(0, min(self.screen_height, int(index_tip.y * self.screen_height)))
                        return np.array([x, y]), self.tracking_sensitivity

            elif tracking_type == 'head':
                # Head tracking using nose tip
                if hasattr(results, 'face_landmarks') and results.face_landmarks:
                    face_lm = results.face_landmarks
                    if hasattr(face_lm, 'landmark') and len(face_lm.landmark) > 1:
                        nose_tip = face_lm.landmark[1]
                        if hasattr(nose_tip, 'x') and hasattr(nose_tip, 'y'):
                            x = max(0, min(self.screen_width, int(nose_tip.x * self.screen_width)))
                            y = max(0, min(self.screen_height, int(nose_tip.y * self.screen_height)))
                            return np.array([x, y]), self.tracking_sensitivity

            elif tracking_type == 'eye':
                # Eye tracking using average eye position
                if hasattr(results, 'face_landmarks') and results.face_landmarks:
                    face_lm = results.face_landmarks
                    if hasattr(face_lm, 'landmark') and len(face_lm.landmark) > 362:
                        left_eye = face_lm.landmark[33]
                        right_eye = face_lm.landmark[362]
                        if (hasattr(left_eye, 'x') and hasattr(left_eye, 'y') and
                            hasattr(right_eye, 'x') and hasattr(right_eye, 'y')):
                            eye_x = (left_eye.x + right_eye.x) / 2
                            eye_y = (left_eye.y + right_eye.y) / 2
                            x = max(0, min(self.screen_width, int(eye_x * self.screen_width)))
                            y = max(0, min(self.screen_height, int(eye_y * self.screen_height)))
                            return np.array([x, y]), self.tracking_sensitivity

            elif tracking_type == 'pose' or tracking_type == 'body':
                # Body/pose tracking using shoulders center
                if hasattr(results, 'pose_landmarks') and results.pose_landmarks:
                    pose_lm = results.pose_landmarks
                    if hasattr(pose_lm, 'landmark') and len(pose_lm.landmark) > 12:
                        left_shoulder = pose_lm.landmark[11]
                        right_shoulder = pose_lm.landmark[12]
                        if (hasattr(left_shoulder, 'x') and hasattr(left_shoulder, 'y') and
                            hasattr(right_shoulder, 'x') and hasattr(right_shoulder, 'y')):
                            shoulder_x = (left_shoulder.x + right_shoulder.x) / 2
                            shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
                            x = max(0, min(self.screen_width, int(shoulder_x * self.screen_width)))
                            y = max(0, min(self.screen_height, int(shoulder_y * self.screen_height)))
                            return np.array([x, y]), self.tracking_sensitivity

        except (AttributeError, IndexError, TypeError, ValueError) as e:
            logging.debug(f"Tracking error for {tracking_type}: {e}")
        except Exception as e:
            logging.error(f"Unexpected tracking error for {tracking_type}: {e}")

        return self.cursor_position, 0.0  # No detection

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

            # Tracking type and sensitivity
            tracking_info = f"Tracking: {self.tracking_type.upper()}"
            if self.multi_tracking:
                tracking_info += " (MULTI)"
            cv2.putText(frame, tracking_info, (10, 155),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            cv2.putText(frame, f"Sensitivity: {self.tracking_sensitivity:.1f}", (10, 180),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # Cursor position indicator
            screen_cursor_x = int(float(cursor_pos[0]) * frame.shape[1] / self.screen_width)
            screen_cursor_y = int(float(cursor_pos[1]) * frame.shape[0] / self.screen_height)
            cv2.circle(frame, (screen_cursor_x, screen_cursor_y), 8, (0, 255, 255), 2)
            cv2.circle(frame, (screen_cursor_x, screen_cursor_y), 3, (0, 255, 255), -1)

        except Exception as e:
            logging.error(f"Overlay drawing error: {e}")
