import os
import cv2
import time
import json
import threading
from flask import Flask, render_template, send_file, jsonify, request
from flask_socketio import SocketIO
from ultralytics import YOLO
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from database.db_detection_main import DetectionMainDatabase
from database.db_detection_class import DetectionClassDatabase

# Configuration des chemins
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SRC_DIR = os.path.join(BASE_DIR, 'src')
FRONTEND_DIR = os.path.join(SRC_DIR, 'frontend')
MODEL_PATH = os.path.join(BASE_DIR, "data/final/weights_model/yolov8n.pt")
IMAGE_OUT_DIR = os.path.join(BASE_DIR, "data/final/image_annoted")
JSON_OUT_DIR = os.path.join(BASE_DIR, "data/final/yolo_json")
WATCH_DIR = os.getenv(
    "WATCH_DIR",
    os.path.join(BASE_DIR, "data/raw/webcam_bergen_snapshots")
)

app = Flask(__name__, template_folder=FRONTEND_DIR, static_folder=FRONTEND_DIR, static_url_path='')
socketio = SocketIO(app, cors_allowed_origins="*")

# Creation des dossiers de sauvegarde
os.makedirs(IMAGE_OUT_DIR, exist_ok=True)
os.makedirs(JSON_OUT_DIR, exist_ok=True)

# Initialisation des deux bases de données
db_main = DetectionMainDatabase()
db_class = DetectionClassDatabase()

model = YOLO(MODEL_PATH)


def is_processed(image_filename):
    """Vérifie si une image est déjà enregistrée en base."""
    return db_main.get_detection_by_url(image_filename) is not None

def process_image(file_path):
    try:
        time.sleep(0.5) # Securite pour ecriture fichier
        results = model.predict(source=file_path, conf=0.25, save=False, verbose=False)
        result = results[0]
        
        # 1. Sauvegarde de l'image annotee (meme nom que l'image source, comme yolo_test_inference)
        image_name = os.path.basename(file_path)
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
            "image_id": os.path.splitext(image_name)[0],
            "date": time.strftime("%Y-%m-%d"),  # Ajout de la date
            "time": time.strftime("%H:%M:%S"),  # Heure
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S"),  # Date et heure combinées
            "num_detections": len(detections),
            "detection_count": detection_count,
            "detections": detections,
            "image_url": f"/api/image/{image_name}"
        }

        # 3. Sauvegarde du fichier JSON
        json_name = f"{os.path.splitext(image_name)[0]}.json"
        with open(os.path.join(JSON_OUT_DIR, json_name), 'w') as f:
            json.dump(data_payload, f, indent=4)

        # 4. Insertion dans les deux bases de données
        # Insérer dans la DB principale des détections
        is_inserted = db_main.insert_detection(
            image_url=data_payload['image_url'],
            date=data_payload['date'],
            time=data_payload['time'],
            datetime_str=data_payload['datetime'],
            num_detections=data_payload['num_detections']
        )
        
        # Insérer les détails dans la DB des classes
        if is_inserted:
            class_list = []
            for class_name, count in data_payload['detection_count'].items():
                # Calculer la confiance moyenne pour cette classe
                confidences = [obj['confidence'] for obj in data_payload['detections'] 
                             if obj['class'] == class_name]
                avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
                
                class_list.append({
                    'class': class_name,
                    'confidence': avg_confidence,
                    'count': count
                })
            
            db_class.insert_batch_class(
                image_url=data_payload['image_url'],
                detections=class_list
            )
            print(f"✓ Données insérées dans les deux DB")
        else:
            print(f"✗ Erreur lors de l'insertion dans la DB")

        # 5. Envoi au frontend
        socketio.emit('new_detection', data_payload)
        print(f"Traite : {image_name} ({len(detections)} objets)")

    except Exception as e:
        print(f"Erreur : {e}")

class ImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            process_image(event.src_path)


def process_latest_pending_image():
    """Rattrapage: traite la dernière image brute non encore traitée."""
    try:
        if not os.path.isdir(WATCH_DIR):
            return

        candidates = [
            os.path.join(WATCH_DIR, f)
            for f in os.listdir(WATCH_DIR)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        ]
        if not candidates:
            return

        latest_file = max(candidates, key=os.path.getmtime)
        latest_name = os.path.basename(latest_file)
        if not is_processed(latest_name):
            print(f"Rattrapage: traitement de {latest_name}")
            process_image(latest_file)
    except Exception as e:
        print(f"Erreur rattrapage image: {e}")


def start_fallback_scanner(interval_seconds=10):
    """Scanner périodique pour éviter les événements filesystem manqués."""
    def _loop():
        while True:
            process_latest_pending_image()
            time.sleep(interval_seconds)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/image/<filename>")
def get_image(filename):
    return send_file(os.path.join(IMAGE_OUT_DIR, filename))

@app.route("/api/detections")
def get_detections():
    """Endpoint pour récupérer toutes les détections"""
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)
    detections = db_main.get_all_detections(limit=limit, offset=offset)
    return jsonify(detections)

@app.route("/api/detections/latest")
def get_latest_detection():
    """Endpoint pour récupérer la dernière détection avec ses classes"""
    detections = db_main.get_all_detections(limit=1, offset=0)
    if not detections:
        return jsonify({"error": "No detection found"}), 404

    latest = detections[0]
    image_filename = os.path.basename(latest["image_url"])
    classes = db_class.get_class_by_image(image_filename)

    detection_count = {}
    detections_list = []
    for cls in classes:
        class_name = cls["class"]
        count = cls["detection_count"]
        detection_count[class_name] = count
        detections_list.append({
            "class": class_name,
            "confidence": cls["confidence"],
        })

    payload = {
        "image_id": image_filename.rsplit(".", 1)[0],
        "date": latest["date"],
        "time": latest["time"],
        "datetime": latest["datetime"],
        "num_detections": latest["num_detections"],
        "detection_count": detection_count,
        "detections": detections_list,
        "image_url": f"/api/image/{image_filename}",
    }
    return jsonify(payload)

@app.route("/api/detections/<image_id>")
def get_detection(image_id):
    """Endpoint pour récupérer une détection spécifique"""
    detection = db_main.get_detection_by_url(image_id)
    if detection:
        # Récupérer aussi les classes
        classes = db_class.get_class_by_image(image_id)
        detection['classes'] = classes
        return jsonify(detection)
    return jsonify({"error": "Detection not found"}), 404

@app.route("/api/statistics")
def get_statistics():
    """Endpoint pour récupérer les statistiques"""
    stats = db_class.get_class_statistics()
    return jsonify(stats)

@app.route("/api/detections/date/<date>")
def get_detections_by_date(date):
    """Endpoint pour récupérer les détections par date (YYYY-MM-DD)"""
    detections = db_main.get_detections_by_date(date)
    return jsonify(detections)

@app.route("/api/detections/class/<class_name>")
def get_detections_by_class(class_name):
    """Endpoint pour récupérer les détections par classe"""
    limit = request.args.get('limit', type=int)
    classes = db_class.get_detections_by_class(class_name, limit=limit)
    return jsonify(classes)

if __name__ == "__main__":
    os.makedirs(WATCH_DIR, exist_ok=True)

    # Rattrapage immédiat au démarrage (si des images existent déjà)
    process_latest_pending_image()
    # Fallback continu si watchdog manque un événement
    start_fallback_scanner(interval_seconds=10)

    event_handler = ImageHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    print(f"Serveur Flask démarré sur http://0.0.0.0:5000")
    print(f"DB Main: {db_main.db_path}")
    print(f"DB Class: {db_class.db_path}")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)
