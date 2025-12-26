import time

import cv2


def get_frames(camera_index: int = 0):
    cap = cv2.VideoCapture(camera_index)
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

