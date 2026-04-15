import cv2
import mediapipe as mp
import time
import socket

# Setup socket for IntelliJ communication
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect(('localhost', 5005))
except:
    print("Java App not running. Printing to console instead.")

# MediaPipe modern setup
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# Global variables for tracking
neutral_y = None
calibration_frames = 0

def process_result(result, output_image, timestamp_ms):
    global neutral_y, calibration_frames
    
    if not result.pose_landmarks:
        return

    # Nose landmark (index 0)
    curr_y = result.pose_landmarks[0][0].y

    # Calibration Phase (First 50 frames)
    if calibration_frames < 50:
        if neutral_y is None: neutral_y = curr_y
        else: neutral_y = (neutral_y + curr_y) / 2
        calibration_frames += 1
        return

    # Detection Logic (0.15 is a proxy for 15cm relative to screen)
    status = "neutral"
    if curr_y > neutral_y + 0.15:
        status = "down"
    elif curr_y < neutral_y - 0.15:
        status = "up"

    # Send data to Java
    try:
        client_socket.sendall(f"{status}\n".encode())
    except:
        print(f"Status: {status}")

# Initialize Landmarker
options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='pose_landmarker_heavy.task'),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=process_result
)

with PoseLandmarker.create_from_options(options) as landmarker:
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        success, frame = cap.read()
        if not success: break

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        # Use system time for high-precision timestamping required by Tasks API
        timestamp = int(time.time() * 1000)
        landmarker.detect_async(mp_image, timestamp)

        cv2.imshow('MediaPipe Pose', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
