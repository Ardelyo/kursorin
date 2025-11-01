#!/usr/bin/env python3
"""
Performance benchmark for Camera Cursor System
Tests processing speed and resource usage
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import psutil
import os

def benchmark_mediapipe():
    """Benchmark MediaPipe Holistic processing speed"""
    print("🔬 Benchmarking MediaPipe Holistic...")

    # Initialize
    mp_holistic = mp.solutions.holistic
    holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    # Create test frame
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    test_rgb = cv2.cvtColor(test_frame, cv2.COLOR_BGR2RGB)

    # Warm up
    for _ in range(5):
        holistic.process(test_rgb)

    # Benchmark
    times = []
    for _ in range(50):
        start = time.time()
        results = holistic.process(test_rgb)
        end = time.time()
        times.append(end - start)

    avg_time = sum(times) / len(times)
    fps = 1.0 / avg_time

    holistic.close()

    print(".3f"    print(".1f"
    return fps

def benchmark_memory():
    """Check memory usage"""
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(".1f"    return memory_mb

def benchmark_full_pipeline():
    """Benchmark full pipeline performance"""
    print("\n🏃 Testing full camera pipeline...")

    # Initialize components
    mp_holistic = mp.solutions.holistic
    holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    # Test with simulated frames (since we might not have camera in test env)
    processing_times = []

    for i in range(100):
        # Simulate camera frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        start = time.time()

        # Process frame
        results = holistic.process(frame_rgb)

        # Simulate cursor calculations
        if results.right_hand_landmarks:
            wrist = results.right_hand_landmarks.landmark[0]
            cursor_x = int(wrist.x * 1920)  # Assume 1920x1080 screen
            cursor_y = int(wrist.y * 1080)

        processing_times.append(time.time() - start)

    holistic.close()

    avg_time = sum(processing_times) / len(processing_times)
    avg_fps = 1.0 / avg_time

    print(".3f"    print(".1f"
    return avg_fps

def run_performance_tests():
    """Run all performance tests"""
    print("⚡ Camera Cursor System - Performance Benchmark")
    print("=" * 50)

    try:
        # Memory before
        mem_before = benchmark_memory()

        # Run tests
        mediapipe_fps = benchmark_mediapipe()
        pipeline_fps = benchmark_full_pipeline()

        # Memory after
        mem_after = benchmark_memory()

        print("\n" + "=" * 50)
        print("📊 Performance Results:")
        print(".1f"        print(".1f"        print(".1f"        print(".1f"
        print("\n✅ Performance test completed successfully!")

        # Recommendations
        if pipeline_fps >= 25:
            print("🎯 Excellent performance! System should run smoothly.")
        elif pipeline_fps >= 15:
            print("👍 Good performance. May experience minor lag in complex scenes.")
        else:
            print("⚠️  Performance may be limited. Consider reducing detection confidence or using faster hardware.")

        return True

    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

if __name__ == "__main__":
    success = run_performance_tests()
    exit(0 if success else 1)
