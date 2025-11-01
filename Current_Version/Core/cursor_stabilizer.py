#!/usr/bin/env python3
"""
Cursor Stabilizer Module
Provides advanced smoothing for cursor trajectory using Kalman Filter and EMA
"""

import numpy as np
from collections import deque
import logging


class KalmanFilter:
    """Simple Kalman filter for cursor smoothing"""

    def __init__(self, process_noise=0.01, measurement_noise=0.1):
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.estimated = np.array([0.0, 0.0])
        self.estimate_error = np.array([1.0, 1.0])
        self.first_measurement = True

    def update(self, measurement: np.ndarray) -> np.ndarray:
        """Update filter with new measurement"""
        if self.first_measurement:
            self.estimated = measurement.copy()
            self.first_measurement = False
            return self.estimated

        # Prediction step
        prediction_error = self.estimate_error + self.process_noise

        # Update step
        kalman_gain = prediction_error / (prediction_error + self.measurement_noise)
        self.estimated = self.estimated + kalman_gain * (measurement - self.estimated)
        self.estimate_error = (1 - kalman_gain) * prediction_error

        return self.estimated.copy()

    def reset(self):
        """Reset the filter state"""
        self.first_measurement = True
        self.estimated = np.array([0.0, 0.0])
        self.estimate_error = np.array([1.0, 1.0])


class ExponentialMovingAverage:
    """Exponential Moving Average for cursor smoothing"""

    def __init__(self, alpha=0.7):
        """
        Initialize EMA filter
        Args:
            alpha: Smoothing factor (0-1). Higher values = less smoothing
        """
        self.alpha = alpha
        self.smoothed = None
        self.first_measurement = True

    def update(self, measurement: np.ndarray) -> np.ndarray:
        """Update EMA with new measurement"""
        if self.first_measurement or self.smoothed is None:
            self.smoothed = measurement.copy()
            self.first_measurement = False
            return self.smoothed

        # EMA formula: smoothed = alpha * measurement + (1-alpha) * previous_smoothed
        self.smoothed = self.alpha * measurement + (1 - self.alpha) * self.smoothed
        return self.smoothed.copy()

    def reset(self):
        """Reset the EMA state"""
        self.smoothed = None
        self.first_measurement = True


class CursorStabilizer:
    """
    Advanced cursor trajectory stabilizer
    Supports multiple smoothing algorithms for optimal cursor movement
    """

    def __init__(self, method='kalman', **kwargs):
        """
        Initialize cursor stabilizer

        Args:
            method: Smoothing method ('kalman', 'ema', 'none')
            **kwargs: Parameters for the chosen method
        """
        self.method = method.lower()
        self.filter = None

        if self.method == 'kalman':
            process_noise = kwargs.get('process_noise', 0.003)
            measurement_noise = kwargs.get('measurement_noise', 0.03)
            self.filter = KalmanFilter(process_noise, measurement_noise)
            logging.info(f"Initialized Kalman Filter stabilizer (process_noise={process_noise}, measurement_noise={measurement_noise})")

        elif self.method == 'ema':
            alpha = kwargs.get('alpha', 0.7)
            self.filter = ExponentialMovingAverage(alpha)
            logging.info(f"Initialized EMA stabilizer (alpha={alpha})")

        elif self.method == 'none':
            logging.info("Cursor stabilization disabled")
        else:
            logging.warning(f"Unknown stabilization method '{method}', using 'none'")
            self.method = 'none'

    def stabilize(self, position: np.ndarray) -> np.ndarray:
        """
        Stabilize cursor position

        Args:
            position: Raw cursor position as numpy array [x, y]

        Returns:
            Stabilized cursor position
        """
        if self.method == 'none' or self.filter is None:
            return position

        try:
            return self.filter.update(position)
        except Exception as e:
            logging.error(f"Stabilization error: {e}")
            return position

    def reset(self):
        """Reset the stabilizer state"""
        if self.filter and hasattr(self.filter, 'reset'):
            self.filter.reset()
            logging.info("Cursor stabilizer reset")

    def set_method(self, method: str, **kwargs):
        """Change stabilization method"""
        self.__init__(method, **kwargs)

    def get_method(self) -> str:
        """Get current stabilization method"""
        return self.method

    def get_stats(self) -> dict:
        """Get stabilizer statistics"""
        stats = {
            'method': self.method,
            'active': self.method != 'none'
        }

        if self.filter:
            if hasattr(self.filter, 'estimated'):
                stats['current_estimate'] = self.filter.estimated.tolist()
            if hasattr(self.filter, 'smoothed') and self.filter.smoothed is not None:
                stats['current_smoothed'] = self.filter.smoothed.tolist()

        return stats
