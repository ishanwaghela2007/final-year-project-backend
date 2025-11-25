# test_on_images.py
from ultralytics import YOLO
import glob, cv2, os

MODEL_PT = "runs/tube_detect/weights/best.pt"  # trained model
TEST_DIR = "test_samples"                       # put your sample images here

model = YOLO(MODEL_PT)

imgs = glob.glob(os.path.join(TEST_DIR, "*.*"))
for img_path in imgs:
    results = model.predict(source=img_path, conf=0.4, imgsz=640)
    # results[0].plot() returns cv2 image with boxes
    out = results[0].plot()
    cv2.imshow("res", out)
    k = cv2.waitKey(0)
    if k == 27:
        break
cv2.destroyAllWindows()
