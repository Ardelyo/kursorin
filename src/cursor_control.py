"""
Cursor Control Module
Handles cursor movement, clicking, and stabilization
"""

import pyautogui
import time
import logging
import threading
from typing import Tuple, Optional
import numpy as np


class CursorController:
    """Controls cursor movement and clicking operations"""

    def __init__(self, screen_width: int, screen_height: int, stabilizer=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.stabilizer = stabilizer

        # Cursor control settings
        self.mouse_enabled = True
        self.last_mouse_move = time.time()
        self.mouse_timeout = 30  # seconds

        # Clicking state
        self.dwell_start_time = None
        self.dwell_threshold = 2.0  # seconds
        self.is_clicking = False

        # Movement smoothing
        self.prev_cursor_x = screen_width // 2
        self.prev_cursor_y = screen_height // 2
        self.smoothing_factor = 0.7

        # Thread safety
        self.lock = threading.Lock()

        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01  # Small pause between actions

    def move_cursor(self, target_x: float, target_y: float, smooth: bool = True):
        """Move cursor to target position with optional smoothing"""
        if not self.mouse_enabled:
            return

        with self.lock:
            try:
                # Apply smoothing if enabled
                if smooth and self.smoothing_factor > 0:
                    target_x = self.prev_cursor_x + (target_x - self.prev_cursor_x) * (1 - self.smoothing_factor)
                    target_y = self.prev_cursor_y + (target_y - self.prev_cursor_y) * (1 - self.smoothing_factor)

                # Ensure coordinates are within screen bounds
                target_x = max(0, min(target_x, self.screen_width - 1))
                target_y = max(0, min(target_y, self.screen_height - 1))

                # Apply stabilizer if available
                if self.stabilizer:
                    stabilized_x, stabilized_y = self.stabilizer.stabilize(target_x, target_y)
                else:
                    stabilized_x, stabilized_y = target_x, target_y

                # Move cursor
                pyautogui.moveTo(int(stabilized_x), int(stabilized_y))

                # Update previous position
                self.prev_cursor_x = stabilized_x
                self.prev_cursor_y = stabilized_y

                # Reset mouse timeout
                self.last_mouse_move = time.time()

            except Exception as e:
                logging.error(f"Cursor movement error: {e}")

    def handle_dwell_clicking(self, cursor_x: float, cursor_y: float,
                            detection_found: bool, move_cursor: bool = True) -> bool:
        """Handle dwell-based clicking with cursor stabilization"""
        current_time = time.time()

        # Check if cursor is stable (minimal movement)
        cursor_moved = abs(cursor_x - self.prev_cursor_x) > 5 or abs(cursor_y - self.prev_cursor_y) > 5

        if detection_found and not cursor_moved and not self.is_clicking:
            # Start dwell timer
            if self.dwell_start_time is None:
                self.dwell_start_time = current_time
                logging.debug("Dwell clicking started")

            # Check if dwell time exceeded
            elif current_time - self.dwell_start_time >= self.dwell_threshold:
                self.perform_click()
                self.dwell_start_time = None
                self.is_clicking = True
                return True

        else:
            # Reset dwell timer if cursor moved or no detection
            if self.dwell_start_time is not None:
                logging.debug("Dwell clicking reset")
            self.dwell_start_time = None
            self.is_clicking = False

        # Move cursor if requested
        if move_cursor and detection_found:
            self.move_cursor(cursor_x, cursor_y)

        return False

    def perform_click(self, button: str = 'left'):
        """Perform a mouse click"""
        if not self.mouse_enabled:
            return

        try:
            with self.lock:
                if button == 'left':
                    pyautogui.click()
                elif button == 'right':
                    pyautogui.rightClick()
                elif button == 'middle':
                    pyautogui.middleClick()

                logging.info(f"Mouse {button} click performed")
        except Exception as e:
            logging.error(f"Click error: {e}")

    def perform_double_click(self):
        """Perform a double click"""
        if not self.mouse_enabled:
            return

        try:
            with self.lock:
                pyautogui.doubleClick()
                logging.info("Double click performed")
        except Exception as e:
            logging.error(f"Double click error: {e}")

    def perform_drag(self, start_x: float, start_y: float, end_x: float, end_y: float):
        """Perform a drag operation"""
        if not self.mouse_enabled:
            return

        try:
            with self.lock:
                pyautogui.moveTo(int(start_x), int(start_y))
                pyautogui.dragTo(int(end_x), int(end_y), duration=0.5)
                logging.info("Drag operation performed")
        except Exception as e:
            logging.error(f"Drag error: {e}")

    def scroll(self, direction: str, clicks: int = 3):
        """Perform scrolling"""
        if not self.mouse_enabled:
            return

        try:
            with self.lock:
                if direction == 'up':
                    pyautogui.scroll(clicks)
                elif direction == 'down':
                    pyautogui.scroll(-clicks)
                logging.info(f"Scrolled {direction}")
        except Exception as e:
            logging.error(f"Scroll error: {e}")

    def toggle_mouse_control(self):
        """Toggle mouse control on/off"""
        self.mouse_enabled = not self.mouse_enabled
        status = "enabled" if self.mouse_enabled else "disabled"
        logging.info(f"Mouse control {status}")

        if not self.mouse_enabled:
            # Move cursor to center when disabled
            center_x, center_y = self.screen_width // 2, self.screen_height // 2
            self.move_cursor(center_x, center_y, smooth=False)

    def check_mouse_timeout(self) -> bool:
        """Check if mouse control should be disabled due to timeout"""
        if time.time() - self.last_mouse_move > self.mouse_timeout:
            logging.warning("Mouse control timeout - disabling")
            self.mouse_enabled = False
            return True
        return False

    def set_dwell_time(self, dwell_time: float):
        """Set the dwell time for clicking"""
        self.dwell_threshold = max(0.5, min(dwell_time, 5.0))  # Clamp between 0.5-5 seconds
        logging.info(f"Dwell time set to {self.dwell_threshold}s")

    def set_smoothing_factor(self, factor: float):
        """Set cursor smoothing factor"""
        self.smoothing_factor = max(0.0, min(factor, 1.0))
        logging.info(f"Smoothing factor set to {self.smoothing_factor}")

    def get_cursor_position(self) -> Tuple[int, int]:
        """Get current cursor position"""
        try:
            x, y = pyautogui.position()
            return x, y
        except Exception as e:
            logging.error(f"Error getting cursor position: {e}")
            return self.screen_width // 2, self.screen_height // 2

    def reset_to_center(self):
        """Reset cursor to screen center"""
        center_x, center_y = self.screen_width // 2, self.screen_height // 2
        self.move_cursor(center_x, center_y, smooth=False)
        logging.info("Cursor reset to center")
