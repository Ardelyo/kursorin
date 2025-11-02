"""
Main Application Module
Orchestrates all modules for the Smart Cursor Control system
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import threading
import logging
import sys
from typing import Optional, Tuple

# Import our modular components
import settings_manager
import gui_components
import cursor_control
import gesture_recognition
import tracking_engines
import performance_optimizer
import virtual_keyboard
import text_display


class SmartCursorApplication:
    """Main application class that coordinates all modules"""

    def __init__(self):
        # Initialize settings first
        self.settings_manager = settings_manager.SettingsManager()

        # Get screen dimensions
        self.screen_width, self.screen_height = self._get_screen_dimensions()

        # Initialize components
        self.performance_optimizer = performance_optimizer.PerformanceOptimizer()
        self.tracking_manager = tracking_engines.TrackingEngineManager(self.screen_width, self.screen_height)
        self.cursor_controller = cursor_control.CursorController(self.screen_width, self.screen_height)
        self.gesture_recognizer = gesture_recognition.GestureRecognizer()
        self.virtual_keyboard = virtual_keyboard.VirtualKeyboardDisplay(self.screen_width, self.screen_height)
        self.text_display = text_display.TextDisplay(self.screen_width, self.screen_height)

        # Initialize MediaPipe
        self.mp_holistic = mp.solutions.holistic
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils

        # MediaPipe instances (initialized when needed)
        self.holistic = None
        self.hands = None

        # Application state
        self.running = False
        self.current_mode = "normal"
        self.gui = None

        # Typing mode state
        self.typing_mode_active = False

        # Performance tracking
        self.fps_history = []
        self.frame_count = 0
        self.start_time = time.time()

        # Threading
        self.lock = threading.Lock()
        self.processing_thread = None

    def _get_screen_dimensions(self):
        """Get screen dimensions safely"""
        try:
            import pyautogui
            return pyautogui.size()
        except Exception as e:
            logging.warning(f"Could not get screen size: {e}, using defaults")
            return 1920, 1080

    def initialize_components(self):
        """Initialize MediaPipe components with optimized settings"""
        try:
            # Get optimized settings from performance optimizer
            holistic_settings = self.performance_optimizer.optimize_mediapipe_settings(0.5)

            self.holistic = self.mp_holistic.Holistic(
                min_detection_confidence=holistic_settings['min_detection_confidence'],
                min_tracking_confidence=holistic_settings['min_tracking_confidence'],
                model_complexity=holistic_settings['model_complexity']
            )

            self.hands = self.mp_hands.Hands(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
                max_num_hands=2
            )

            logging.info("MediaPipe components initialized successfully")

        except Exception as e:
            logging.error(f"Failed to initialize MediaPipe: {e}")
            raise

    def create_gui(self):
        """Create and configure the GUI"""
        def on_mode_change(mode):
            self.set_mode(mode)

        def on_setting_change(setting, value):
            self.settings_manager.set(setting, value)
            self._apply_setting_change(setting, value)

        self.gui = gui_components.ControlPanel(
            self.settings_manager,
            on_mode_change=on_mode_change,
            on_setting_change=on_setting_change
        )

        return self.gui.create_control_panel()

    def set_mode(self, mode: str):
        """Set the application mode"""
        self.current_mode = mode
        self.typing_mode_active = (mode == "typing")

        # Configure tracking based on mode
        if mode == "normal":
            self.tracking_manager.set_tracking_type(tracking_engines.TrackingType.FINGER)
            self.tracking_manager.set_multi_tracking(False)
        elif mode == "eye_tracking":
            self.tracking_manager.set_tracking_type(tracking_engines.TrackingType.EYE)
        elif mode == "gaming":
            self.tracking_manager.set_tracking_type(tracking_engines.TrackingType.FINGER)
            self.tracking_manager.set_sensitivity(0.95)
            self.cursor_controller.set_smoothing_factor(0.3)  # Less smoothing for faster response
        elif mode == "typing":
            self.tracking_manager.set_tracking_type(tracking_engines.TrackingType.FINGER)
            self.tracking_manager.set_sensitivity(0.8)
            self.cursor_controller.set_smoothing_factor(0.7)
            # Initialize typing mode
            self.text_display.clear_text()

        logging.info(f"Mode changed to: {mode}")

    def _apply_setting_change(self, setting: str, value):
        """Apply setting changes to relevant components"""
        if setting == "dwell_time":
            self.cursor_controller.set_dwell_time(value)
        elif setting == "tracking_sensitivity":
            self.tracking_manager.set_sensitivity(value)
        elif setting == "stabilizer_alpha":
            self.cursor_controller.set_smoothing_factor(value)

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, bool, Optional[str]]:
        """Process a single frame through the entire pipeline"""
        if not self.performance_optimizer.should_process_frame(frame):
            return frame, False, None

        try:
            # Apply distance scaling if needed
            processed_frame, scale = self.performance_optimizer.apply_distance_scaling(frame)

            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)

            # Process with MediaPipe
            holistic_results = self.holistic.process(rgb_frame)
            hand_results = self.hands.process(rgb_frame)

            # Get cursor position from tracking
            cursor_x, cursor_y, detection_found = self.tracking_manager.process_frame(
                holistic_results, hand_results
            )

            # Handle typing mode interactions
            typed_character = ""
            if self.typing_mode_active and hand_results and hand_results.multi_hand_landmarks:
                # Get finger positions for keyboard interaction
                finger_positions = []
                for hand_landmarks in hand_results.multi_hand_landmarks:
                    # Use index finger tip
                    index_tip = hand_landmarks.landmark[8]
                    finger_x = int(index_tip.x * self.screen_width)
                    finger_y = int(index_tip.y * self.screen_height)
                    finger_positions.append((finger_x, finger_y))

                # Update virtual keyboard with finger positions
                self.virtual_keyboard.update_finger_position(finger_positions)

                # Check for key presses (dwell clicking on keyboard)
                if detection_found and self.virtual_keyboard.is_position_on_keyboard((cursor_x, cursor_y)):
                    # Use dwell time for keyboard presses
                    pressed = self.cursor_controller.handle_dwell_clicking(cursor_x, cursor_y, detection_found)
                    if pressed:
                        typed_character = self.virtual_keyboard.press_key_at_position((cursor_x, cursor_y))
                        if typed_character:
                            self._handle_keyboard_input(typed_character)

            # Handle cursor control
            gesture = None
            if not self.typing_mode_active and hand_results and hand_results.multi_hand_landmarks:
                # Detect gestures
                hand_landmarks = hand_results.multi_hand_landmarks[0]
                gesture = self.gesture_recognizer.detect_gesture(hand_landmarks)

                # Handle gesture-based actions
                if gesture and self.gesture_recognizer.should_trigger_action(gesture):
                    self._handle_gesture_action(gesture)

            # Move cursor or handle dwell clicking (non-typing mode)
            if not self.typing_mode_active:
                clicked = self.cursor_controller.handle_dwell_clicking(
                    cursor_x, cursor_y, detection_found
                )

            # Update display
            display_frame = self._update_display(
                processed_frame, (cursor_x, cursor_y), detection_found, gesture
            )

            return display_frame, detection_found, gesture

        except Exception as e:
            logging.error(f"Frame processing error: {e}")
            return frame, False, None

    def _handle_keyboard_input(self, character: str):
        """Handle keyboard input in typing mode"""
        self.text_display.add_text(character)

    def _handle_gesture_action(self, gesture: str):
        """Handle gesture-based actions"""
        if gesture == "pinch":
            self.cursor_controller.perform_click()  # Now includes redesigned fist gesture
        elif gesture == "peace":
            self.cursor_controller.perform_double_click()
        elif gesture == "open":
            # Could implement drag or other actions
            pass

    def _update_display(self, frame: np.ndarray, cursor_pos: Tuple[int, int],
                        detection_found: bool, gesture: Optional[str]) -> np.ndarray:
        """Update the display frame with overlays"""
        display_frame = frame.copy()

        # Draw virtual keyboard and text display in typing mode
        if self.typing_mode_active:
            display_frame = self.virtual_keyboard.draw_keyboard(display_frame)
            display_frame = self.text_display.draw_text_display(display_frame)

        # Draw landmarks
        if hasattr(self, 'holistic') and self.holistic:
            self.mp_drawing.draw_landmarks(
                display_frame, self.holistic_results.face_landmarks,
                self.mp_holistic.FACEMESH_CONTOURS
            )

        if hasattr(self, 'hand_results') and self.hand_results:
            for hand_landmarks in self.hand_results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    display_frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )

        # Draw cursor position indicator
        if detection_found:
            cv2.circle(display_frame, cursor_pos, 10, (0, 255, 0), 2)

        # Draw gesture indicator
        if gesture:
            cv2.putText(display_frame, f"Gesture: {gesture}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # Draw mode and performance info
        cv2.putText(display_frame, f"Mode: {self.current_mode}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        fps = self._calculate_fps()
        cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return display_frame

    def _calculate_fps(self) -> float:
        """Calculate current FPS"""
        current_time = time.time()
        self.fps_history.append(current_time)

        # Keep only last 30 frames for FPS calculation
        while len(self.fps_history) > 30:
            self.fps_history.pop(0)

        if len(self.fps_history) > 1:
            return len(self.fps_history) / (self.fps_history[-1] - self.fps_history[0])
        return 0.0

    def main_loop(self):
        """Main processing loop"""
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            logging.error("Could not open camera")
            return

        logging.info("Starting main processing loop")

        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    logging.warning("Failed to read frame from camera")
                    continue

                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)

                # Process frame
                display_frame, detection_found, gesture = self.process_frame(frame)

                # Update GUI status
                if self.gui:
                    status_updates = {
                        "Detection": "Found" if detection_found else "Searching",
                        "FPS": f"{self._calculate_fps():.1f}",
                        "Mouse": "Enabled" if self.cursor_controller.mouse_enabled else "Disabled"
                    }
                    self.gui.update_status_display(status_updates)

                # Show frame
                cv2.imshow('Smart Cursor Control', display_frame)

                # Check for quit key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except KeyboardInterrupt:
            logging.info("Interrupted by user")
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.cleanup()

    def start(self):
        """Start the application"""
        try:
            logging.info("Starting Smart Cursor Control application...")

            # Initialize components
            self.initialize_components()

            # Create GUI
            gui_window = self.create_gui()

            # Set running flag
            self.running = True

            # Start main loop in separate thread
            self.processing_thread = threading.Thread(target=self.main_loop, daemon=True)
            self.processing_thread.start()

            # Start GUI main loop (blocking)
            self.gui.run()

        except Exception as e:
            logging.error(f"Failed to start application: {e}")
            self.cleanup()
            sys.exit(1)

    def stop(self):
        """Stop the application"""
        logging.info("Stopping Smart Cursor Control application...")
        self.running = False

        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)

        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.holistic:
                self.holistic.close()
            if self.hands:
                self.hands.close()

            cv2.destroyAllWindows()
            logging.info("Cleanup completed")

        except Exception as e:
            logging.error(f"Error during cleanup: {e}")


def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('smart_cursor.log'),
            logging.StreamHandler()
        ]
    )

    app = SmartCursorApplication()
    app.start()


if __name__ == "__main__":
    main()
