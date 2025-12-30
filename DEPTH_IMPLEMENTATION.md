# Depth-Aware Distance Estimation Implementation

## ✅ Implementation Status: COMPLETE

The Vision-to-Voice Assistant now includes **Level 3 Depth Awareness** using monocular depth estimation, fully integrated without breaking the existing pipeline.

---

## 🏗️ Architecture Overview

### Existing Pipeline (Unchanged)
```
camera.py → yolo_detector.py → vertex_ai.py → decision_engine.py → elevenlabs_tts.py
```

### Enhanced Pipeline (With Depth)
```
camera.py 
  ↓
depth_estimator.py (parallel depth map generation)
  ↓
yolo_detector.py (YOLO + depth fusion)
  ↓
vertex_ai.py (depth-aware reasoning)
  ↓
decision_engine.py
  ↓
elevenlabs_tts.py
```

---

## 📦 Module Breakdown

### 1. **depth_estimator.py** (NEW MODULE)

#### Key Functions:

- **`initialize_depth_model(model_type)`**
  - Loads MiDaS Small model (lightweight, CPU-friendly)
  - One-time initialization at startup
  - Returns: `True` if successful, `False` otherwise

- **`estimate_depth(frame)`**
  - Accepts: BGR frame from OpenCV
  - Returns: Normalized depth map (0=close, 1=far)
  - Runs inference using MiDaS
  - Handles failures gracefully (returns `None`)

- **`compute_bbox_depth(depth_map, bbox)`**
  - Extracts depth values from bounding box region
  - Uses median (robust to outliers)
  - Returns: `(median_depth, distance_bucket)`

- **`get_distance_bucket(depth_value)`**
  - Converts normalized depth to human categories:
    - **VERY_CLOSE**: < 0.25 (within arm's reach)
    - **CLOSE**: 0.25 - 0.45 (a few steps away)
    - **MODERATE**: 0.45 - 0.70 (several steps away)
    - **FAR**: > 0.70 (not immediate concern)

- **`get_object_direction(bbox, frame_width)`**
  - Determines horizontal position: `left`, `right`, `ahead`
  - Uses 20% margin from center for thresholds

- **`is_safety_relevant(label)`**
  - Identifies critical objects: person, vehicle, stairs, etc.
  - Used for safety override logic

---

### 2. **yolo_detector.py** (MODIFIED)

#### Changes:

- **Added `depth_map` parameter** to `detect()` function
- **Extracts bounding box coordinates** for each detection
- **Calls depth functions** to compute:
  - `distance`: very_close / close / moderate / far
  - `direction`: left / right / ahead
  - `depth_value`: raw median depth (for debugging)
- **Returns enhanced detections** with depth info

#### Example Output:
```python
{
  "label": "person",
  "confidence": 0.92,
  "distance": "close",
  "direction": "left",
  "depth_value": 0.38
}
```

---

### 3. **vertex_ai.py** (MODIFIED)

#### Changes:

- **Updated `_format_detections()`** to include depth info:
  ```
  - Person (left, close)
  - Chair (ahead, very_close)
  - Car (right, moderate)
  ```

- **Added `_has_very_close_hazard()`** function:
  - Checks if any safety-relevant object is VERY_CLOSE
  - Triggers urgent response mode

- **Enhanced prompts** with distance guidance:
  - Explains distance categories to Gemini
  - Enforces approximate language (no exact meters)
  - Uses context-aware phrasing:
    - `very_close` → "very close", "within arm's reach"
    - `close` → "a few steps away", "nearby"
    - `moderate` → "several steps ahead"

#### Example Prompt Addition:
```
DISTANCE MEANINGS:
- very_close: Within arm's reach, immediate danger
- close: A few steps away
- moderate: Several steps away
- far: Not an immediate concern
```

---

### 4. **app.py** (MODIFIED)

#### Changes:

- **Depth initialization at startup**:
  ```python
  if use_depth:
      depth_enabled = initialize_depth_model("midas_small")
  ```

- **Depth estimation in `process_frame()`**:
  ```python
  depth_map = None
  if depth_enabled:
      depth_map = estimate_depth(frame)
  
  detections = detector.detect(frame, depth_map=depth_map)
  ```

- **Safety override for very close hazards**:
  ```python
  has_urgent_hazard = any(
      d.get("distance") == "very_close" 
      for d in stable_detections
  )
  ```
  - Bypasses cooldown logic for urgent situations
  - Always processes very close safety-relevant objects

---

## ⚙️ Configuration (.env)

```bash
# Enable/disable depth estimation
USE_DEPTH_ESTIMATION=true
```

---

## 🎯 Key Features

### ✅ Safety-First Design

1. **Emergency Override**
   - Very close hazards bypass all cooldown logic
   - Immediate narration for critical situations
   - Calm but urgent phrasing

2. **Safety-Relevant Objects**
   - person, car, truck, bus, motorcycle, bicycle
   - chair, couch, bench, stairs
   - traffic light, stop sign

### ✅ No Fake Precision

- **Never outputs exact distances** (no "3.2 meters")
- Uses **approximate, human-friendly language**:
  - "very close"
  - "a few steps away"
  - "right beside you"
  - "within arm's reach"

### ✅ Performance & Reliability

- **Asynchronous processing** (non-blocking)
- **Graceful degradation**: Falls back if depth fails
- **Minimal overhead**: Depth runs only on processed frames (every 15th frame)
- **Cached depth maps** per frame

### ✅ Spatial Intelligence

- **Direction awareness**: left, right, ahead
- **Distance awareness**: very close, close, moderate, far
- **Context-aware guidance**:
  - "A person is a few steps ahead on the left. Move slightly right."
  - "There is a chair very close on your left. Please stop and step right."

---

## 📊 Example Narrations

### Before Depth (Object Detection Only):
❌ "A person is nearby."

### After Depth (Spatial Awareness):
✅ "A person is a few steps ahead on the left. Move slightly right."

---

### Before Depth:
❌ "There is a chair."

### After Depth:
✅ "Warning. Chair very close on your left. Step back."

---

## 🔍 Debug Logging

Minimal logging for development:

```
[depth] Loading midas_small model...
[depth] Model loaded successfully on cpu
[depth] person → VERY_CLOSE
[depth] chair → CLOSE
[app] URGENT: Very close hazard detected
```

---

## 🧪 Testing

### Verify Depth is Working:
1. Start the app: `python app.py`
2. Look for: `[app] Depth estimation enabled`
3. Move close to objects
4. Listen for distance-aware narrations

### Expected Behavior:
- Objects very close trigger urgent warnings
- Narrations include direction (left/right/ahead)
- Language is approximate and natural
- No exact distance numbers

---

## 📦 Dependencies

Added to `requirements.txt`:
```
torch
torchvision
```

MiDaS model is downloaded automatically via PyTorch Hub on first run.

---

## 🚫 What Was NOT Changed

- ✅ YOLO detection logic (unchanged)
- ✅ Vertex AI integration (only prompt enhanced)
- ✅ ElevenLabs TTS (unchanged)
- ✅ Narration cooldown logic (except safety override)
- ✅ Threading architecture (unchanged)
- ✅ Decision engine (unchanged)
- ✅ Camera capture (unchanged)

---

## 🎓 Technical Details

### Depth Model: MiDaS Small
- **Architecture**: Monocular depth estimation
- **Input**: Single RGB frame
- **Output**: Relative depth map
- **Accuracy**: Scene-consistent, not metrically accurate
- **Performance**: ~50-100ms per frame on CPU

### Distance Buckets (Normalized 0-1):
```python
VERY_CLOSE_THRESHOLD = 0.25  # < 0.25
CLOSE_THRESHOLD = 0.45       # 0.25 - 0.45
MODERATE_THRESHOLD = 0.70    # 0.45 - 0.70
# FAR                         # > 0.70
```

### Direction Thresholds:
```python
LEFT:   center_x < 40% of frame width
RIGHT:  center_x > 60% of frame width
AHEAD:  40% <= center_x <= 60%
```

---

## ✅ Compliance Checklist

- ✅ Level 3 depth awareness implemented
- ✅ Monocular depth estimation (MiDaS)
- ✅ Distance buckets (very_close, close, moderate, far)
- ✅ Direction awareness (left, right, ahead)
- ✅ Safety override for very close hazards
- ✅ No fake precision (no exact meters)
- ✅ Approximate, human-friendly language
- ✅ Graceful failure handling
- ✅ Non-blocking, asynchronous processing
- ✅ Minimal logging
- ✅ No UI changes
- ✅ No refactoring of existing code
- ✅ Fully compatible with ElevenLabs + Vertex AI

---

## 🎉 Result

The Vision-to-Voice Assistant now understands **proximity**, not just **presence**.

**Example:**
- Old: "There is a person."
- **New: "A person is very close on your right. Step left."**

This makes the system **significantly more intelligent** and **safer** for visually impaired users.

---

## 🔧 Maintenance Notes

- Depth model loads once at startup (~2-5 seconds)
- Model cached in `~/.cache/torch/hub/intel-isl_MiDaS_master/`
- To disable: Set `USE_DEPTH_ESTIMATION=false` in `.env`
- To test without depth: App falls back gracefully if model fails
