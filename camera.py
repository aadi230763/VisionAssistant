import time

import cv2


def get_frames(camera_index: int = 0):
    # Try multiple camera backends
    cap = None
    for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
        cap = cv2.VideoCapture(camera_index, backend)
        if cap.isOpened():
            print(f"[camera] opened with backend {backend}")
            break
    
    if cap is None or not cap.isOpened():
        print(f"[camera] failed to open camera {camera_index}")
        return
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[camera] frame read failed; retrying...")
                time.sleep(0.1)
                continue
            yield frame
    except KeyboardInterrupt:
        return
    finally:
        cap.release()

