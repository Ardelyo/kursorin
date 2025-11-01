import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import pygame
import tkinter as tk
from tkinter import messagebox
import time
import threading

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Get screen size
screen_width, screen_height = pyautogui.size()

# Pygame for effects
pygame.init()
effect_screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
pygame.display.set_caption("Cursor Effects")
clock = pygame.time.Clock()

# Cursor trail
trail_points = []
trail_color = (0, 255, 0)
trail_length = 20

# Modes
modes = ["normal", "browsing", "gaming", "typing"]
current_mode = "normal"

# Tkinter for popups (run in separate thread)
def show_popup(message, title="Cursor System"):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(title, message)
    root.destroy()

# Detect context (simple: check if cursor is over clickable areas)
def detect_context(x, y):
    # Placeholder: check screen content (would need OCR integration)
    # For now, just switch modes based on position
    if x < screen_width // 4:
        return "browsing"
    elif x > 3 * screen_width // 4:
        return "gaming"
    elif y > 3 * screen_height // 4:
        return "typing"
    else:
        return "normal"

# Open webcam
cap = cv2.VideoCapture(0)

# Variables for smoothing
prev_x, prev_y = 0, 0
smoothing = 0.5

# Click cooldown
last_click = 0
click_cooldown = 0.5

# Main loop
running = True
while running and cap.isOpened():
    success, img = cap.read()
    if not success:
        break

    # Flip image
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    cursor_x, cursor_y = prev_x, prev_y

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw landmarks
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get wrist position
            wrist = hand_landmarks.landmark[0]
            h, w, _ = img.shape

            # Convert to screen coordinates
            cursor_x = int(wrist.x * screen_width)
            cursor_y = int(wrist.y * screen_height)

            # Smooth
            cursor_x = int(prev_x + (cursor_x - prev_x) * smoothing)
            cursor_y = int(prev_y + (cursor_y - prev_y) * smoothing)

            # Detect new mode
            new_mode = detect_context(cursor_x, cursor_y)
            if new_mode != current_mode:
                current_mode = new_mode
                # Show popup in thread
                threading.Thread(target=show_popup, args=(f"Switched to {current_mode} mode")).start()

            # Click detection
            index_tip = hand_landmarks.landmark[8]
            thumb_tip = hand_landmarks.landmark[4]
            distance = np.sqrt((index_tip.x - thumb_tip.x)**2 + (index_tip.y - thumb_tip.y)**2)

            if distance < 0.05 and time.time() - last_click > click_cooldown:
                pyautogui.click()
                last_click = time.time()
                # Effect: flash screen
                effect_screen.fill((255, 255, 255))
                pygame.display.flip()
                pygame.time.wait(100)

    # Move cursor
    pyautogui.moveTo(cursor_x, cursor_y)
    prev_x, prev_y = cursor_x, cursor_y

    # Add to trail
    trail_points.append((cursor_x, cursor_y))
    if len(trail_points) > trail_length:
        trail_points.pop(0)

    # Pygame effects
    effect_screen.fill((0, 0, 0, 0))  # Transparent
    for i, point in enumerate(trail_points):
        alpha = int(255 * (i / len(trail_points)))
        pygame.draw.circle(effect_screen, trail_color + (alpha,), point, 5)
    pygame.display.update()

    # Display image
    cv2.putText(img, f"Mode: {current_mode}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow('Camera Cursor Control v2', img)

    # Handle pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        running = False

cap.release()
cv2.destroyAllWindows()
pygame.quit()
