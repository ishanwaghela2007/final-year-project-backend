@echo off
echo 📌 Starting Tube Detector System...

echo 📥 Preparing dataset...
python prepare_dataset.py

echo 🎯 Training YOLO...
python train_yolo.py

echo 🔄 Exporting YOLO to TFLite...
bash export_tflite.sh

echo 🚀 Launching FastAPI server...
start uvicorn fastapi_server:app --host 0.0.0.0 --port 8000

echo 🛰️ Starting detection module...
python pi_tflite_detect.py

echo ✔️ Done!
pause
