# export_tflite.sh
#!/bin/bash
# Run from project root after training finished.

# path to best.pt (adjust if different)
BEST_PT="runs/tube_detect/weights/best.pt"

# export fp16 tflite (fast, usually works)
python - <<PY
from ultralytics import YOLO
model = YOLO("$BEST_PT")
print("Exporting to TFLite (fp16)...")
model.export(format="tflite", opset=11, dynamic=False, optimize=True)
print("Export done. Look for .tflite in the current folder or export folder.")
PY

# For INT8 (if you want and have representative images):
# model.export(format="tflite", int8=True, ...)  <-- uncomment & configure if you prepare representative dataset
