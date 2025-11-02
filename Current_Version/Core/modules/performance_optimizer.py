"""
Performance Optimization Module
GPU acceleration, frame skipping, and processing optimizations
"""

import cv2
import numpy as np
import time
import logging
from typing import Dict, Any, Tuple, Optional


class PerformanceOptimizer:
    """Handles performance optimizations for cursor control system"""

    def __init__(self):
        # GPU acceleration settings
        self.gpu_enabled = False
        self.cuda_available = False
        self.opencl_available = False

        # Frame skipping and motion detection
        self.frame_skip_enabled = True
        self.motion_threshold = 0.01
        self.skip_counter = 0
        self.skip_interval = 3
        self.prev_frame_gray = None

        # Resolution scaling based on distance
        self.distance_scaling_enabled = True
        self.near_distance_threshold = 0.3
        self.far_distance_threshold = 0.7
        self.near_scale = 1.0
        self.far_scale = 0.5

        # Landmark caching for static poses
        self.landmark_cache_enabled = True
        self.landmark_cache = {}
        self.cache_timeout = 0.5
        self.last_cache_update = 0
        self.pose_stability_threshold = 0.05

        # Performance tracking
        self.performance_metrics = {
            'gpu_acceleration': False,
            'frame_skip_rate': 0.0,
            'avg_processing_resolution': 1.0,
            'cache_hit_rate': 0.0,
        }

        self._enable_gpu_acceleration()

    def _enable_gpu_acceleration(self):
        """Enable GPU acceleration if available"""
        try:
            # Check for CUDA availability
            import torch
            if torch.cuda.is_available():
                self.cuda_available = True
                self.gpu_enabled = True
                self.performance_metrics['gpu_acceleration'] = True
                logging.info("CUDA GPU acceleration enabled")
            else:
                # Check for OpenCL support
                try:
                    import pyopencl as cl
                    platforms = cl.get_platforms()
                    if platforms:
                        self.opencl_available = True
                        self.gpu_enabled = True
                        self.performance_metrics['gpu_acceleration'] = True
                        logging.info("OpenCL GPU acceleration enabled")
                    else:
                        logging.info("No GPU acceleration available, using CPU")
                except ImportError:
                    logging.info("OpenCL not available, using CPU")

        except ImportError:
            logging.info("PyTorch not available for GPU detection, using CPU")

        # If no GPU, ensure we're using optimized CPU settings
        if not self.gpu_enabled:
            logging.info("Using optimized CPU processing")

    def should_process_frame(self, frame: np.ndarray) -> bool:
        """Determine if frame should be processed based on motion detection"""
        if not self.frame_skip_enabled:
            return True

        try:
            # Convert to grayscale for motion detection
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame_gray = cv2.GaussianBlur(frame_gray, (5, 5), 0)

            if self.prev_frame_gray is None:
                self.prev_frame_gray = frame_gray
                return True

            # Calculate motion
            frame_diff = cv2.absdiff(frame_gray, self.prev_frame_gray)
            motion_level = np.mean(frame_diff) / 255.0

            self.prev_frame_gray = frame_gray

            # Process frame if motion is above threshold
            if motion_level > self.motion_threshold:
                self.skip_counter = 0
                return True

            # Skip frames when no motion, but process occasionally
            self.skip_counter += 1
            if self.skip_counter >= self.skip_interval:
                self.skip_counter = 0
                return True

            return False

        except Exception as e:
            logging.error(f"Frame processing check error: {e}")
            return True

    def apply_distance_scaling(self, frame: np.ndarray, distance: float = 0.5) -> Tuple[np.ndarray, float]:
        """Apply resolution scaling based on distance"""
        if not self.distance_scaling_enabled:
            return frame, 1.0

        try:
            if distance < self.near_distance_threshold:
                scale = self.near_scale
            elif distance > self.far_distance_threshold:
                scale = self.far_scale
            else:
                # Linear interpolation between thresholds
                ratio = (distance - self.near_distance_threshold) / (self.far_distance_threshold - self.near_distance_threshold)
                scale = self.near_scale + ratio * (self.far_scale - self.near_scale)

            if scale < 1.0:
                new_width = int(frame.shape[1] * scale)
                new_height = int(frame.shape[0] * scale)
                scaled_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
                return scaled_frame, scale
            else:
                return frame, 1.0

        except Exception as e:
            logging.error(f"Distance scaling error: {e}")
            return frame, 1.0

    def get_cached_landmarks(self, pose_key: str) -> Optional[Any]:
        """Retrieve cached landmarks if still valid"""
        if not self.landmark_cache_enabled:
            return None

        current_time = time.time()
        if pose_key in self.landmark_cache:
            cached_data, timestamp = self.landmark_cache[pose_key]
            if current_time - timestamp < self.cache_timeout:
                return cached_data

        return None

    def set_cached_landmarks(self, pose_key: str, landmarks: Any):
        """Cache landmarks for pose key"""
        if self.landmark_cache_enabled:
            self.landmark_cache[pose_key] = (landmarks, time.time())

            # Limit cache size
            if len(self.landmark_cache) > 100:
                # Remove oldest entries
                sorted_items = sorted(self.landmark_cache.items(), key=lambda x: x[1][1])
                self.landmark_cache = dict(sorted_items[-50:])

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        return self.performance_metrics.copy()

    def update_performance_metrics(self, processing_time: float, resolution_scale: float, cache_hit: bool):
        """Update performance tracking metrics"""
        # This would be called after processing each frame
        pass

    def optimize_mediapipe_settings(self, distance: float) -> Dict[str, Any]:
        """Get optimized MediaPipe settings based on distance and performance"""
        settings = {
            'min_detection_confidence': 0.3,
            'min_tracking_confidence': 0.3,
            'model_complexity': 0
        }

        # Adjust based on distance (closer = higher accuracy)
        if distance < 0.3:
            settings['min_detection_confidence'] = 0.5
            settings['min_tracking_confidence'] = 0.5
            settings['model_complexity'] = 1
        elif distance > 0.7:
            settings['min_detection_confidence'] = 0.2
            settings['min_tracking_confidence'] = 0.2
            settings['model_complexity'] = 0

        return settings
