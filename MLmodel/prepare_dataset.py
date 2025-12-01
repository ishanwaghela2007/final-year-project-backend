# prepare_dataset.py
import os
from glob import glob

IMG_EXTS = [".jpg", ".jpeg", ".png"]
ROOT = "dataset"

def check():
    for split in ("train", "val"):
        img_dir = os.path.join(ROOT, "images", split)
        lab_dir = os.path.join(ROOT, "labels", split)
        imgs = []
        for ext in IMG_EXTS:
            imgs += glob(os.path.join(img_dir, f"*{ext}"))
        print(f"{split}: images={len(imgs)}")
        if not os.path.exists(lab_dir):
            print(f" -> labels folder missing: {lab_dir}")
            continue
        txts = glob(os.path.join(lab_dir, "*.txt"))
        print(f"{split}: labels={len(txts)}")
        # check pairing
        img_basenames = {os.path.splitext(os.path.basename(p))[0] for p in imgs}
        txt_basenames = {os.path.splitext(os.path.basename(p))[0] for p in txts}
        missing = img_basenames - txt_basenames
        if missing:
            print(f" WARNING: {len(missing)} images missing label files. Examples: {list(missing)[:5]}")
        extra = txt_basenames - img_basenames
        if extra:
            print(f" WARNING: {len(extra)} label files missing images. Examples: {list(extra)[:5]}")

if __name__ == "__main__":
    check()
