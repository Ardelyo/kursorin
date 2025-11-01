
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import time

# Mock the necessary modules before importing the main script
import sys
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['pyautogui'] = MagicMock()
sys.modules['mss'] = MagicMock()

from Core.smart_cursor_stable import SmartCursorStable

class TestFix(unittest.TestCase):

    @patch('Core.smart_cursor_stable.HighPerformanceCursor')
    def test_no_crash_on_none_result(self, MockHighPerformanceCursor):
        # Arrange
        mock_hp_cursor = MockHighPerformanceCursor.return_value
        mock_hp_cursor.process_frame_async.return_value = (None, False, None)

        # Mock the GUI to prevent it from starting
        with patch('Core.smart_cursor_stable.tk.Tk'):
            system = SmartCursorStable()

        # Act & Assert
        try:
            # Run a few iterations of the main loop to simulate the scenario
            for _ in range(5):
                system.main_loop()
                time.sleep(0.1)
            # If no exception is raised, the test passes
            self.assertTrue(True, "System did not crash on None result")
        except Exception as e:
            self.fail(f"System crashed with exception: {e}")

if __name__ == '__main__':
    unittest.main()
