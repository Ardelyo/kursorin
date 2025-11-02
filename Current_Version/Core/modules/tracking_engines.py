"""
Tracking Engines Module
Various tracking implementations for cursor control
"""

import cv2
import mediapipe as mp
import numpy as np
import logging
from typing import Tuple, Optional, Any
from enum import Enum


class TrackingType(Enum):
    FINGER = "finger"
    HAND = "hand"
    HEAD = "head"
    EYE = "eye"
    POSE = "pose"
    BODY = "body"


class TrackingEngine:
    """Base class for tracking engines"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.sensitivity = 0.8

    def process_frame(self, results: Any) -> Tuple[int, int, bool]:
        """Process tracking results and return cursor position"""
        raise NotImplementedError

    def set_sensitivity(self, sensitivity: float):
        """Set tracking sensitivity"""
        self.sensitivity = max(0.1, min(sensitivity, 1.0))


class FingerTrackingEngine(TrackingEngine):
    """Advanced finger tip tracking with precision"""

    def __init__(self, screen_width: int, screen_height: int):
        super().__init__(screen_width, screen_height)
        self.finger_history = []
        self.history_size = 5

    def process_frame(self, results: Any) -> Tuple[int, int, bool]:
        """Process finger tracking from MediaPipe results"""
        if not results or not results.multi_hand_landmarks:
            return self.screen_width // 2, self.screen_height // 2, False

        try:
            # Get the most prominent hand (usually the first one)
            hand_landmarks = results.multi_hand_landmarks[0]

            # Use index finger tip (landmark 8) for precise tracking
            index_tip = hand_landmarks.landmark[8]

            # Apply sensitivity scaling
            cursor_x = int(index_tip.x * self.screen_width * self.sensitivity +
                          (self.screen_width // 2) * (1 - self.sensitivity))
            cursor_y = int(index_tip.y * self.screen_height * self.sensitivity +
                          (self.screen_height // 2) * (1 - self.sensitivity))

            # Add to history for smoothing
            self.finger_history.append((cursor_x, cursor_y))
            if len(self.finger_history) > self.history_size:
                self.finger_history.pop(0)

            # Return averaged position
            if len(self.finger_history) >= 3:
                avg_x = sum(x for x, y in self.finger_history) // len(self.finger_history)
                avg_y = sum(y for x, y in self.finger_history) // len(self.finger_history)
                return avg_x, avg_y, True

            return cursor_x, cursor_y, True

        except Exception as e:
            logging.error(f"Finger tracking error: {e}")
            return self.screen_width // 2, self.screen_height // 2, False


class HandTrackingEngine(TrackingEngine):
    """Hand/wrist tracking for general movement"""

    def process_frame(self, results: Any) -> Tuple[int, int, bool]:
        """Process hand tracking from MediaPipe results"""
        if not results or not results.multi_hand_landmarks:
            return self.screen_width // 2, self.screen_height // 2, False

        try:
            # Use wrist position (landmark 0) for hand tracking
            hand_landmarks = results.multi_hand_landmarks[0]
            wrist = hand_landmarks.landmark[0]

            cursor_x = int(wrist.x * self.screen_width)
            cursor_y = int(wrist.y * self.screen_height)

            return cursor_x, cursor_y, True

        except Exception as e:
            logging.error(f"Hand tracking error: {e}")
            return self.screen_width // 2, self.screen_height // 2, False


class HeadTrackingEngine(TrackingEngine):
    """Head/nose tracking for accessibility"""

    def process_frame(self, results: Any) -> Tuple[int, int, bool]:
        """Process head tracking from MediaPipe holistic results"""
        if not results or not results.face_landmarks:
            return self.screen_width // 2, self.screen_height // 2, False

        try:
            # Use nose tip (landmark 1) for head tracking
            nose = results.face_landmarks.landmark[1]

            cursor_x = int(nose.x * self.screen_width)
            cursor_y = int(nose.y * self.screen_height)

            return cursor_x, cursor_y, True

        except Exception as e:
            logging.error(f"Head tracking error: {e}")
            return self.screen_width // 2, self.screen_height // 2, False


class EyeTrackingEngine(TrackingEngine):
    """Eye gaze tracking"""

    def process_frame(self, results: Any) -> Tuple[int, int, bool]:
        """Process eye tracking from MediaPipe face results"""
        if not results or not results.face_landmarks:
            return self.screen_width // 2, self.screen_height // 2, False

        try:
            face_landmarks = results.face_landmarks

            # Get eye landmarks
            left_eye_center = face_landmarks.landmark[468]   # Left eye center
            right_eye_center = face_landmarks.landmark[473]  # Right eye center

            # Calculate average eye position
            eye_x = (left_eye_center.x + right_eye_center.x) / 2
            eye_y = (left_eye_center.y + right_eye_center.y) / 2

            cursor_x = int(self.screen_width // 2)  # Center X for eye tracking
            cursor_y = int(eye_y * self.screen_height)

            return cursor_x, cursor_y, True

        except Exception as e:
            logging.error(f"Eye tracking error: {e}")
            return self.screen_width // 2, self.screen_height // 2, False


class PoseTrackingEngine(TrackingEngine):
    """Body pose tracking"""

    def process_frame(self, results: Any) -> Tuple[int, int, bool]:
        """Process pose tracking from MediaPipe holistic results"""
        if not results or not results.pose_landmarks:
            return self.screen_width // 2, self.screen_height // 2, False

        try:
            # Use shoulder center for pose tracking
            left_shoulder = results.pose_landmarks.landmark[11]
            right_shoulder = results.pose_landmarks.landmark[12]

            shoulder_x = (left_shoulder.x + right_shoulder.x) / 2
            shoulder_y = (left_shoulder.y + right_shoulder.y) / 2

            cursor_x = int(shoulder_x * self.screen_width)
            cursor_y = int(shoulder_y * self.screen_height)

            return cursor_x, cursor_y, True

        except Exception as e:
            logging.error(f"Pose tracking error: {e}")
            return self.screen_width // 2, self.screen_height // 2, False


class TrackingEngineManager:
    """Manages multiple tracking engines"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Initialize all tracking engines
        self.engines = {
            TrackingType.FINGER: FingerTrackingEngine(screen_width, screen_height),
            TrackingType.HAND: HandTrackingEngine(screen_width, screen_height),
            TrackingType.HEAD: HeadTrackingEngine(screen_width, screen_height),
            TrackingType.EYE: EyeTrackingEngine(screen_width, screen_height),
            TrackingType.POSE: PoseTrackingEngine(screen_width, screen_height),
        }

        self.current_engine = TrackingType.FINGER
        self.multi_tracking = False
        self.multi_tracking_weights = {
            TrackingType.FINGER: 0.6,
            TrackingType.HAND: 0.4,
        }

    def set_tracking_type(self, tracking_type: TrackingType):
        """Set the primary tracking engine"""
        if tracking_type in self.engines:
            self.current_engine = tracking_type
            logging.info(f"Tracking type set to: {tracking_type.value}")

    def set_multi_tracking(self, enabled: bool, weights: Optional[dict] = None):
        """Enable/disable multi-tracking with custom weights"""
        self.multi_tracking = enabled
        if weights:
            self.multi_tracking_weights = weights
        logging.info(f"Multi-tracking {'enabled' if enabled else 'disabled'}")

    def set_sensitivity(self, sensitivity: float, engine_type: Optional[TrackingType] = None):
        """Set sensitivity for tracking engine(s)"""
        if engine_type:
            if engine_type in self.engines:
                self.engines[engine_type].set_sensitivity(sensitivity)
        else:
            # Set for all engines
            for engine in self.engines.values():
                engine.set_sensitivity(sensitivity)

    def process_frame(self, holistic_results: Any, hand_results: Any = None) -> Tuple[int, int, bool]:
        """Process frame with current tracking configuration"""
        if self.multi_tracking:
            return self._process_multi_tracking(holistic_results, hand_results)
        else:
            return self._process_single_tracking(holistic_results, hand_results)

    def _process_single_tracking(self, holistic_results: Any, hand_results: Any) -> Tuple[int, int, bool]:
        """Process with single tracking engine"""
        if self.current_engine == TrackingType.FINGER or self.current_engine == TrackingType.HAND:
            # Use hand results for finger/hand tracking
            return self.engines[self.current_engine].process_frame(hand_results)
        else:
            # Use holistic results for other tracking types
            return self.engines[self.current_engine].process_frame(holistic_results)

    def _process_multi_tracking(self, holistic_results: Any, hand_results: Any) -> Tuple[int, int, bool]:
        """Process with multiple tracking engines combined"""
        positions = []
        weights = []

        for engine_type, weight in self.multi_tracking_weights.items():
            if engine_type == TrackingType.FINGER or engine_type == TrackingType.HAND:
                x, y, found = self.engines[engine_type].process_frame(hand_results)
            else:
                x, y, found = self.engines[engine_type].process_frame(holistic_results)

            if found:
                positions.append((x, y))
                weights.append(weight)

        if not positions:
            return self.screen_width // 2, self.screen_height // 2, False

        # Weighted average of all valid positions
        total_weight = sum(weights)
        avg_x = sum(x * w for (x, y), w in zip(positions, weights)) / total_weight
        avg_y = sum(y * w for (x, y), w in zip(positions, weights)) / total_weight

        return int(avg_x), int(avg_y), True
