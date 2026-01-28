import cv2
import mediapipe as mp
import pyautogui
import time
from pynput.mouse import Button, Controller
from collections import deque

mouse = Controller()
screen_width, screen_height = pyautogui.size()

# ------------------- Mediapipe Setup -------------------
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="hand_landmarker.task"),
    running_mode=VisionRunningMode.VIDEO,
    num_hands=1
)
hands = HandLandmarker.create_from_options(options)

HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(0,17),(17,18),(18,19),(19,20)
]

# ------------------- State Variables -------------------
position_buffer = deque(maxlen=5)
gesture_cooldown = 0
cooldown_frames = 20
last_gesture_time = 0
min_gesture_interval = 0.5

# ------------------- Finger Detection -------------------
def count_fingers(hand_landmarks):
    """Count extended fingers"""
    if not hand_landmarks:
        return 0
    
    fingers_up = []
    
    # Thumb (check x-coordinate for left/right)
    if hand_landmarks[4].x < hand_landmarks[3].x:  # Thumb
        fingers_up.append(1)
    else:
        fingers_up.append(0)
    
    # Other 4 fingers (check y-coordinate)
    finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky tips
    finger_pips = [6, 10, 14, 18]  # Corresponding PIP joints
    
    for tip, pip in zip(finger_tips, finger_pips):
        if hand_landmarks[tip].y < hand_landmarks[pip].y:  # Tip above PIP = finger up
            fingers_up.append(1)
        else:
            fingers_up.append(0)
    
    return fingers_up

def get_gesture_name(fingers_up):
    """Determine gesture from finger count"""
    total = sum(fingers_up)
    
    # All 5 fingers up
    if total == 5:
        return "MOVE"
    
    # Only index finger up (thumb down, index up, others down)
    elif fingers_up == [0, 1, 0, 0, 0]:
        return "LEFT_CLICK"
    
    # Index + Middle up (peace sign)
    elif fingers_up == [0, 1, 1, 0, 0]:
        return "RIGHT_CLICK"
    
    # Index + Middle + Ring up (three fingers)
    elif fingers_up == [0, 1, 1, 1, 0]:
        return "DOUBLE_CLICK"
    
    # Closed fist (all fingers down)
    elif total == 0:
        return "SCREENSHOT"
    
    return "NONE"

# ------------------- Mouse Control -------------------
def move_mouse_smooth(index_finger_tip):
    """Smooth mouse movement"""
    if index_finger_tip:
        x = int(index_finger_tip.x * screen_width)
        y = int(index_finger_tip.y * screen_height)
        
        position_buffer.append((x, y))
        
        if len(position_buffer) > 0:
            avg_x = sum([pos[0] for pos in position_buffer]) // len(position_buffer)
            avg_y = sum([pos[1] for pos in position_buffer]) // len(position_buffer)
            
            current_x, current_y = pyautogui.position()
            distance = ((avg_x - current_x)**2 + (avg_y - current_y)**2)**0.5
            
            if distance > 5:
                pyautogui.moveTo(avg_x, avg_y, duration=0)

def execute_gesture(gesture, frame, hand_landmarks):
    """Execute action based on gesture"""
    global gesture_cooldown, last_gesture_time
    
    current_time = time.time()
    
    # Move mouse (no cooldown needed)
    if gesture == "MOVE":
        index_finger_tip = hand_landmarks[8]
        move_mouse_smooth(index_finger_tip)
        cv2.putText(frame, "Moving Mouse", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return
    
    # Check cooldown for click gestures
    if gesture_cooldown > 0:
        gesture_cooldown -= 1
        return
    
    if current_time - last_gesture_time < min_gesture_interval:
        return
    
    # Execute click gestures
    if gesture == "LEFT_CLICK":
        mouse.click(Button.left)
        cv2.putText(frame, "LEFT CLICK", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        gesture_cooldown = cooldown_frames
        last_gesture_time = current_time
        
    elif gesture == "RIGHT_CLICK":
        mouse.click(Button.right)
        cv2.putText(frame, "RIGHT CLICK", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        gesture_cooldown = cooldown_frames
        last_gesture_time = current_time
        
    elif gesture == "DOUBLE_CLICK":
        pyautogui.doubleClick()
        cv2.putText(frame, "DOUBLE CLICK", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        gesture_cooldown = cooldown_frames
        last_gesture_time = current_time
        
    elif gesture == "SCREENSHOT":
        timestamp = int(time.time())
        filename = f'screenshot_{timestamp}.png'
        pyautogui.screenshot(filename)
        cv2.putText(frame, f"SCREENSHOT: {filename}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        gesture_cooldown = cooldown_frames
        last_gesture_time = current_time
        print(f"Screenshot saved: {filename}")

# ------------------- Main Loop -------------------
def main():
    cap = cv2.VideoCapture(0)
    frame_count = 0
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("=" * 50)
    print("🖱️  EASY VIRTUAL MOUSE - FINGER COUNTING")
    print("=" * 50)
    print("✋ 5 Fingers UP      → Move Mouse")
    print("👆 Only Index UP     → Left Click")
    print("✌️  Index + Middle   → Right Click")
    print("🤟 Three Fingers UP  → Double Click")
    print("✊ Closed Fist       → Screenshot")
    print("=" * 50)
    print("Press 'q' to quit\n")

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame = cv2.flip(frame, 1)
            frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            timestamp_ms = frame_count * 33
            frame_count += 1
            
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frameRGB)
            hand_result = hands.detect_for_video(mp_image, timestamp_ms=timestamp_ms)

            if hand_result.hand_landmarks:
                hand_landmarks = hand_result.hand_landmarks[0]
                
                # Draw hand skeleton
                for start_idx, end_idx in HAND_CONNECTIONS:
                    x1 = int(hand_landmarks[start_idx].x * frame.shape[1])
                    y1 = int(hand_landmarks[start_idx].y * frame.shape[0])
                    x2 = int(hand_landmarks[end_idx].x * frame.shape[1])
                    y2 = int(hand_landmarks[end_idx].y * frame.shape[0])
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Count fingers and detect gesture
                fingers_up = count_fingers(hand_landmarks)
                gesture = get_gesture_name(fingers_up)
                
                # Display finger count
                finger_count = sum(fingers_up)
                cv2.putText(frame, f"Fingers: {finger_count}", (frame.shape[1] - 200, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                # Execute gesture
                execute_gesture(gesture, frame, hand_landmarks)
                
            else:
                position_buffer.clear()
                cv2.putText(frame, "No Hand Detected", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            cv2.imshow('Easy Virtual Mouse', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("\n✅ Virtual Mouse Stopped!")

if __name__ == '__main__':
    main()


## ✨ **METHOD 2: Even Simpler (Thumb-Based)**

##If Method 1 is still hard, try this **super simple** version:
##```
##👍 THUMB UP              → Move Mouse
##👎 THUMB DOWN            → Left Click
##👍 + ✌️ (Thumb + Peace)  → Right Click
##✊ FIST                  → Screenshot


## ✨ **METHOD 3: Single Hand Palm Control**
##```
##🖐️ OPEN PALM (5 fingers) → Move Mouse
##👊 FIST (0 fingers)      → Left Click
##✌️ PEACE (2 fingers)     → Right Click
##🤘 ROCK (2 different)    → Screenshot