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

# Import cursor stabilizer
from cursor_stabilizer import CursorStabilizer

class GestureRecognizer:
    """Advanced gesture recognition for clicking"""
    def __init__(self):
        self.gesture_history = deque(maxlen=5)
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.3  # seconds

    def detect_gesture(self, hand_landmarks) -> Optional[str]:
        """Detect hand gestures with improved accuracy"""
        if not hand_landmarks:
            return None

        try:
            # Get all relevant landmark positions
            # Finger tips
            thumb_tip = hand_landmarks.landmark[4]
            index_tip = hand_landmarks.landmark[8]
            middle_tip = hand_landmarks.landmark[12]
            ring_tip = hand_landmarks.landmark[16]
            pinky_tip = hand_landmarks.landmark[20]

            # MCP joints (metacarpophalangeal)
            thumb_mcp = hand_landmarks.landmark[2]
            index_mcp = hand_landmarks.landmark[5]
            middle_mcp = hand_landmarks.landmark[9]
            ring_mcp = hand_landmarks.landmark[13]
            pinky_mcp = hand_landmarks.landmark[17]

            # PIP joints (proximal interphalangeal) for better finger state detection
            index_pip = hand_landmarks.landmark[6]
            middle_pip = hand_landmarks.landmark[10]
            ring_pip = hand_landmarks.landmark[14]
            pinky_pip = hand_landmarks.landmark[18]

            # Wrist
            wrist = hand_landmarks.landmark[0]

            # Calculate distances and relative positions
            thumb_index_dist = self._distance(thumb_tip, index_tip)
            thumb_wrist_dist = self._distance(thumb_tip, wrist)

            # Determine hand orientation (palm facing camera or away)
            # Check if fingers are generally pointing toward or away from camera
            palm_facing_camera = self._is_palm_facing_camera(hand_landmarks)

            # Analyze finger states using multiple joints for robustness
            finger_states = self._analyze_finger_states(
                [index_tip, middle_tip, ring_tip, pinky_tip],
                [index_mcp, middle_mcp, ring_mcp, pinky_mcp],
                [index_pip, middle_pip, ring_pip, pinky_pip],
                palm_facing_camera
            )

            index_extended = finger_states[0]
            middle_extended = finger_states[1]
            ring_extended = finger_states[2]
            pinky_extended = finger_states[3]

            # Thumb state analysis
            thumb_extended = self._is_thumb_extended(thumb_tip, thumb_mcp, wrist, palm_facing_camera)

            # Count extended and curled fingers (excluding thumb for now)
            extended_count = sum([index_extended, middle_extended, ring_extended, pinky_extended])
            curled_count = 4 - extended_count

            # ===== GESTURE DETECTION LOGIC =====

            # 1. PINCH GESTURE: Thumb and index finger tips are very close
            # AND index finger is extended, other fingers curled
            if (thumb_index_dist < 0.04 and  # Very close
                index_extended and  # Index finger extended
                curled_count >= 2 and  # At least 2 other fingers curled
                thumb_extended):  # Thumb is extended (not tucked)
                return "pinch"

            # 2. FINGER POINTING: Index finger extended, others curled, thumb tucked or semi-tucked
            if (index_extended and  # Index finger clearly extended
                curled_count >= 2 and  # At least 2 other fingers curled
                not thumb_extended and  # Thumb tucked (important distinction from pinch)
                middle_extended == False):  # Middle finger definitely curled
                return "finger"

            # 3. FIST: Most/all fingers curled, thumb tucked
            if (curled_count >= 3 and  # At least 3 fingers curled
                not thumb_extended):  # Thumb tucked
                return "fist"

            # 4. OPEN PALM: Most fingers extended
            if extended_count >= 3:
                return "open"

            # 5. PEACE SIGN: Index and middle extended, others curled
            if (index_extended and middle_extended and
                ring_extended == False and pinky_extended == False):
                return "peace"

        except Exception as e:
            logging.error(f"Gesture detection error: {e}")

        return None

    def _distance(self, point1, point2) -> float:
        """Calculate distance between two landmarks"""
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

    def _is_palm_facing_camera(self, hand_landmarks) -> bool:
        """Determine if palm is facing the camera"""
        try:
            # Check the relative positions of finger tips vs MCP joints
            # If fingertips are generally closer to camera than MCPs, palm is facing camera
            wrist = hand_landmarks.landmark[0]

            finger_tips_z = []
            finger_mcps_z = []

            # Sample a few fingers
            for tip_idx, mcp_idx in [(8, 5), (12, 9), (16, 13)]:  # Index, middle, ring
                if tip_idx < len(hand_landmarks.landmark) and mcp_idx < len(hand_landmarks.landmark):
                    finger_tips_z.append(hand_landmarks.landmark[tip_idx].z)
                    finger_mcps_z.append(hand_landmarks.landmark[mcp_idx].z)

            if finger_tips_z and finger_mcps_z:
                avg_tip_z = sum(finger_tips_z) / len(finger_tips_z)
                avg_mcp_z = sum(finger_mcps_z) / len(finger_mcps_z)

                # If fingertips are closer to camera (smaller z) than MCPs, palm is facing camera
                return avg_tip_z < avg_mcp_z

        except Exception as e:
            logging.error(f"Palm orientation detection error: {e}")

        return True  # Default assumption

    def _analyze_finger_states(self, finger_tips, finger_mcps, finger_pips, palm_facing_camera):
        """Analyze whether each finger is extended or curled"""
        finger_states = []

        for tip, mcp, pip in zip(finger_tips, finger_mcps, finger_pips):
            try:
                # Calculate distances between joints
                tip_to_pip_dist = self._distance(tip, pip)
                pip_to_mcp_dist = self._distance(pip, mcp)
                tip_to_mcp_dist = self._distance(tip, mcp)

                # A finger is extended if the tip is far from the MCP relative to the pip
                # This works regardless of hand orientation
                extension_ratio = tip_to_mcp_dist / (pip_to_mcp_dist + 0.001)  # Avoid division by zero

                # Also consider the angle between joints
                # Vector from MCP to PIP
                mcp_to_pip = (pip.x - mcp.x, pip.y - mcp.y)
                # Vector from PIP to tip
                pip_to_tip = (tip.x - pip.x, tip.y - pip.y)

                # Dot product to check if finger is relatively straight
                dot_product = mcp_to_pip[0] * pip_to_tip[0] + mcp_to_pip[1] * pip_to_tip[1]
                magnitude_mcp_pip = math.sqrt(mcp_to_pip[0]**2 + mcp_to_pip[1]**2)
                magnitude_pip_tip = math.sqrt(pip_to_tip[0]**2 + pip_to_tip[1]**2)

                if magnitude_mcp_pip > 0 and magnitude_pip_tip > 0:
                    cos_angle = dot_product / (magnitude_mcp_pip * magnitude_pip_tip)
                    cos_angle = max(-1, min(1, cos_angle))  # Clamp to valid range
                    angle = math.acos(cos_angle)
                else:
                    angle = 0

                # Finger is extended if:
                # 1. Extension ratio is high (tip far from MCP)
                # 2. Angle between joints is small (finger relatively straight)
                is_extended = (extension_ratio > 1.3 and angle < math.pi/3)  # About 60 degrees

                finger_states.append(is_extended)

            except Exception as e:
                logging.error(f"Finger state analysis error: {e}")
                finger_states.append(False)  # Default to curled on error

        return finger_states

    def _is_thumb_extended(self, thumb_tip, thumb_mcp, wrist, palm_facing_camera):
        """Analyze if thumb is extended"""
        try:
            # Thumb is extended if it's positioned away from the palm
            thumb_mcp_dist = self._distance(thumb_tip, thumb_mcp)
            thumb_wrist_dist = self._distance(thumb_tip, wrist)

            # Thumb extension ratio (how far thumb tip is from MCP relative to wrist)
            extension_ratio = thumb_mcp_dist / (thumb_wrist_dist + 0.001)

            # Also check if thumb is positioned laterally (away from other fingers)
            # This is a simplified check
            thumb_lateral_pos = abs(thumb_tip.x - wrist.x)

            # Thumb is extended if it's relatively far from MCP and positioned laterally
            return extension_ratio > 0.6 and thumb_lateral_pos > 0.1

        except Exception as e:
            logging.error(f"Thumb extension analysis error: {e}")
            return False

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

    def __init__(self, screen_width: int, screen_height: int, stabilizer_kwargs: dict = None):
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

        # Advanced filtering and smoothing (optimized for finger tracking)
        if stabilizer_kwargs:
            self.cursor_stabilizer = CursorStabilizer(**stabilizer_kwargs)
        else:
            self.cursor_stabilizer = CursorStabilizer(method='kalman', process_noise=0.003, measurement_noise=0.03)

        # Gesture recognition
        self.gesture_recognizer = GestureRecognizer()

        # Advanced tracking accuracy features
        self.landmark_history = deque(maxlen=10)  # Store recent landmarks for smoothing
        self.optical_flow = None  # For optical flow tracking
        self.roi_bounds = None  # Adaptive ROI tracking
        self.confidence_threshold = 0.6  # Minimum confidence for landmarks

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

    def set_stabilizer_method(self, method: str, **kwargs):
        """Set the stabilizer method with parameters"""
        try:
            stabilizer_kwargs = {'method': method}
            stabilizer_kwargs.update(kwargs)
            self.cursor_stabilizer = CursorStabilizer(**stabilizer_kwargs)
            logging.info(f"Cursor stabilizer method changed to: {method}")
        except Exception as e:
            logging.error(f"Failed to set stabilizer method: {e}")
            # Fallback to default
            self.cursor_stabilizer = CursorStabilizer(method='kalman', process_noise=0.003, measurement_noise=0.03)

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
        except Exception as e:
            logging.error(f"Error in process_frame_async: {e}")

        # Return None if no new result is available
        return None, False, None

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
        """Synchronous frame processing with advanced tracking accuracy"""
        # Flip and convert
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        original_frame = frame.copy()  # Keep original for optical flow

        # Initialize optical flow if needed
        self._initialize_optical_flow(original_frame)

        try:
            # Apply adaptive ROI if available
            if self.roi_bounds:
                x1, y1, x2, y2 = self.roi_bounds
                roi_frame = frame_rgb[y1:y2, x1:x2]
                # Note: This is simplified - in practice, you'd need to adjust landmark coordinates
                # For now, we'll process the full frame but track ROI bounds
            else:
                roi_frame = frame_rgb

            # Process with MediaPipe
            results = self.holistic.process(roi_frame)

            # Optional: Log detection for debugging (uncomment if needed)
            # has_right_hand = results.right_hand_landmarks is not None
            # has_left_hand = results.left_hand_landmarks is not None
            # if has_right_hand or has_left_hand:
            #     logging.debug(f"MediaPipe detected hands")
            # else:
            #     logging.debug("No hand landmarks detected")

        except Exception as e:
            logging.error(f"MediaPipe processing error: {e}")
            return self.cursor_position, False, None

        cursor_pos = self.cursor_position.copy()
        detection_found = False
        gesture = None

        # Process based on tracking type
        if self.multi_tracking:
            # Advanced multi-tracking mode with optical flow fallback
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

                    # Update adaptive ROI with combined position
                    self._update_adaptive_roi(cursor_pos, frame_rgb.shape)
            else:
                # Fallback to optical flow if no detection but we have previous tracking
                optical_flow_delta = self._track_optical_flow(original_frame)
                if optical_flow_delta is not None and detection_found:
                    # Apply optical flow correction (small adjustments only)
                    flow_scale = 0.1  # Scale down optical flow influence
                    flow_x = optical_flow_delta[0] * flow_scale * (self.screen_width / frame_rgb.shape[1])
                    flow_y = optical_flow_delta[1] * flow_scale * (self.screen_height / frame_rgb.shape[0])

                    cursor_pos[0] = max(0, min(self.screen_width, cursor_pos[0] + flow_x))
                    cursor_pos[1] = max(0, min(self.screen_height, cursor_pos[1] + flow_y))
                    detection_found = True  # Maintain detection if optical flow provides continuity
        else:
            # Single tracking mode
            cursor_pos, confidence = self._get_tracking_position(self.tracking_type, results)
            detection_found = confidence > 0.1  # Use a threshold for detection

        # Apply cursor stabilization for smooth movement if detection found
        if detection_found:
            try:
                measurement = np.array(cursor_pos, dtype=np.float32)
                filtered_pos = self.cursor_stabilizer.stabilize(measurement)
                cursor_pos = filtered_pos.astype(int)
            except Exception as e:
                logging.error(f"Cursor stabilization error: {e}")

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
                # Advanced finger tracking with sub-pixel interpolation and multi-frame smoothing
                hand_landmarks = getattr(results, 'right_hand_landmarks', None) or getattr(results, 'left_hand_landmarks', None)
                if hand_landmarks and hasattr(hand_landmarks, 'landmark') and len(hand_landmarks.landmark) > 8:
                    index_tip = hand_landmarks.landmark[8]

                    if hasattr(index_tip, 'x') and hasattr(index_tip, 'y'):
                        # Apply sub-pixel interpolation for higher precision
                        precise_x, precise_y = self._subpixel_interpolate_landmark(index_tip, frame_rgb.shape)

                        # Extract all hand landmarks for multi-frame smoothing and validation
                        current_landmarks = []
                        for lm in hand_landmarks.landmark:
                            current_landmarks.append([lm.x * self.screen_width, lm.y * self.screen_height])

                        # Apply multi-frame smoothing
                        smoothed_landmarks = self._smooth_landmarks_multiframe(current_landmarks)

                        # Validate hand skeleton constraints
                        if self._validate_hand_skeleton(smoothed_landmarks):
                            # Use smoothed index finger tip position
                            if len(smoothed_landmarks) > 8:
                                x, y = smoothed_landmarks[8]  # Index finger tip

                                # Apply confidence-based filtering (placeholder - MediaPipe doesn't provide per-landmark confidence)
                                filtered_x = max(0, min(self.screen_width, int(x)))
                                filtered_y = max(0, min(self.screen_height, int(y)))

                                # Update adaptive ROI based on hand position
                                self._update_adaptive_roi(np.array([filtered_x, filtered_y]), frame_rgb.shape)

                                # Higher sensitivity for finger tracking since it's more precise
                                finger_sensitivity = min(1.0, self.tracking_sensitivity * 1.2)
                                return np.array([filtered_x, filtered_y]), finger_sensitivity

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

    def _subpixel_interpolate_landmark(self, landmark, image_shape):
        """Implement sub-pixel interpolation for landmark detection"""
        try:
            # Get integer pixel coordinates
            x_pixel = int(landmark.x * image_shape[1])
            y_pixel = int(landmark.y * image_shape[0])

            # For sub-pixel precision, use bilinear interpolation
            # This assumes we have access to the original image data
            # For now, we'll use a simple approach with floating point precision

            # Clamp coordinates to image bounds
            x_pixel = max(0, min(image_shape[1] - 1, x_pixel))
            y_pixel = max(0, min(image_shape[0] - 1, y_pixel))

            # Return precise floating-point coordinates
            precise_x = landmark.x * self.screen_width
            precise_y = landmark.y * self.screen_height

            return precise_x, precise_y

        except Exception as e:
            logging.error(f"Sub-pixel interpolation error: {e}")
            return landmark.x * self.screen_width, landmark.y * self.screen_height

    def _smooth_landmarks_multiframe(self, current_landmarks):
        """Apply multi-frame landmark smoothing with weighted averaging"""
        if not current_landmarks:
            return current_landmarks

        try:
            # Add current landmarks to history
            self.landmark_history.append(current_landmarks)

            if len(self.landmark_history) < 3:
                return current_landmarks  # Need at least 3 frames for meaningful smoothing

            # Weighted average with exponential decay (more recent frames have higher weight)
            smoothed_landmarks = []
            weights = []
            total_weight = 0

            for i, frame_landmarks in enumerate(reversed(self.landmark_history)):
                weight = 1.0 / (i + 1)  # Exponential decay: 1, 0.5, 0.33, etc.
                weights.append(weight)
                total_weight += weight

                if i == 0:  # Initialize with first frame
                    smoothed_landmarks = [list(lm) for lm in frame_landmarks]
                else:
                    # Weighted average
                    for j, (x, y) in enumerate(frame_landmarks):
                        if j < len(smoothed_landmarks):
                            smoothed_landmarks[j][0] = (smoothed_landmarks[j][0] * (total_weight - weight) + x * weight) / total_weight
                            smoothed_landmarks[j][1] = (smoothed_landmarks[j][1] * (total_weight - weight) + y * weight) / total_weight

            return smoothed_landmarks

        except Exception as e:
            logging.error(f"Multi-frame smoothing error: {e}")
            return current_landmarks

    def _validate_hand_skeleton(self, hand_landmarks):
        """Validate hand skeleton constraints for anatomical plausibility"""
        if not hand_landmarks or len(hand_landmarks) < 21:
            return False

        try:
            # Basic anatomical constraints for hand
            # 1. Finger tips should generally be above MCP joints (when hand is upright)
            finger_constraints = [
                (8, 5),   # Index tip > Index MCP
                (12, 9),  # Middle tip > Middle MCP
                (16, 13), # Ring tip > Ring MCP
                (20, 17), # Pinky tip > Pinky MCP
            ]

            valid_constraints = 0
            for tip_idx, mcp_idx in finger_constraints:
                if (hand_landmarks[tip_idx][1] < hand_landmarks[mcp_idx][1] or  # Tip above MCP (y decreases upward)
                    abs(hand_landmarks[tip_idx][1] - hand_landmarks[mcp_idx][1]) < 0.05):  # Or very close
                    valid_constraints += 1

            # 2. Thumb should be positioned reasonably relative to index finger
            thumb_tip = hand_landmarks[4]
            index_base = hand_landmarks[5]
            thumb_index_dist = math.sqrt((thumb_tip[0] - index_base[0])**2 + (thumb_tip[1] - index_base[1])**2)

            # 3. Wrist should be below all finger bases
            wrist = hand_landmarks[0]
            finger_bases = [hand_landmarks[i] for i in [5, 9, 13, 17]]
            wrist_below_bases = sum(1 for base in finger_bases if wrist[1] > base[1]) >= 3

            # Overall validation: at least 3 finger constraints valid, reasonable thumb position, wrist positioning
            return (valid_constraints >= 3 and
                   0.05 < thumb_index_dist < 0.3 and
                   wrist_below_bases)

        except Exception as e:
            logging.error(f"Skeleton validation error: {e}")
            return False

    def _filter_landmarks_by_confidence(self, hand_landmarks, confidences=None):
        """Filter landmarks based on confidence scores"""
        if not hand_landmarks:
            return hand_landmarks

        try:
            filtered_landmarks = []

            for i, landmark in enumerate(hand_landmarks):
                # If we have confidence data, use it
                if confidences and i < len(confidences):
                    confidence = confidences[i]
                else:
                    # Estimate confidence based on landmark stability (placeholder)
                    confidence = self.confidence_threshold

                if confidence >= self.confidence_threshold:
                    filtered_landmarks.append(landmark)

            return filtered_landmarks

        except Exception as e:
            logging.error(f"Confidence filtering error: {e}")
            return hand_landmarks

    def _update_adaptive_roi(self, hand_position, image_shape):
        """Update adaptive ROI based on current hand position"""
        if hand_position is None:
            return

        try:
            roi_margin = 0.3  # 30% margin around detected hand
            roi_width = int(image_shape[1] * roi_margin)
            roi_height = int(image_shape[0] * roi_margin)

            # Convert hand position to image coordinates
            hand_x_img = int(hand_position[0] * image_shape[1] / self.screen_width)
            hand_y_img = int(hand_position[1] * image_shape[0] / self.screen_height)

            # Create ROI bounds
            x1 = max(0, hand_x_img - roi_width // 2)
            y1 = max(0, hand_y_img - roi_height // 2)
            x2 = min(image_shape[1], hand_x_img + roi_width // 2)
            y2 = min(image_shape[0], hand_y_img + roi_height // 2)

            self.roi_bounds = (x1, y1, x2, y2)

        except Exception as e:
            logging.error(f"Adaptive ROI update error: {e}")
            self.roi_bounds = None

    def _initialize_optical_flow(self, frame):
        """Initialize optical flow tracker"""
        try:
            if self.optical_flow is None:
                # Initialize Lucas-Kanade optical flow
                self.optical_flow = cv2.createOptFlow_DualTVL1()
                self.prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                self.optical_flow_points = None
        except Exception as e:
            logging.error(f"Optical flow initialization error: {e}")

    def _track_optical_flow(self, frame):
        """Track using optical flow"""
        if self.optical_flow is None or self.optical_flow_points is None:
            return None

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Calculate optical flow
            flow = self.optical_flow.calc(self.prev_frame, gray, None)

            # Update previous frame
            self.prev_frame = gray

            # Calculate average flow vector
            if flow is not None and flow.size > 0:
                mean_flow = np.mean(flow, axis=(0, 1))
                return mean_flow

        except Exception as e:
            logging.error(f"Optical flow tracking error: {e}")

        return None

    def handle_gesture_click(self, gesture: str) -> bool:
        """Handle gesture-based clicking"""
        try:
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
            elif gesture == "finger":
                pyautogui.click()
                self.last_click_time = current_time
                logging.info("Gesture click: finger")
                return True

        except Exception as e:
            logging.error(f"Error in handle_gesture_click: {e}")

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
