from ultralytics import YOLO
import os
import json
import cv2
from collections import defaultdict

# =============================
# CONFIG
# =============================
MODEL_PATH = r"data/final/weights_model/yolov8n.pt"
IMAGE_PATH = r"data/raw/webcam_bergen_snapshots/bergen_20260213_120318.png"

JSON_DIR = r"data/final/yolo_json"
IMAGE_OUT_DIR = r"data/final/image_annoted"

CONF_THRESHOLD = 0.25

# =============================
# SETUP
# =============================
os.makedirs(JSON_DIR, exist_ok=True)
os.makedirs(IMAGE_OUT_DIR, exist_ok=True)

model = YOLO(MODEL_PATH)

# =============================
# INFERENCE
# =============================
results = model.predict(
    source=IMAGE_PATH,
    conf=CONF_THRESHOLD,
    save=False,
    verbose=False
)

result = results[0]

# =============================
# SAUVEGARDE IMAGE ANNOTÉE
# =============================
annotated_img = result.plot()
image_name = os.path.basename(IMAGE_PATH)
image_out_path = os.path.join(IMAGE_OUT_DIR, image_name)
cv2.imwrite(image_out_path, annotated_img)

# =============================
# COMPTAGE PAR CLASSE
# =============================
class_counts = defaultdict(int)

for box in result.boxes:
    cls_id = int(box.cls[0])
    class_name = model.names[cls_id]
    class_counts[class_name] += 1

# =============================
# SAUVEGARDE JSON
# =============================
json_data = {
    "image": image_name,
    "image_path": IMAGE_PATH,
    "model": os.path.basename(MODEL_PATH),
    "num_detections": len(result.boxes),
    "class_counts": dict(class_counts),
    "detections": []
}

for box in result.boxes:
    cls_id = int(box.cls[0])
    json_data["detections"].append({
        "class_id": cls_id,
        "class_name": model.names[cls_id],
        "confidence": float(box.conf[0]),
        "bbox_xyxy": box.xyxy[0].tolist()
    })

json_path = os.path.join(
    JSON_DIR,
    os.path.splitext(image_name)[0] + ".json"
)

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=4, ensure_ascii=False)


print("✓ Inférence terminée")
print(f"🖼️ Image annotée : {image_out_path}")
print(f"📄 JSON : {json_path}")

print("\n📊 Comptage par classe :")
for cls, count in class_counts.items():
    print(f"  - {cls}: {count}")
