#!/bin/bash

echo "📌 Starting Tube Detector System..."

# 1. Prepare dataset
echo "📥 Preparing dataset..."
python3 prepare_dataset.py

# 2. Train YOLO (if not already trained)
echo "🎯 Training YOLO model..."
python3 train_yolo.py

# 3. Export TFLite model for Raspberry Pi
echo "🔄 Exporting YOLO to TFLite..."
bash export_tflite.sh

# 4. Start FastAPI server
echo "🚀 Launching FastAPI server..."
uvicorn fastapi_server:app --host 0.0.0.0 --port 8000 &

# 5. Start Raspberry Pi TFLite live detection script
echo "🛰️ Starting detection module..."
python3 pi_tflite_detect.py

echo "✔️ All modules started successfully!"
