# Finger Gesture Virtual Mouse

A Python virtual mouse that uses your webcam and MediaPipe hand tracking to control the cursor with simple finger gestures.

The app detects one hand, counts raised fingers, draws a hand skeleton on the camera feed, and maps gestures to mouse actions such as move, left click, right click, double click, and screenshot.

## Features

- Move the mouse using an open hand
- Left click, right click, and double click with finger gestures
- Take screenshots with a closed fist
- Live webcam preview with hand landmark drawing
- Basic cursor smoothing to reduce shaky movement
- Gesture cooldowns to prevent repeated accidental clicks

## Gesture Controls

| Gesture | Action |
| --- | --- |
| 5 fingers up | Move mouse |
| Only index finger up | Left click |
| Index + middle fingers up | Right click |
| Index + middle + ring fingers up | Double click |
| Closed fist | Save screenshot |

Screenshots are saved in the project folder as `screenshot_<timestamp>.png`.

## Project Structure

```text
.
|-- camera.py                # Main virtual mouse application
|-- util.py                  # Helper functions for angle and distance calculations
|-- hand_landmarker.task     # MediaPipe hand landmark model
`-- README.md
```

## Requirements

- Python 3.10 or newer
- A working webcam
- The included `hand_landmarker.task` model file

Python packages:

```text
opencv-python
mediapipe
pyautogui
pynput
numpy
```

## Setup

1. Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install opencv-python mediapipe pyautogui pynput numpy
```

3. Make sure `hand_landmarker.task` is in the same folder as `camera.py`.

## Run

```powershell
python camera.py
```

Press `q` in the camera window to quit.

## How It Works

`camera.py` opens the webcam with OpenCV, flips the frame for a mirror-like view, and passes each frame to MediaPipe's hand landmarker model. The detected hand landmarks are used to count which fingers are raised.

The recognized gesture is then converted into a mouse action with `pyautogui` and `pynput`.

## Troubleshooting

- If the camera does not open, check that no other app is using the webcam.
- If MediaPipe cannot find the model, confirm that `hand_landmarker.task` is in the project root.
- If clicks trigger too often, increase `cooldown_frames` or `min_gesture_interval` in `camera.py`.
- If the cursor movement feels jumpy, increase the `position_buffer` size in `camera.py`.
- On some systems, mouse automation may require accessibility or input-control permissions.

## Notes

This project currently tracks one hand only. Gesture detection is based on finger counting, so results may vary depending on lighting, camera angle, hand orientation, and background.
