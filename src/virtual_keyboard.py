"""
Virtual Keyboard Module
Displays and manages an on-screen keyboard for typing mode
"""

import cv2
import numpy as np
from typing import Tuple, List, Dict, Optional, Any
from enum import Enum
import time
import text_prediction


class KeyState(Enum):
    NORMAL = "normal"
    HOVER = "hover"
    PRESSED = "pressed"
    DISABLED = "disabled"


class KeyType(Enum):
    CHARACTER = "character"
    MODIFIER = "modifier"
    FUNCTION = "function"
    SPECIAL = "special"


class VirtualKey:
    """Represents a single key on the virtual keyboard"""

    def __init__(self, key_id: str, label: str, x: int, y: int, width: int, height: int,
                 key_type: KeyType = KeyType.CHARACTER, alt_label: str = ""):
        self.key_id = key_id
        self.label = label
        self.alt_label = alt_label
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.key_type = key_type
        self.state = KeyState.NORMAL
        self.last_press_time = 0
        self.press_cooldown = 0.2  # 200ms cooldown between presses

    def contains_point(self, point: Tuple[int, int]) -> bool:
        """Check if a point is within this key's bounds"""
        px, py = point
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)

    def set_state(self, state: KeyState):
        """Set the key's visual state"""
        self.state = state

    def can_press(self) -> bool:
        """Check if the key can be pressed (cooldown check)"""
        return time.time() - self.last_press_time > self.press_cooldown

    def press(self) -> str:
        """Press the key and return the character to input"""
        current_time = time.time()
        if current_time - self.last_press_time > self.press_cooldown:
            self.last_press_time = current_time
            self.state = KeyState.PRESSED
            return self._get_output_character()
        return ""

    def _get_output_character(self) -> str:
        """Get the character this key should output"""
        if self.key_type == KeyType.CHARACTER:
            return self.label
        elif self.key_id == "space":
            return " "
        elif self.key_id == "enter":
            return "\n"
        elif self.key_id == "backspace":
            return "\b"
        elif self.key_id == "tab":
            return "\t"
        return ""


class VirtualKeyboardDisplay:
    """Manages the virtual keyboard display and interaction"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Keyboard layout settings
        self.keyboard_width = int(screen_width * 0.8)
        self.keyboard_height = int(screen_height * 0.4)
        self.keyboard_x = (screen_width - self.keyboard_width) // 2
        self.keyboard_y = screen_height - self.keyboard_height - 50

        # Key dimensions
        self.key_margin = 3
        self.key_height = 50
        self.key_width_standard = 50
        self.key_width_space = 300

        # Visual settings
        self.colors = {
            KeyState.NORMAL: (200, 200, 200),    # Light gray
            KeyState.HOVER: (150, 200, 255),     # Light blue
            KeyState.PRESSED: (100, 150, 255),   # Darker blue
            KeyState.DISABLED: (100, 100, 100),  # Dark gray
        }
        self.text_colors = {
            KeyState.NORMAL: (0, 0, 0),          # Black
            KeyState.HOVER: (0, 0, 0),           # Black
            KeyState.PRESSED: (255, 255, 255),   # White
            KeyState.DISABLED: (150, 150, 150),  # Light gray
        }

        # Font settings
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.7
        self.font_thickness = 2

        # Initialize keyboard layout
        self.keys = self._create_keyboard_layout()

        # State tracking
        self.shift_pressed = False
        self.caps_lock = False
        self.last_hovered_key = None

        # Prediction
        self.predictor = text_prediction.TextPredictor()
        self.current_word = ""
        self.suggestions = []
        self.suggestion_height = 40
        self.suggestion_y = self.keyboard_y - self.suggestion_height - 10

    def _update_suggestions(self):
        """Update suggestions based on current word"""
        self.suggestions = self.predictor.get_suggestions(self.current_word)

    def _get_suggestion_rects(self) -> List[Tuple[int, int, int, int, str]]:
        """Get rectangles for current suggestions: (x, y, w, h, text)"""
        if not self.suggestions:
            return []
        
        rects = []
        total_width = self.keyboard_width
        width_per_suggestion = total_width // 3
        
        for i, text in enumerate(self.suggestions):
            x = self.keyboard_x + (i * width_per_suggestion)
            y = self.suggestion_y
            rects.append((x, y, width_per_suggestion - 5, self.suggestion_height, text))
        return rects

    def _create_keyboard_layout(self) -> Dict[str, VirtualKey]:
        """Create the QWERTY keyboard layout"""
        keys = {}

        # Define keyboard rows
        row1 = "1234567890"
        row2 = "QWERTYUIOP"
        row3 = "ASDFGHJKL"
        row4 = "ZXCVBNM"

        current_y = self.keyboard_y + 10

        # Row 1: Numbers
        current_x = self.keyboard_x + 10
        for char in row1:
            key = VirtualKey(char, char, current_x, current_y,
                           self.key_width_standard, self.key_height)
            keys[char] = key
            current_x += self.key_width_standard + self.key_margin

        current_y += self.key_height + self.key_margin

        # Row 2: QWERTYUIOP
        current_x = self.keyboard_x + 30  # Slight offset for alignment
        for char in row2:
            key = VirtualKey(char, char, current_x, current_y,
                           self.key_width_standard, self.key_height)
            keys[char] = key
            current_x += self.key_width_standard + self.key_margin

        current_y += self.key_height + self.key_margin

        # Row 3: ASDFGHJKL
        current_x = self.keyboard_x + 50  # More offset
        for char in row3:
            key = VirtualKey(char, char, current_x, current_y,
                           self.key_width_standard, self.key_height)
            keys[char] = key
            current_x += self.key_width_standard + self.key_margin

        current_y += self.key_height + self.key_margin

        # Row 4: ZXCVBNM
        current_x = self.keyboard_x + 80  # Even more offset
        for char in row4:
            key = VirtualKey(char, char, current_x, current_y,
                           self.key_width_standard, self.key_height)
            keys[char] = key
            current_x += self.key_width_standard + self.key_margin

        # Special keys
        # Shift keys
        shift_left = VirtualKey("shift_left", "SHIFT", self.keyboard_x + 10, current_y,
                              70, self.key_height, KeyType.MODIFIER)
        keys["shift_left"] = shift_left

        shift_right = VirtualKey("shift_right", "SHIFT",
                               current_x + 20, current_y, 70, self.key_height, KeyType.MODIFIER)
        keys["shift_right"] = shift_right

        # Spacebar
        space_y = current_y + self.key_height + self.key_margin
        space = VirtualKey("space", "SPACE", self.keyboard_x + 150, space_y,
                         self.key_width_space, self.key_height, KeyType.SPECIAL)
        keys["space"] = space

        # Enter key
        enter = VirtualKey("enter", "ENTER", current_x + 100, current_y,
                         80, self.key_height, KeyType.SPECIAL)
        keys["enter"] = enter

        # Backspace
        backspace = VirtualKey("backspace", "BKSP",
                             self.keyboard_x + self.keyboard_width - 80, self.keyboard_y + 10,
                             70, self.key_height, KeyType.SPECIAL)
        keys["backspace"] = backspace

        return keys

    def update_finger_position(self, finger_positions: List[Tuple[int, int]]):
        """Update keyboard state based on finger positions"""
        # Reset all keys to normal state
        for key in self.keys.values():
            if key.state != KeyState.DISABLED:
                key.set_state(KeyState.NORMAL)

        # Find which key the primary finger is hovering over
        if finger_positions:
            primary_finger = finger_positions[0]  # Use first finger
            hovered_key = None

            for key in self.keys.values():
                if key.contains_point(primary_finger):
                    hovered_key = key
                    if key.can_press():
                        key.set_state(KeyState.HOVER)
                    break

            self.last_hovered_key = hovered_key

    def press_key_at_position(self, position: Tuple[int, int]) -> str:
        """Press the key at the given position and return the character"""
        # Check suggestions first
        px, py = position
        for x, y, w, h, text in self._get_suggestion_rects():
            if x <= px <= x + w and y <= py <= y + h:
                # Suggestion clicked
                # Return the remaining part of the word plus a space
                remaining = text[len(self.current_word):] + " "
                self.current_word = "" # Reset current word
                self.suggestions = []
                return remaining

        for key in self.keys.values():
            if key.contains_point(position) and key.can_press():
                char = key.press()
                
                # Update current word for prediction
                if char:
                    if len(char) == 1 and char.isalnum():
                        self.current_word += char
                        self._update_suggestions()
                    elif char == " ":
                        self.predictor.learn_word(self.current_word) # Learn finished word
                        self.current_word = ""
                        self.suggestions = []
                    elif char == "\b":
                        self.current_word = self.current_word[:-1]
                        self._update_suggestions()
                    elif char == "\n":
                        self.current_word = ""
                        self.suggestions = []
                        
                return char
        return ""

    def draw_keyboard(self, frame: np.ndarray) -> np.ndarray:
        """Draw the virtual keyboard on the frame"""
        # Create a copy of the frame
        display_frame = frame.copy()

        # Draw keyboard background
        cv2.rectangle(display_frame,
                     (self.keyboard_x, self.keyboard_y),
                     (self.keyboard_x + self.keyboard_width, self.keyboard_y + self.keyboard_height),
                     (50, 50, 50), -1)  # Dark gray background

        # Draw border
        cv2.rectangle(display_frame,
                     (self.keyboard_x, self.keyboard_y),
                     (self.keyboard_x + self.keyboard_width, self.keyboard_y + self.keyboard_height),
                     (255, 255, 255), 2)  # White border

        # Draw each key
        for key in self.keys.values():
            self._draw_key(display_frame, key)

        # Draw suggestions
        for x, y, w, h, text in self._get_suggestion_rects():
            # Background
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (200, 200, 255), -1)
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (255, 255, 255), 1)
            
            # Text
            text_size = cv2.getTextSize(text, self.font, 0.6, 1)[0]
            text_x = x + (w - text_size[0]) // 2
            text_y = y + (h + text_size[1]) // 2
            cv2.putText(display_frame, text, (text_x, text_y), self.font, 0.6, (0, 0, 0), 1)

        return display_frame

    def _draw_key(self, frame: np.ndarray, key: VirtualKey):
        """Draw a single key on the frame"""
        # Key background
        color = self.colors[key.state]
        cv2.rectangle(frame, (key.x, key.y), (key.x + key.width, key.y + key.height),
                     color, -1)

        # Key border
        border_color = (255, 255, 255) if key.state == KeyState.PRESSED else (0, 0, 0)
        cv2.rectangle(frame, (key.x, key.y), (key.x + key.width, key.y + key.height),
                     border_color, 1)

        # Key label
        text_color = self.text_colors[key.state]
        text = key.alt_label if (self.shift_pressed or self.caps_lock) and key.alt_label else key.label

        # Calculate text position for centering
        text_size = cv2.getTextSize(text, self.font, self.font_scale, self.font_thickness)[0]
        text_x = key.x + (key.width - text_size[0]) // 2
        text_y = key.y + (key.height + text_size[1]) // 2

        cv2.putText(frame, text, (text_x, text_y), self.font,
                   self.font_scale, text_color, self.font_thickness)

    def toggle_shift(self):
        """Toggle shift state"""
        self.shift_pressed = not self.shift_pressed

    def toggle_caps_lock(self):
        """Toggle caps lock state"""
        self.caps_lock = not self.caps_lock

    def get_keyboard_bounds(self) -> Tuple[int, int, int, int]:
        """Get keyboard bounding box (x, y, width, height)"""
        return (self.keyboard_x, self.keyboard_y, self.keyboard_width, self.keyboard_height)

    def is_position_on_keyboard(self, position: Tuple[int, int]) -> bool:
        """Check if a position is within the keyboard area"""
        x, y = position
        return (self.keyboard_x <= x <= self.keyboard_x + self.keyboard_width and
                self.keyboard_y <= y <= self.keyboard_y + self.keyboard_height)
