import cv2
import mediapipe as mp
import pyautogui
import numpy as np

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Get screen size
screen_width, screen_height = pyautogui.size()

# Open webcam
cap = cv2.VideoCapture(0)

# Variables for smoothing cursor movement
prev_x, prev_y = 0, 0
smoothing = 0.5

while cap.isOpened():
    success, img = cap.read()
    if not success:
        break

    # Flip image horizontally for natural movement
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get wrist position (landmark 0)
            wrist = hand_landmarks.landmark[0]
            h, w, _ = img.shape

            # Convert to screen coordinates
            x = int(wrist.x * screen_width)
            y = int(wrist.y * screen_height)

            # Smooth the movement
            x = int(prev_x + (x - prev_x) * smoothing)
            y = int(prev_y + (y - prev_y) * smoothing)

            # Move cursor
            pyautogui.moveTo(x, y)

            prev_x, prev_y = x, y

            # Simple click detection: if index finger tip is close to thumb tip
            index_tip = hand_landmarks.landmark[8]
            thumb_tip = hand_landmarks.landmark[4]

            distance = np.sqrt((index_tip.x - thumb_tip.x)**2 + (index_tip.y - thumb_tip.y)**2)
            if distance < 0.05:  # Threshold for click
                pyautogui.click()

    # Display image
    cv2.imshow('Camera Cursor Control', img)

    # Exit on 'q' press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
