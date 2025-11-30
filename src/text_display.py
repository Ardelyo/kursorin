"""
Text Display Module
Handles text display and editing for typing mode
"""

import cv2
from typing import List, Tuple
import time


class TextDisplay:
    """Manages text display and editing for typing mode"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Text display settings
        self.text_lines: List[str] = []
        self.current_line = 0
        self.cursor_position = 0
        self.max_chars_per_line = 60
        self.max_lines = 10

        # Display position and styling
        self.display_x = 50
        self.display_y = 100
        self.line_height = 40
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.8
        self.font_thickness = 2
        self.text_color = (255, 255, 255)  # White text
        self.cursor_color = (0, 255, 0)    # Green cursor

        # Cursor blinking
        self.cursor_visible = True
        self.last_cursor_toggle = time.time()
        self.cursor_blink_rate = 0.5  # Blink every 0.5 seconds

    def add_text(self, text: str):
        """Add text to the current position"""
        if not self.text_lines:
            self.text_lines.append("")

        for char in text:
            if char == "\n":
                self._insert_newline()
            elif char == "\b":  # Backspace
                self._backspace()
            else:
                self._insert_character(char)

    def _insert_character(self, char: str):
        """Insert a character at the current cursor position"""
        current_line = self.text_lines[self.current_line]

        # Insert character at cursor position
        before_cursor = current_line[:self.cursor_position]
        after_cursor = current_line[self.cursor_position:]
        new_line = before_cursor + char + after_cursor

        # Check if line is too long
        if len(new_line) > self.max_chars_per_line:
            # Move to next line
            self._insert_newline()
            self._insert_character(char)
            return

        self.text_lines[self.current_line] = new_line
        self.cursor_position += 1

    def _insert_newline(self):
        """Insert a new line"""
        # Split current line at cursor position
        current_line = self.text_lines[self.current_line]
        before_cursor = current_line[:self.cursor_position]
        after_cursor = current_line[self.cursor_position:]

        # Update current line
        self.text_lines[self.current_line] = before_cursor

        # Insert new line
        self.text_lines.insert(self.current_line + 1, after_cursor)

        # Move cursor to beginning of new line
        self.current_line += 1
        self.cursor_position = 0

        # Remove old lines if we exceed max_lines
        if len(self.text_lines) > self.max_lines:
            self.text_lines.pop(0)
            self.current_line = min(self.current_line, len(self.text_lines) - 1)

    def _backspace(self):
        """Handle backspace operation"""
        if self.cursor_position > 0:
            # Remove character before cursor
            current_line = self.text_lines[self.current_line]
            before_cursor = current_line[:self.cursor_position - 1]
            after_cursor = current_line[self.cursor_position:]
            self.text_lines[self.current_line] = before_cursor + after_cursor
            self.cursor_position -= 1
        elif self.current_line > 0:
            # Move to end of previous line
            prev_line = self.text_lines[self.current_line - 1]
            self.cursor_position = len(prev_line)

            # Merge lines
            self.text_lines[self.current_line - 1] = prev_line + self.text_lines[self.current_line]
            self.text_lines.pop(self.current_line)
            self.current_line -= 1

    def get_current_text(self) -> str:
        """Get the current text as a single string"""
        return "\n".join(self.text_lines)

    def clear_text(self):
        """Clear all text"""
        self.text_lines = [""]
        self.current_line = 0
        self.cursor_position = 0

    def draw_text_display(self, frame):
        """Draw the text display on the frame"""
        display_frame = frame.copy()

        # Update cursor blinking
        current_time = time.time()
        if current_time - self.last_cursor_toggle > self.cursor_blink_rate:
            self.cursor_visible = not self.cursor_visible
            self.last_cursor_toggle = current_time

        # Draw each line of text
        for line_idx, line in enumerate(self.text_lines):
            y_pos = self.display_y + (line_idx * self.line_height)

            # Draw the text
            cv2.putText(display_frame, line, (self.display_x, y_pos),
                       self.font, self.font_scale, self.text_color, self.font_thickness)

            # Draw cursor if this is the current line
            if line_idx == self.current_line and self.cursor_visible:
                cursor_x = self.display_x + (self.cursor_position * 20)  # Approximate character width
                cursor_y1 = y_pos - 25  # Above the text
                cursor_y2 = y_pos + 5   # Below the text
                cv2.line(display_frame, (int(cursor_x), cursor_y1), (int(cursor_x), cursor_y2),
                        self.cursor_color, 2)

        # Draw text display border
        border_padding = 20
        cv2.rectangle(display_frame,
                     (self.display_x - border_padding, self.display_y - 30),
                     (self.screen_width - 50, self.display_y + (len(self.text_lines) * self.line_height) + 10),
                     (100, 100, 100), 2)  # Gray border

        # Draw "Text Input" label
        cv2.putText(display_frame, "Text Input:", (self.display_x, self.display_y - 10),
                   self.font, 0.6, (200, 200, 200), 1)

        return display_frame

    def get_display_bounds(self) -> Tuple[int, int, int, int]:
        """Get the text display bounding box (x, y, width, height)"""
        width = self.screen_width - 2 * self.display_x
        height = len(self.text_lines) * self.line_height + 40
        return (self.display_x, self.display_y - 30, width, height)
