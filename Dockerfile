# Multi-stage build for Vision-to-Voice Assistant
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and other libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgthread-2.0-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Download smaller YOLO model for free tier (yolo11n instead of yolo11l)
RUN python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"

# Expose port for WebSocket server
EXPOSE 8765

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV USE_BROWSER_CAMERA=true
ENV YOLO_MODEL=yolo11n.pt
ENV USE_DEPTH_ESTIMATION=false

# Run the application
CMD ["python", "ui_server.py"]
