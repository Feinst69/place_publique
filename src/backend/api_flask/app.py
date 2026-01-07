import os
import cv2
import uuid
import time
import json
from flask import Flask, render_template, send_file, jsonify
from flask_socketio import SocketIO
from ultralytics import YOLO
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
MODEL_PATH = os.path.join(BASE_DIR, "data/final/weights_model/yolov8n.pt")
IMAGE_OUT_DIR = os.path.join(BASE_DIR, "data/final/image_annoted")
JSON_OUT_DIR = os.path.join(BASE_DIR, "data/final/yolo_json")
WATCH_DIR = r"C:\Users\idirs\Desktop\M2IA\place_publique\data\raw\webcam_bergen_snapshots"

app = Flask(__name__, template_folder=FRONTEND_DIR, static_folder=FRONTEND_DIR, static_url_path='')
socketio = SocketIO(app, cors_allowed_origins="*")

# Creation des dossiers de sauvegarde
os.makedirs(IMAGE_OUT_DIR, exist_ok=True)
os.makedirs(JSON_OUT_DIR, exist_ok=True)

model = YOLO(MODEL_PATH)

def process_image(file_path):
    try:
        time.sleep(0.5) # Securite pour ecriture fichier
        results = model.predict(source=file_path, conf=0.25, save=False, verbose=False)
        result = results[0]

        uid = uuid.uuid4().hex
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # 1. Sauvegarde de l'image annotee
        image_name = f"det_{timestamp}_{uid}.png"
        image_save_path = os.path.join(IMAGE_OUT_DIR, image_name)
        annotated_img = result.plot()
        cv2.imwrite(image_save_path, annotated_img)

        # 2. Preparation des donnees
        detections = []
        detection_count = {}  # Compteur par classe
        
        if result.boxes is not None:
            for box in result.boxes:
                class_name = model.names[int(box.cls[0])]
                detections.append({
                    "class": class_name,
                    "confidence": round(float(box.conf[0]), 2)
                })
                # Compter par classe
                detection_count[class_name] = detection_count.get(class_name, 0) + 1

        data_payload = {
            "image_id": uid,
            "timestamp": time.strftime("%H:%M:%S"),
            "num_detections": len(detections),
            "detection_count": detection_count,  # Ajout du compteur par classe
            "detections": detections,
            "image_url": f"/image/{image_name}"
        }

        # 3. Sauvegarde du fichier JSON
        json_name = f"data_{timestamp}_{uid}.json"
        with open(os.path.join(JSON_OUT_DIR, json_name), 'w') as f:
            json.dump(data_payload, f, indent=4)

        # 4. Envoi au frontend
        socketio.emit('new_detection', data_payload)
        print(f"Traite : {image_name} ({len(detections)} objets)")

    except Exception as e:
        print(f"Erreur : {e}")

class ImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            process_image(event.src_path)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/image/<filename>")
def get_image(filename):
    return send_file(os.path.join(IMAGE_OUT_DIR, filename))

if __name__ == "__main__":
    event_handler = ImageHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)