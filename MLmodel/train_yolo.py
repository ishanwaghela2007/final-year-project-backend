# train_yolo.py
from ultralytics import YOLO
import os

# paths
DATA_YAML = "dataset/data.yaml"
WEIGHTS_DIR = "runs"

# create or use yolov8n pretrained (small)
model = YOLO("yolov8n.pt")  # download if not present

# Train - tune epochs/batch for your dataset size
model.train(
    data=DATA_YAML,
    epochs=100,
    imgsz=640,
    batch=8,          # reduce if GPU memory small or using CPU
    patience=20,
    project="runs",
    name="tube_detect",
    device="0"        # "cpu" or "0" for GPU
)

# After training, best weights are in runs/tube_detect/weights/best.pt
print("Training finished. Best model at runs/tube_detect/weights/best.pt")
