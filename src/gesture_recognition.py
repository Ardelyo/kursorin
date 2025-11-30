"""
Gesture Recognition Module
Advanced hand gesture detection and classification
"""

import math
import time
import logging
from collections import deque
from typing import Optional, List


class GestureRecognizer:
    """Advanced gesture recognition for clicking and control"""

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
            if (thumb_index_dist < 0.06 and  # Relaxed threshold (was 0.04)
                index_extended and  # Index finger extended
                curled_count >= 2 and  # At least 2 other fingers curled
                thumb_extended):  # Thumb is extended (not tucked)
                return "pinch"

            # 2. FINGER POINTING: Index finger extended, others curled, thumb tucked
            if (index_extended and  # Index finger clearly extended
                curled_count >= 2 and  # At least 2 other fingers curled
                not thumb_extended and  # Thumb tucked (important distinction from pinch)
                middle_extended == False):  # Middle finger definitely curled
                return "finger"

            # 3. REDESIGNED FIST AS PINCH: Most/all fingers curled, thumb tucked - now triggers pinch action
            if (curled_count >= 3 and  # At least 3 fingers curled
                not thumb_extended):  # Thumb tucked
                return "pinch"

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
                extension_ratio = tip_to_mcp_dist / (pip_to_mcp_dist + 0.001)  # Avoid division by zero

                # Also consider the angle between joints
                mcp_to_pip = (pip.x - mcp.x, pip.y - mcp.y)
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
