# pi_tflite_detect.py
import cv2
import numpy as np
import time
import requests
import uuid
from collections import deque

# Try tflite_runtime first (recommended on Pi)
try:
    import tflite_runtime.interpreter as tflite
except Exception:
    from tensorflow import lite as tflite

MODEL_PATH = "yolov8n.tflite"        # adjust to exported filename
CAM_INDEX = 0                        # or use video stream URL
IMG_SIZE = 640                       # same as model export size
CONF_THR = 0.35
IOU_MATCH = 0.3
API_URL = "http://<<REPLACE_ME_API_HOST>>:8000/add_inspection"  # <<REPLACE_ME>>
BATCH_ID = "BATCH-2025-A"

# Simple track memory (store previous boxes to avoid duplicates)
prev_boxes = deque(maxlen=5)  # store last N frames boxes

def iou(boxA, boxB):
    # boxes in x1,y1,x2,y2
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    if boxAArea + boxBArea - interArea == 0:
        return 0.0
    return interArea / float(boxAArea + boxBArea - interArea)

# Load TFLite
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

cap = cv2.VideoCapture(CAM_INDEX)
if not cap.isOpened():
    raise SystemExit("Cannot open camera")

def preprocess(frame):
    h, w = frame.shape[:2]
    # resize with aspect preserving pad to IMG_SIZE if needed (simple resize here)
    img = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.expand_dims(img, axis=0)
    return img

def postprocess_tflite(output, frame_shape, conf_thr=0.35):
    # Attempt to parse output. Many ultralytics tflite exports produce Nx6 arrays: [x,y,w,h,conf,cls]
    # Normalize coordinates from 0..1 relative to input size (if needed). We'll handle several shapes.
    detections = []
    h_frame, w_frame = frame_shape
    out = output
    # Flatten to (N, >=6)
    arr = np.array(out).squeeze()
    if arr.ndim == 1 and arr.size == 6:
        arr = arr.reshape(1,6)
    # if arr has shape (N,6)
    if arr.ndim == 2 and arr.shape[1] >= 6:
        for row in arr:
            x, y, w, h, conf, cls = row[:6]
            if conf < conf_thr: 
                continue
            # convert from relative cx,cy,w,h (0..1) to pixel x1,y1,x2,y2
            x_c = x; y_c = y
            x1 = int((x_c - w/2) * w_frame)
            y1 = int((y_c - h/2) * h_frame)
            x2 = int((x_c + w/2) * w_frame)
            y2 = int((y_c + h/2) * h_frame)
            detections.append({"box":(x1,y1,x2,y2),"conf":float(conf),"cls":int(cls)})
    else:
        # If output shape unknown, try to flatten and skip
        pass
    return detections

def send_counts(batch, counts, defects):
    payload = {
        "batch": batch,
        "counts": counts,
        "defects": defects,
        "report_id": str(uuid.uuid4())
    }
    try:
        r = requests.post(API_URL, json=payload, timeout=3)
        r.raise_for_status()
    except Exception as e:
        print("POST failed:", e)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1); continue

        img_in = preprocess(frame)
        interpreter.set_tensor(input_details[0]['index'], img_in.astype(np.float32))
        interpreter.invoke()
        out = interpreter.get_tensor(output_details[0]['index'])

        detections = postprocess_tflite(out, frame.shape, conf_thr=CONF_THR)

        # Counting with basic de-duplication: if a detected box has IoU > IOU_MATCH with
        # any box in previous frames, consider it same object (do not re-count).
        frame_boxes = []
        counts = {"tube_ok":0, "scratch":0, "crack":0, "bend":0, "hole":0}
        for d in detections:
            b = d["box"]
            cls = d["cls"]
            # check if matches previous
            duplicate = False
            for past in prev_boxes:
                for pb in past:
                    if iou(b, pb) > IOU_MATCH:
                        duplicate = True
                        break
                if duplicate: break
            if not duplicate:
                frame_boxes.append(b)
                if cls == 0: counts["tube_ok"] += 1
                elif cls == 1: counts["scratch"] += 1
                elif cls == 2: counts["crack"] += 1
                elif cls == 3: counts["bend"] += 1
                elif cls == 4: counts["hole"] += 1

            # draw for visualization
            color = (0,255,0) if cls==0 else (0,0,255)
            x1,y1,x2,y2 = b
            cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
            cv2.putText(frame, f"{cls}:{d['conf']:.2f}", (x1, y1-6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # push current boxes to history
        prev_boxes.append(frame_boxes)

        total_produced = sum(counts.values())
        total_defects = counts["scratch"] + counts["crack"] + counts["bend"] + counts["hole"]

        # Send counts to server (you can change frequency/min intervals)
        send_counts(BATCH_ID, total_produced, counts)

        cv2.putText(frame, f"Produced:{total_produced}  Defects:{total_defects}", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255),2)
        cv2.imshow("Pi Detect", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    pass
finally:
    cap.release()
    cv2.destroyAllWindows()
