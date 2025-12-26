import os
import queue
import threading
import time
import re
from collections import Counter, deque
from concurrent.futures import Future, ThreadPoolExecutor
from difflib import SequenceMatcher

from dotenv import load_dotenv

from camera import get_frames
from elevenlabs_tts import speak
from groq_ai import describe_scene
from yolo_detector import YoloDetector

load_dotenv()


def _tts_worker(stop_event: threading.Event, tts_queue: "queue.Queue[str]"):
    last_spoken_text: str | None = None
    last_spoken_ts: float = 0.0
    cooldown_s = float(os.getenv("NARRATION_COOLDOWN_S", "3"))

    def _normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _is_similar(a: str, b: str) -> bool:
        na, nb = _normalize(a), _normalize(b)
        if not na or not nb:
            return False
        if na == nb:
            return True
        ratio = SequenceMatcher(None, na, nb).ratio()
        if ratio >= 0.88:
            return True
        sa, sb = set(na.split()), set(nb.split())
        if sa and sb:
            jacc = len(sa & sb) / max(1, len(sa | sb))
            if jacc >= 0.8:
                return True
        return False

    while not stop_event.is_set():
        try:
            text = tts_queue.get(timeout=0.25)
        except queue.Empty:
            continue

        if text is None:  # sentinel
            return

        try:
            now = time.time()
            if cooldown_s > 0 and (now - last_spoken_ts) < cooldown_s:
                print("[tts] cooldown active; skipping")
                continue

            if last_spoken_text and _is_similar(text, last_spoken_text):
                print("[tts] similar to last narration; skipping")
                continue

            print(f"[tts] speaking: {text}")
            speak(text)
            last_spoken_text = text
            last_spoken_ts = now
        except Exception as exc:
            print(f"[tts] error: {exc}")


def main():
    print("[app] Vision-to-Voice Assistant started")

    process_every_n_frames = int(os.getenv("PROCESS_EVERY_N_FRAMES", "15"))
    yolo_model = os.getenv("YOLO_MODEL", "yolo11n.pt")
    yolo_conf = float(os.getenv("YOLO_CONF", "0.35"))

    detector = YoloDetector(model=yolo_model, conf=yolo_conf)

    smoothing_window = int(os.getenv("DETECTION_SMOOTHING_WINDOW", "3"))
    smoothing_min_hits = int(os.getenv("DETECTION_SMOOTHING_MIN_HITS", "2"))
    recent_label_sets: "deque[set[str]]" = deque(maxlen=max(1, smoothing_window))

    force_narration_every_s = float(os.getenv("FORCE_NARRATION_EVERY_S", "0"))
    last_groq_ts: float = 0.0

    stop_event = threading.Event()
    tts_queue: "queue.Queue[str]" = queue.Queue(maxsize=2)
    tts_thread = threading.Thread(target=_tts_worker, args=(stop_event, tts_queue), daemon=True)
    tts_thread.start()

    cooldown_s = float(os.getenv("NARRATION_COOLDOWN_S", "3"))
    last_enqueue_ts: float = 0.0
    last_enqueued_text: str | None = None
    last_enqueued_detection_key: tuple | None = None

    def _normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _is_similar(a: str, b: str) -> bool:
        na, nb = _normalize(a), _normalize(b)
        if not na or not nb:
            return False
        if na == nb:
            return True
        ratio = SequenceMatcher(None, na, nb).ratio()
        if ratio >= 0.88:
            return True
        sa, sb = set(na.split()), set(nb.split())
        if sa and sb:
            jacc = len(sa & sb) / max(1, len(sa | sb))
            if jacc >= 0.8:
                return True
        return False

    last_detection_key_lock = threading.Lock()
    last_detection_key: tuple | None = None

    def process_frame(frame) -> str | None:
        nonlocal last_detection_key
        nonlocal last_groq_ts

        detections = detector.detect(frame)
        if not detections:
            print("[yolo] no detections")
            recent_label_sets.append(set())
            return None

        labels_now = {d["label"] for d in detections}
        recent_label_sets.append(labels_now)

        # Smooth labels over a short rolling window to avoid false-positive jitter.
        counts: Counter[str] = Counter()
        for s in recent_label_sets:
            counts.update(s)

        stable_labels = {label for label, c in counts.items() if c >= smoothing_min_hits}
        if not stable_labels:
            print("[yolo] no stable detections")
            return None

        stable_detections = [d for d in detections if d["label"] in stable_labels]

        # Treat "unchanged" as same stabilized labels (ignore confidence jitter)
        detection_key = tuple(sorted(stable_labels))

        with last_detection_key_lock:
            if last_detection_key == detection_key:
                if force_narration_every_s > 0 and (time.time() - last_groq_ts) >= force_narration_every_s:
                    pass
                else:
                    print("[app] detections unchanged; skipping Groq")
                    return None

        text = describe_scene(stable_detections)
        if not text:
            return None

        with last_detection_key_lock:
            last_detection_key = detection_key

        last_groq_ts = time.time()

        return text

    executor = ThreadPoolExecutor(max_workers=1)
    pending: Future | None = None

    frame_idx = 0
    try:
        for frame in get_frames():
            frame_idx += 1

            if frame_idx % process_every_n_frames != 0:
                continue

            if pending is not None and not pending.done():
                continue

            print(f"[app] processing frame {frame_idx}")
            pending = executor.submit(process_frame, frame.copy())

            if pending.done():
                # extremely rare, but handle immediate completion
                text = pending.result()
                if text:
                    now = time.time()
                    if cooldown_s > 0 and (now - last_enqueue_ts) < cooldown_s:
                        continue
                    # If detections are effectively the same, don't enqueue near-duplicate narration
                    with last_detection_key_lock:
                        current_key = last_detection_key
                    if (
                        last_enqueued_text
                        and current_key is not None
                        and last_enqueued_detection_key == current_key
                        and _is_similar(text, last_enqueued_text)
                    ):
                        continue
                    if not tts_queue.full():
                        tts_queue.put_nowait(text)
                        last_enqueue_ts = now
                        last_enqueued_text = text
                        last_enqueued_detection_key = current_key

            else:
                # attach callback to enqueue narration when ready
                def _on_done(fut: Future):
                    try:
                        text = fut.result()
                    except Exception as exc:
                        print(f"[app] processing error: {exc}")
                        return
                    if not text:
                        return

                    nonlocal last_enqueue_ts, last_enqueued_text, last_enqueued_detection_key
                    now = time.time()
                    if cooldown_s > 0 and (now - last_enqueue_ts) < cooldown_s:
                        return

                    with last_detection_key_lock:
                        current_key = last_detection_key

                    if (
                        last_enqueued_text
                        and current_key is not None
                        and last_enqueued_detection_key == current_key
                        and _is_similar(text, last_enqueued_text)
                    ):
                        return

                    if tts_queue.full():
                        return

                    tts_queue.put_nowait(text)
                    last_enqueue_ts = now
                    last_enqueued_text = text
                    last_enqueued_detection_key = current_key
                    print(f"[groq] {text}")

                pending.add_done_callback(_on_done)

    except KeyboardInterrupt:
        print("[app] stopping...")
    finally:
        stop_event.set()
        try:
            tts_queue.put_nowait(None)
        except queue.Full:
            pass
        executor.shutdown(wait=False, cancel_futures=True)
        tts_thread.join(timeout=2)


if __name__ == "__main__":
    main()

