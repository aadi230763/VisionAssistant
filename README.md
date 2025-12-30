# 🎯 Vision-to-Voice Assistant v3.0

An AI-powered assistive system that helps visually impaired users navigate their environment through real-time audio guidance with **depth-aware spatial intelligence** and **anticipatory navigation intelligence (ANI)**. Uses computer vision (YOLO), monocular depth estimation (MiDaS), temporal motion tracking, Google Vertex AI (Gemini), and ElevenLabs text-to-speech.

---

## 🌟 Features

- **Real-time Object Detection**: YOLO11s detects objects in camera feed
- **Depth-Aware Distance Estimation**: MiDaS provides relative distance (very close, close, moderate, far)
- **Spatial Intelligence**: Direction awareness (left, right, ahead)
- **🧠 Anticipatory Navigation Intelligence (ANI)**: 
  - Temporal object tracking with persistent IDs
  - Motion prediction (1.5s horizon)
  - Proactive risk assessment before collision
  - Motion classification (approaching, crossing, moving, stationary)
  - 5-level risk scoring (NONE, LOW, MEDIUM, HIGH, IMMINENT)
- **Smart AI Guidance**: Vertex AI (Gemini) provides actionable navigation instructions with distance and motion context
- **Emergency Warnings**: Automatic urgent alerts for very close hazards and imminent collision predictions
- **Natural Voice Output**: ElevenLabs TTS for high-quality speech
- **Intelligent Filtering**: Prevents repetitive notifications
- **Clean Terminal Output**: Color-coded emojis for easy monitoring
- **No API Keys in Code**: Secure authentication via Google Cloud ADC

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud account with billing enabled
- ElevenLabs API account
- Webcam
- 4GB RAM (8GB recommended for smooth depth estimation)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies include:**
- `opencv-python` - Video capture
- `ultralytics` - YOLO object detection
- `torch` & `torchvision` - Deep learning framework
- `timm` - PyTorch image models
- `requests` - HTTP requests
- `python-dotenv` - Environment variables
- `google-genai` - Vertex AI client

### 2. Set Up Google Cloud Authentication

```bash
# Install Google Cloud SDK
# Mac:
brew install google-cloud-sdk

# Windows:
winget install Google.CloudSDK

# Authenticate (creates local credentials)
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com
```

### 3. Configure Environment

Create a `.env` file (or copy from `.env.example`):

```env
# Vertex AI Configuration
VERTEX_PROJECT_ID=your-google-cloud-project-id
VERTEX_LOCATION=us-central1
VERTEX_MODEL=gemini-2.0-flash-exp

# ElevenLabs TTS Configuration
ELEVENLABS_API_KEY=your-elevenlabs-api-key
ELEVENLABS_VOICE_ID=your-elevenlabs-voice-id

# YOLO Configuration
YOLO_MODEL=yolo11s.pt
YOLO_CONF=0.35

# Depth Estimation (Spatial Awareness)
USE_DEPTH_ESTIMATION=true

# Anticipatory Navigation Intelligence (ANI) - Predictive Motion Tracking
USE_ANI=true
ANI_PREDICTION_HORIZON_S=1.5
ANI_MAX_TRACKING_DISTANCE=0.3
ANI_MAX_MISSED_FRAMES=5

# Frame Processing Settings
PROCESS_EVERY_N_FRAMES=15
DETECTION_SMOOTHING_WINDOW=3
DETECTION_SMOOTHING_MIN_HITS=2

# Narration Settings
NARRATION_COOLDOWN_S=3
FORCE_NARRATION_EVERY_S=0
```

### 4. Run the Application

```bash
python app.py
```

**Expected Output:**
```
============================================================
🎯 VISION-TO-VOICE ASSISTANT
============================================================

🔍 Initializing depth estimation...
✅ Depth estimation enabled
📹 Camera opened successfully

============================================================
📹 Frame 15
============================================================
  🟠 PERSON: 0.35 [close] → left
  🟡 CHAIR: 0.52 [moderate] → ahead

💬 AI: A person is nearby on your left. A chair is several steps ahead.
🔊 Speaking: A person is nearby on your left. A chair is several steps ahead.
```

---

## 🎓 How It Works

```
Camera → Depth → YOLO → Smoothing → Vertex AI → Filtering → ElevenLabs → Audio
  ↓       ↓       ↓         ↓           ↓            ↓            ↓
60fps   Depth   Objects  Stable    Distance-    Unique       Speech
        Map              Labels    Aware AI
```

### Enhanced Pipeline (with Depth):

1. **Camera Capture**: Continuous video stream from webcam (60fps)
2. **Depth Estimation**: MiDaS generates monocular depth map (every 15th frame)
3. **YOLO Detection**: Identifies objects with bounding boxes
4. **Depth Fusion**: Assigns distance (very_close/close/moderate/far) and direction (left/right/ahead) to each object
5. **Detection Smoothing**: 3-frame rolling window prevents false positives
6. **Vertex AI Processing**: Generates actionable, distance-aware navigation guidance
7. **Intelligent Filtering**: Removes duplicate/similar narrations
8. **Emergency Override**: Very close hazards bypass cooldown
9. **Text-to-Speech**: ElevenLabs converts to natural voice
10. **Audio Playback**: User hears spatial guidance through speakers

---

## 🔍 Depth Estimation Explained

### Distance Buckets

Objects are classified into **4 distance categories**:

| Depth Value | Bucket | Voice Description | Emoji |
|-------------|--------|-------------------|-------|
| 0.00 - 0.24 | **VERY_CLOSE** | "within arm's reach", "right beside you" | 🔴 |
| 0.25 - 0.44 | **CLOSE** | "a few steps away", "nearby" | 🟠 |
| 0.45 - 0.69 | **MODERATE** | "several steps ahead" | 🟡 |
| 0.70 - 1.00 | **FAR** | Background, not mentioned unless relevant | 🟢 |

### Direction Detection

Objects are positioned relative to camera center:
- **LEFT**: Object center < 40% of frame width
- **AHEAD**: Object center 40-60% of frame width  
- **RIGHT**: Object center > 60% of frame width

### Example Output

**Terminal:**
```
  🔴 PERSON: 0.18 [very_close] → ahead
```

**Voice:**
> "Warning. Person very close directly ahead. Stop immediately."

---

## 📁 Project Structure

```
vision/
├── app.py                  # Main orchestration loop with depth integration
├── vertex_ai.py           # Vertex AI integration (depth-aware prompts)
├── depth_estimator.py     # MiDaS depth estimation (NEW)
├── camera.py              # Video capture
├── yolo_detector.py       # Object detection with depth fusion
├── elevenlabs_tts.py      # Text-to-speech
├── decision_engine.py     # Narration filtering
├── test_depth.py          # Depth testing utility (NEW)
├── .env                   # Configuration (DO NOT COMMIT)
├── .env.example           # Configuration template
├── requirements.txt       # Python dependencies
├── yolo11s.pt            # YOLO model weights
├── README.md             # This file
├── DEPTH_IMPLEMENTATION.md  # Technical depth details (NEW)
├── DEPTH_VALUES_GUIDE.md    # Numerical depth guide (NEW)
└── OUTPUT_GUIDE.md          # Terminal output guide (NEW)
```

---

## 🎯 Key Features Explained

### 1. Depth-Aware Actionable Guidance

**Before Depth Enhancement:**
> "A person is ahead."

**After Depth Enhancement:**
> "A person is a few steps ahead on your left. Move slightly right to avoid them."

**Characteristics:**
- **Distance context**: "very close", "a few steps away", "several steps ahead"
- **Direction awareness**: left, right, ahead
- **Decisive instructions**: Provides specific guidance
- **Approximate language**: No fake precision, no exact meters
- **Calm and reassuring tone**

### 2. Emergency Interrupt System (Safety Override)

When **very close** hazards are detected:

**Terminal:**
```
🚨 URGENT: Very close hazard detected!
  🔴 CAR: 0.15 [very_close] → right
```

**Voice:**
> "Warning. Car very close on your right. Step back immediately."

**Triggered by:**
- Any object at VERY_CLOSE distance (< 0.25)
- Safety-relevant objects: person, vehicle, stairs, chair, etc.

**Behavior:**
- **Immediate interrupt** - Bypasses normal cooldown
- **Urgent but calm tone** - Firm without causing panic
- **Clear action command** - Stop, Step back, Move aside

### 3. Smart Deduplication

Prevents repetitive notifications:
- **Detection key comparison** (same objects = skip)
- **Text similarity check** (88% threshold)
- **Cooldown timer** (default: 3 seconds)
- **3-frame smoothing window** (reduces jitter)
- **Exception**: Very close hazards always trigger

### 4. Clean, Color-Coded Output

Terminal uses emojis for instant visual feedback:

```
============================================================
📹 Frame 30
============================================================
  🔴 PERSON: 0.18 [very_close] → ahead    ← URGENT!
  🟠 CHAIR: 0.35 [close] → left           ← Close
  🟡 TABLE: 0.55 [moderate] → right       ← Several steps
  🟢 WALL: 0.80 [far] → ahead             ← Background
```

---

## ⚙️ Configuration Guide

### Performance Tuning

**Faster Response (more CPU usage):**
```env
PROCESS_EVERY_N_FRAMES=10     # Process more frames
NARRATION_COOLDOWN_S=2        # Speak more often
```

**Battery Saving (slower response):**
```env
PROCESS_EVERY_N_FRAMES=30     # Process fewer frames
NARRATION_COOLDOWN_S=5        # Speak less often
```

**Disable Depth (faster processing):**
```env
USE_DEPTH_ESTIMATION=false
```

**More Stable Detection:**
```env
DETECTION_SMOOTHING_WINDOW=5
DETECTION_SMOOTHING_MIN_HITS=3
```

**More Sensitive Detection:**
```env
YOLO_CONF=0.25                # Lower confidence threshold
```

---

## 🧪 Testing Depth Estimation

### Run Depth Test Script

```bash
python test_depth.py
```

**Output:**
```
======================================================================
DEPTH ESTIMATION TEST
======================================================================
✅ Depth model loaded successfully

DETECTED OBJECTS WITH DEPTH
======================================================================
Object          Conf   Depth    Bucket       Direction 
----------------------------------------------------------------------
person          0.87   0.3469   close        ahead     
chair           0.92   0.5124   moderate     left      
clock           0.78   0.1234   very_close   right     
```

### Verify Depth is Working

1. **Move object closer to camera**
   - Watch depth value decrease: 0.75 → 0.50 → 0.25 → 0.10
   - Watch emoji change: 🟢 → 🟡 → 🟠 → 🔴

2. **Check for URGENT alerts**
   - Get very close to camera
   - Should see: `🚨 URGENT: Very close hazard detected!`

3. **Monitor numerical values**
   - Terminal shows: `🔴 PERSON: 0.18 [very_close] → ahead`
   - Value 0.18 is real depth from MiDaS, not hardcoded!

---

## 🐛 Troubleshooting

### Depth Estimation Issues

**Issue: "depth estimation failed"**
**Solutions**:
1. Check if `timm` is installed: `pip install timm`
2. Verify PyTorch is installed: `pip install torch torchvision`
3. Check available RAM (depth needs ~2-3GB)
4. Disable depth: `USE_DEPTH_ESTIMATION=false`

**Issue: Slow performance with depth**
**Solutions**:
1. Increase `PROCESS_EVERY_N_FRAMES=30`
2. Use smaller YOLO model: `YOLO_MODEL=yolo11n.pt`
3. Close other applications
4. Consider GPU acceleration (if available)

### General Issues

**Issue: "VERTEX_PROJECT_ID is not set"**
**Solution**: Check `.env` file exists and contains your project ID

**Issue: "404 NOT_FOUND" from Vertex AI**
**Solution**:
```bash
gcloud services enable aiplatform.googleapis.com
```

**Issue: "No module named 'ultralytics'"**
**Solution**:
```bash
pip install -r requirements.txt
```

**Issue: Camera won't open**
**Solutions**:
- Check camera permissions
- Close other apps using camera (Zoom, Skype, etc.)
- Try `CAMERA_INDEX=1` in code if multiple cameras

**Issue: No audio output**
**Solutions**:
- Verify `ELEVENLABS_API_KEY` is correct
- Check system volume
- Test audio: `afplay alert.mp3` (Mac) or `start alert.mp3` (Windows)

**Issue: Cluttered terminal output**
**Solution**: Output is already cleaned up! See `OUTPUT_GUIDE.md` for details

---

## 📊 Performance Metrics

- **Frame Processing**: Every 15th frame by default (~1 FPS)
- **YOLO Inference**: ~50-100ms per frame
- **Depth Estimation**: ~100-200ms per frame (CPU)
- **Vertex AI Response**: ~500-1000ms
- **TTS Generation**: ~1-2 seconds
- **Total Latency**: 3-5 seconds (detection to audio)
- **Memory Usage**: ~3-4GB RAM (with depth)

**Hardware Recommendations:**
- **Minimum**: 4GB RAM, dual-core CPU
- **Recommended**: 8GB RAM, quad-core CPU
- **Optional**: NVIDIA GPU for faster depth estimation

---

## 🔒 Security Best Practices

### Before Pushing to Git:

1. **Verify `.gitignore` includes:**
```
.env
alert.mp3
__pycache__/
venv/
*.pyc
.DS_Store
```

2. **Never commit:**
- `.env` file with API keys
- ADC credentials (stored by gcloud)
- `alert.mp3` (generated audio)
- Model cache files

3. **Safe to commit:**
- `.env.example` (template)
- All Python source files
- `requirements.txt`
- Documentation files
- Model weights (if small enough)

---

## 🏆 Technology Stack

- **AI Model**: Google Gemini 2.0 Flash (via Vertex AI)
- **Object Detection**: YOLO11s (Ultralytics)
- **Depth Estimation**: MiDaS Small (Intel ISL)
- **Text-to-Speech**: ElevenLabs
- **Computer Vision**: OpenCV
- **Deep Learning**: PyTorch
- **Authentication**: Google Cloud ADC
- **Language**: Python 3.11+

---

## 📈 Roadmap

**Implemented ✅**
- ✅ YOLO object detection
- ✅ Vertex AI integration
- ✅ ElevenLabs TTS
- ✅ Depth estimation (MiDaS)
- ✅ Distance buckets
- ✅ Direction awareness
- ✅ Emergency override
- ✅ Clean terminal output

**Future Enhancements 🚧**
- 🚧 Obstacle avoidance path planning
- 🚧 Indoor/outdoor scene classification
- 🚧 Stair detection enhancement
- 🚧 Mobile app version
- 🚧 Multi-language support
- 🚧 Offline mode (local models)

---

## 💡 Tips for Best Results

1. **Good Lighting**: Ensures better YOLO and depth accuracy
2. **Stable Camera**: Mount camera or use steady posture
3. **Clear Environment**: Start in open spaces for testing
4. **Volume**: Adjust system volume comfortably
5. **Cooldown**: Increase `NARRATION_COOLDOWN_S` if too chatty
6. **Move Slowly**: Give system time to process and respond
7. **Test First**: Use `test_depth.py` to verify setup

---

## 📚 Additional Documentation

- **[DEPTH_IMPLEMENTATION.md](DEPTH_IMPLEMENTATION.md)** - Technical depth implementation details
- **[DEPTH_VALUES_GUIDE.md](DEPTH_VALUES_GUIDE.md)** - Understanding numerical depth values
- **[OUTPUT_GUIDE.md](OUTPUT_GUIDE.md)** - Terminal output interpretation

---

## 🙏 Acknowledgments

- **Google Cloud**: Vertex AI and Gemini models
- **Intel ISL**: MiDaS depth estimation model
- **Ultralytics**: YOLO object detection
- **ElevenLabs**: Natural text-to-speech
- **OpenCV**: Computer vision library
- **PyTorch**: Deep learning framework

---

## 📄 License

This project is for educational and assistive technology purposes.

---

## 📞 Support

For issues or questions:

1. **Check Documentation**:
   - README.md (this file)
   - DEPTH_VALUES_GUIDE.md
   - OUTPUT_GUIDE.md

2. **Run Tests**:
   ```bash
   python test_depth.py
   ```

3. **Verify Configuration**:
   - Check `.env` file
   - Test authentication: `gcloud auth list`
   - Test imports: `python -c "import cv2, torch, ultralytics; print('OK')"`

4. **Common Fixes**:
   - Reinstall dependencies: `pip install -r requirements.txt`
   - Clear cache: Delete `~/.cache/torch/hub` and restart
   - Check logs: Look for error messages in terminal

---

**Status**: Production Ready (with Depth Estimation)  
**Version**: 2.0  
**Last Updated**: December 30, 2025

**New in v2.0:**
- ✨ Monocular depth estimation (MiDaS)
- ✨ Distance-aware guidance (very close, close, moderate, far)
- ✨ Direction detection (left, right, ahead)
- ✨ Emergency safety override for very close hazards
- ✨ Clean, color-coded terminal output
- ✨ Comprehensive depth testing utilities

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud account with billing enabled
- ElevenLabs API account
- Webcam

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google Cloud Authentication

```bash
# Install Google Cloud SDK
# Windows:
winget install Google.CloudSDK

# Mac:
brew install google-cloud-sdk

# Authenticate (creates local credentials)
gcloud auth application-default login

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com
```

### 3. Configure Environment

Create a `.env` file:

```env
# Google Cloud Vertex AI
VERTEX_PROJECT_ID=your-google-cloud-project-id
VERTEX_LOCATION=us-central1
VERTEX_MODEL=gemini-2.0-flash-exp

# ElevenLabs TTS
ELEVENLABS_API_KEY=your-elevenlabs-api-key
ELEVENLABS_VOICE_ID=your-elevenlabs-voice-id

# YOLO Settings
YOLO_MODEL=yolo11n.pt
YOLO_CONF=0.35

# Performance Tuning
PROCESS_EVERY_N_FRAMES=15
NARRATION_COOLDOWN_S=3
DETECTION_SMOOTHING_WINDOW=3
DETECTION_SMOOTHING_MIN_HITS=2
```

### 4. Run the Application

```bash
python app.py
```

---

## 🎓 How It Works

```
Camera → YOLO Detection → Smoothing → Vertex AI → Filtering → ElevenLabs → Audio
  ↓          ↓               ↓            ↓           ↓            ↓
 60fps     15fps          Stable      Actionable   Unique      Speech
```

### Pipeline Stages:

1. **Camera Capture**: Continuous video stream from webcam
2. **YOLO Detection**: Identifies objects (people, chairs, vehicles, etc.)
3. **Detection Smoothing**: 3-frame rolling window prevents false positives
4. **Vertex AI Processing**: Generates actionable navigation guidance
5. **Intelligent Filtering**: Removes duplicate/similar narrations
6. **Text-to-Speech**: ElevenLabs converts to natural voice
7. **Audio Playback**: User hears guidance through speakers

---

## 🔐 Authentication: How Vertex AI Works

### On Your Machine:
1. Run `gcloud auth application-default login`
2. Browser opens → login with Google account
3. Credentials saved at: `~/.config/gcloud/application_default_credentials.json` (Mac/Linux) or `%APPDATA%\gcloud\...` (Windows)
4. **No API key needed in code!**

### On Other Machines:
Each user must:
1. Install Google Cloud SDK
2. Run `gcloud auth application-default login`
3. Set their own `VERTEX_PROJECT_ID` in `.env`

**Security**: Credentials are stored locally by gcloud, never committed to Git.

---

## 📁 Project Structure

```
vision/
├── app.py                  # Main orchestration loop
├── vertex_ai.py           # Vertex AI integration (primary AI)
├── camera.py              # Video capture
├── yolo_detector.py       # Object detection
├── elevenlabs_tts.py      # Text-to-speech
├── decision_engine.py     # Narration filtering
├── .env                   # Configuration (DO NOT COMMIT)
├── requirements.txt       # Python dependencies
└── yolo11n.pt            # YOLO model weights
```

---

## ⚙️ Configuration Guide

### Performance Tuning

**Faster Response (more CPU usage):**
```env
PROCESS_EVERY_N_FRAMES=10
NARRATION_COOLDOWN_S=2
```

**Battery Saving (slower response):**
```env
PROCESS_EVERY_N_FRAMES=30
NARRATION_COOLDOWN_S=5
```

**More Stable Detection:**
```env
DETECTION_SMOOTHING_WINDOW=5
DETECTION_SMOOTHING_MIN_HITS=3
```

**More Sensitive Detection:**
```env
YOLO_CONF=0.25
```

---

## 🎯 Key Features Explained

### 1. Actionable Guidance (Not Just Description)

**Standard Output:**
> "A person is ahead and a chair is to your left. Move one step right."

**Characteristics:**
- Uses directional language (left/right, ahead/behind)
- Provides distance estimates (one step, two steps)
- Gives decisive instructions (picks one direction)
- Calm and reassuring tone

### 2. Emergency Interrupt System

When vehicles or hazards are detected:

**Emergency Output:**
> "Warning. Vehicle approaching. Please stop immediately."

**Triggered by:**
- Cars, trucks, buses, motorcycles
- Bicycles
- Traffic lights/signs
- Moving hazards

**Behavior:**
- Immediate interrupt
- Urgent but calm tone
- Clear action command (Stop, Step back, Wait)

### 3. Smart Deduplication

Prevents repetitive notifications:
- Detection key comparison (same objects = skip)
- Text similarity check (88% threshold)
- Cooldown timer (default: 3 seconds)
- 3-frame smoothing window

---

## 🐛 Troubleshooting

### Issue: "VERTEX_PROJECT_ID is not set"
**Solution**: Check `.env` file exists and contains your project ID

### Issue: "404 NOT_FOUND" from Vertex AI
**Solution**: Enable the API
```bash
gcloud services enable aiplatform.googleapis.com
```

### Issue: "No module named 'ultralytics'"
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Camera won't open
**Solutions**:
- Check camera permissions
- Close other apps using the camera
- Try a different camera index in code

### Issue: No audio output
**Solutions**:
- Verify `ELEVENLABS_API_KEY` is set in `.env`
- Check that `alert.mp3` file is created
- Test your audio output device

---

## 📊 Performance Metrics

- **Frame Processing**: Every 15th frame by default
- **YOLO Inference**: ~50ms per frame
- **Vertex AI Response**: ~500-1000ms
- **TTS Generation**: ~1-2 seconds
- **Total Latency**: 3-5 seconds (detection to audio)

---

## 🔒 Security Best Practices

### Before Pushing to Git:

1. **Verify `.gitignore` includes:**
```
.env
alert.mp3
__pycache__/
venv/
*.pyc
```

2. **Never commit:**
- Your `.env` file with actual API keys
- ADC credentials (stored by gcloud, not in project)
- `alert.mp3` (generated audio file)

3. **Safe to commit:**
- `.env.example` (template without keys)
- All Python source files
- `requirements.txt`
- `yolo11n.pt` model weights

---

## 🎓 Model Options

### Current (Fast & Efficient):
```env
VERTEX_MODEL=gemini-2.0-flash-exp
```

### Alternative (Higher Quality):
```env
VERTEX_MODEL=gemini-1.5-pro
```

### Legacy:
```env
VERTEX_MODEL=gemini-1.5-flash
```

---

## 📝 Dependencies

```
opencv-python      # Video capture
ultralytics        # YOLO object detection
requests           # HTTP requests
python-dotenv      # Environment variable management
google-genai       # Vertex AI client
```

---

## 💡 Tips for Best Results

1. **Good Lighting**: Ensures better YOLO detection
2. **Stable Camera**: Mount camera or use steady hands
3. **Clear Environment**: Start in open spaces for testing
4. **Volume**: Adjust system volume for comfortable listening
5. **Cooldown**: Increase `NARRATION_COOLDOWN_S` if too chatty

---

## 🚀 Deployment Options

### Local Development:
```bash
python app.py
```

### Production Considerations:
- Consider using a service like Systemd (Linux) or Windows Service
- Add logging to file for debugging
- Monitor CPU/GPU usage
- Consider edge deployment (Raspberry Pi, Jetson Nano)

---

## 🏆 Technology Stack

- **AI Model**: Google Gemini 2.0 Flash (via Vertex AI)
- **Object Detection**: YOLO11n (Ultralytics)
- **Text-to-Speech**: ElevenLabs
- **Computer Vision**: OpenCV
- **Authentication**: Google Cloud ADC
- **Language**: Python 3.11+

---

## 📄 License

This project is for educational and assistive technology purposes.

---

## 🙏 Acknowledgments

- **Google Cloud**: Vertex AI and Gemini models
- **Ultralytics**: YOLO object detection
- **ElevenLabs**: Natural text-to-speech
- **OpenCV**: Computer vision library

---

## 📞 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Verify all prerequisites are installed
3. Ensure `.env` is properly configured
4. Test with `python -c "from vertex_ai import describe_scene; print('OK')"`

---

**Status**: Production Ready  
**Version**: 1.0  
**Last Updated**: December 2025
