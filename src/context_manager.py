"""
Context Manager Module
Detects active application context and suggests appropriate modes
"""

import logging
import time
import sys

# Try to import Windows-specific libraries
try:
    import win32gui
    import win32process
    WINDOWS_SUPPORT = True
except ImportError:
    WINDOWS_SUPPORT = False
    logging.warning("pywin32 not found. Context awareness will be limited.")

class ContextManager:
    """Manages application context and automatic mode switching"""

    def __init__(self):
        self.enabled = True
        self.last_check_time = 0
        self.check_interval = 1.0  # Check every 1 second
        self.current_context = "unknown"
        
        # Define rules: keyword -> mode
        self.rules = {
            "game": "gaming",
            "steam": "gaming",
            "minecraft": "gaming",
            "valorant": "gaming",
            "csgo": "gaming",
            "fortnite": "gaming",
            "notepad": "typing",
            "word": "typing",
            "docs": "typing",
            "code": "typing",
            "visual studio": "typing",
            "browser": "normal",
            "chrome": "normal",
            "firefox": "normal",
            "edge": "normal"
        }

    def get_active_window_title(self) -> str:
        """Get the title of the currently active window"""
        if not WINDOWS_SUPPORT:
            return ""
            
        try:
            window = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(window)
        except Exception as e:
            logging.error(f"Error getting window title: {e}")
            return ""

    def check_context(self) -> str:
        """Check current context and return suggested mode"""
        if not self.enabled:
            return None
            
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return None
            
        self.last_check_time = current_time
        
        title = self.get_active_window_title().lower()
        if not title:
            return None
            
        # Check rules
        suggested_mode = None
        for keyword, mode in self.rules.items():
            if keyword in title:
                suggested_mode = mode
                break
        
        # If no specific rule matches, default to normal if it was something else
        # But we don't want to switch to normal aggressively if we are just in a random window
        # So we only return a suggestion if we found a match
        
        if suggested_mode and suggested_mode != self.current_context:
            logging.info(f"Context change detected: '{title}' -> {suggested_mode}")
            self.current_context = suggested_mode
            return suggested_mode
            
        return None

    def set_enabled(self, enabled: bool):
        """Enable/disable context awareness"""
        self.enabled = enabled
