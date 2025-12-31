# Multi-stage build for Vision-to-Voice Assistant
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Download YOLO model (so it doesn't download on every start)
RUN python -c "from ultralytics import YOLO; YOLO('yolo11l.pt')"

# Expose port for WebSocket server
EXPOSE 8765

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV USE_BROWSER_CAMERA=true

# Run the application
CMD ["python", "ui_server.py"]
