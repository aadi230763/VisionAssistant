# 🎯 Vision-to-Voice Assistant

An AI-powered assistive system that helps visually impaired users navigate their environment through real-time audio guidance. Uses computer vision (YOLO), Google Vertex AI (Gemini), and ElevenLabs text-to-speech.

---

## 🌟 Features

- **Real-time Object Detection**: YOLO11n detects objects in camera feed
- **Smart AI Guidance**: Vertex AI (Gemini) provides actionable navigation instructions
- **Emergency Warnings**: Automatic urgent alerts for vehicles and hazards
- **Natural Voice Output**: ElevenLabs TTS for high-quality speech
- **Intelligent Filtering**: Prevents repetitive notifications
- **No API Keys in Code**: Secure authentication via Google Cloud ADC

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
