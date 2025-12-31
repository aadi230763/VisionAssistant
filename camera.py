import time
import os
import cv2


def get_frames(camera_index: int = 0):
    """
    Get frames from camera or demo video file.
    Set USE_DEMO_VIDEO=true environment variable to use demo video for cloud deployment.
    """
    use_demo = os.getenv("USE_DEMO_VIDEO", "false").lower() == "true"
    demo_video_path = os.getenv("DEMO_VIDEO_PATH", "data/demo_video.mp4")
    
    if use_demo and os.path.exists(demo_video_path):
        print(f"📹 Using demo video: {demo_video_path}")
        cap = cv2.VideoCapture(demo_video_path)
        if not cap.isOpened():
            print(f"❌ Failed to open demo video {demo_video_path}")
            return
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    # Loop the video
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                yield frame
                time.sleep(0.033)  # ~30 FPS
        except KeyboardInterrupt:
            return
        finally:
            cap.release()
    else:
        # Live camera mode
        cap = None
        for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
            cap = cv2.VideoCapture(camera_index, backend)
            if cap.isOpened():
                print(f"📹 Camera opened successfully\\n")
                break
        
        if cap is None or not cap.isOpened():
            print(f"❌ Failed to open camera {camera_index}")
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

