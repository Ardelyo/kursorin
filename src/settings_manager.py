"""
Settings Management Module
Handles loading, saving, and validation of application settings
"""

import json
import os
import logging
from typing import Dict, Any, Optional


class SettingsManager:
    """Manages application settings with validation and fallbacks"""

    DEFAULT_SETTINGS = {
        # Core settings
        'smoothing': 0.7,
        'dwell_time': 2.0,
        'voice_feedback': False,
        'sound_feedback': True,
        'gesture_recognition': True,
        'adaptive_speed': False,

        # Tracking settings
        'tracking_type': 'finger',
        'tracking_sensitivity': 0.8,
        'multi_tracking': False,

        # Stabilizer settings
        'stabilizer_method': 'kalman',
        'stabilizer_alpha': 0.7,
        'stabilizer_process_noise': 0.003,
        'stabilizer_measurement_noise': 0.03,

        # Performance settings
        'gpu_acceleration': True,
        'frame_skip_threshold': 0.1,
        'performance_mode': 'balanced',

        # Accessibility settings
        'high_contrast': False,
        'large_buttons': False,
        'keyboard_shortcuts': True,

        # UI settings
        'window_size': '800x600',
        'theme': 'default'
    }

    def __init__(self, settings_file: str = 'config/cursor_settings.json'):
        self.settings_file = settings_file
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load_settings()

    def load_settings(self) -> None:
        """Load settings from file with comprehensive error handling"""
        try:
            if not os.path.exists(self.settings_file):
                logging.info(f"Settings file {self.settings_file} not found, using defaults")
                return

            # Check file size to prevent loading corrupted files
            if os.path.getsize(self.settings_file) > 1024 * 1024:  # 1MB limit
                logging.warning("Settings file too large, using defaults")
                return

            with open(self.settings_file, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)

            # Validate and merge loaded settings
            self._validate_and_merge_settings(loaded_settings)
            logging.info(f"Settings loaded successfully from {self.settings_file}")

        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in settings file: {e}")
        except PermissionError:
            logging.error(f"Permission denied reading settings file")
        except Exception as e:
            logging.error(f"Error loading settings: {e}")

    def save_settings(self) -> bool:
        """Save current settings to file"""
        try:
            # Create backup if file exists
            if os.path.exists(self.settings_file):
                backup_file = f"{self.settings_file}.backup"
                os.replace(self.settings_file, backup_file)

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)

            logging.info(f"Settings saved to {self.settings_file}")
            return True

        except PermissionError:
            logging.error(f"Permission denied writing settings file")
            return False
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            return False

    def _validate_and_merge_settings(self, loaded_settings: Dict[str, Any]) -> None:
        """Validate and merge loaded settings with defaults"""
        for key, value in loaded_settings.items():
            if key in self.DEFAULT_SETTINGS:
                expected_type = type(self.DEFAULT_SETTINGS[key])
                if isinstance(value, expected_type):
                    self.settings[key] = value
                else:
                    logging.warning(f"Invalid type for setting {key}: expected {expected_type.__name__}, got {type(value).__name__}")
            else:
                logging.warning(f"Unknown setting: {key}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default if default is not None else self.DEFAULT_SETTINGS.get(key))

    def set(self, key: str, value: Any) -> bool:
        """Set a setting value with validation"""
        if key not in self.DEFAULT_SETTINGS:
            logging.warning(f"Unknown setting: {key}")
            return False

        expected_type = type(self.DEFAULT_SETTINGS[key])
        if not isinstance(value, expected_type):
            logging.error(f"Invalid type for setting {key}: expected {expected_type.__name__}, got {type(value).__name__}")
            return False

        self.settings[key] = value
        return True

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults"""
        self.settings = self.DEFAULT_SETTINGS.copy()
        logging.info("Settings reset to defaults")

    def get_all(self) -> Dict[str, Any]:
        """Get all current settings"""
        return self.settings.copy()
