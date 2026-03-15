import os
import cv2
import uuid
import time
import json
from flask import Flask, render_template, send_file, jsonify, request
from flask_socketio import SocketIO
from ultralytics import YOLO
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler
import sys
import threading


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from database.db_detection_main import DetectionMainDatabase
from database.db_detection_class import DetectionClassDatabase

# Configuration des chemins
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SRC_DIR = os.path.join(BASE_DIR, 'src')
FRONTEND_DIR = os.path.join(SRC_DIR, 'frontend')
MODEL_PERSON_PATH = os.path.join(BASE_DIR, "data/final/weights_model/yolo11n.pt")
MODEL_CAR_PATH    = os.path.join(BASE_DIR, "data/final/weights_model/best_car.pt")
IMAGE_OUT_DIR = os.path.join(BASE_DIR, "data/final/image_annoted")
JSON_OUT_DIR = os.path.join(BASE_DIR, "data/final/yolo_json")

# Surveillance des 5 webcams : Cardiff, Madrid, Rome (Trevi), Murcia, La Palma
WATCH_DIRS = [
    os.path.join(BASE_DIR, "data", "raw", "webcam_cardiff_snapshots"),
    os.path.join(BASE_DIR, "data", "raw", "webcam_madrid_snapshots"),
    os.path.join(BASE_DIR, "data", "raw", "webcam_trevi_snapshots"),
    os.path.join(BASE_DIR, "data", "raw", "webcam_murcia_snapshots"),
    os.path.join(BASE_DIR, "data", "raw", "webcam_lapalma_snapshots"),
]

app = Flask(__name__, template_folder=FRONTEND_DIR, static_folder=FRONTEND_DIR, static_url_path='')
socketio = SocketIO(app, cors_allowed_origins="*")

# Creation des dossiers de sauvegarde
os.makedirs(IMAGE_OUT_DIR, exist_ok=True)
os.makedirs(JSON_OUT_DIR, exist_ok=True)

# Initialisation des deux bases de données
db_main = DetectionMainDatabase()
db_class = DetectionClassDatabase()

# Chargement des deux modeles YOLO
model_person = YOLO(MODEL_PERSON_PATH)
model_car    = YOLO(MODEL_CAR_PATH)


def resolve_class_ids(model, keywords):
    """Retourne les IDs de classes dont le nom contient un des keywords."""
    ids = []
    for class_id, class_name in model.names.items():
        name = str(class_name).lower().strip()
        if any(keyword in name for keyword in keywords):
            ids.append(int(class_id))
    return sorted(set(ids))


# Déduction auto des classes selon les noms internes des modèles
# (utile quand les modèles ne sont pas COCO et n'ont pas les IDs standards)
PERSON_CLASSES = resolve_class_ids(model_person, ["person", "people", "pedestrian"])
CAR_CLASSES = resolve_class_ids(model_car, ["car", "cars", "vehicle", "truck", "bus"])

# Si aucune classe n'est trouvée, on ne filtre pas (toutes classes du modèle)
PERSON_CLASSES = PERSON_CLASSES if PERSON_CLASSES else None
CAR_CLASSES = CAR_CLASSES if CAR_CLASSES else None

print(f"Classes person utilisées: {PERSON_CLASSES} | names={model_person.names}")
print(f"Classes car utilisées: {CAR_CLASSES} | names={model_car.names}")

# Mapping dossier -> label affichable
CAMERA_LABELS = {
    "webcam_cardiff_snapshots": "Cardiff",
    "webcam_murcia_snapshots":  "Murcia",
    "webcam_lapalma_snapshots": "La Palma",
    "webcam_madrid_snapshots":  "Madrid",
    "webcam_trevi_snapshots":   "Rome (Trevi)",
}

def process_image(file_path):
    try:
        time.sleep(0.5)  # Securite pour ecriture fichier

        img = cv2.imread(file_path)
        if img is None:
            print(f"Impossible de lire : {file_path}")
            return

        uid = uuid.uuid4().hex
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        detections = []
        detection_count = {}

        # --- Modele person ---
        res_person = model_person.predict(
            source=file_path, classes=PERSON_CLASSES,
            conf=0.25, save=False, verbose=False
        )[0]
        if res_person.boxes is not None:
            for box in res_person.boxes:
                conf = round(float(box.conf[0]), 2)
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
                cv2.rectangle(img, (x1, y1), (x2, y2), (219, 142, 0), 2)   # bleu
                cv2.putText(img, f"person {conf}", (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (219, 142, 0), 1)
                detections.append({"class": "person", "confidence": conf})
                detection_count["person"] = detection_count.get("person", 0) + 1

        # --- Modele car (truck/bus remappes en "car") ---
        res_car = model_car.predict(
            source=file_path, classes=CAR_CLASSES,
            conf=0.25, save=False, verbose=False
        )[0]
        if res_car.boxes is not None:
            for box in res_car.boxes:
                conf = round(float(box.conf[0]), 2)
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 220), 2)     # rouge
                cv2.putText(img, f"car {conf}", (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 220), 1)
                detections.append({"class": "car", "confidence": conf})
                detection_count["car"] = detection_count.get("car", 0) + 1

        # 1. Sauvegarde de l'image annotee
        image_name = f"det_{timestamp}_{uid}.png"
        image_save_path = os.path.join(IMAGE_OUT_DIR, image_name)
        cv2.imwrite(image_save_path, img)

        # 2. Preparation du payload
        folder_name = os.path.basename(os.path.dirname(file_path))
        source_label = CAMERA_LABELS.get(folder_name, folder_name)
        data_payload = {
            "image_id": uid,
            "date": time.strftime("%Y-%m-%d"),
            "time": time.strftime("%H:%M:%S"),
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S"),
            "num_detections": len(detections),
            "detection_count": detection_count,
            "detections": detections,
            "image_url": f"/image/{image_name}",
            "source": folder_name,
            "source_label": source_label
        }

        # 3. Sauvegarde JSON
        json_name = f"data_{timestamp}_{uid}.json"
        with open(os.path.join(JSON_OUT_DIR, json_name), 'w') as f:
            json.dump(data_payload, f, indent=4)

        # 4. Insertion DB
        is_inserted = db_main.insert_detection(
            image_url=data_payload['image_url'],
            date=data_payload['date'],
            time=data_payload['time'],
            datetime_str=data_payload['datetime'],
            num_detections=data_payload['num_detections']
        )
        if is_inserted:
            class_list = []
            for class_name, count in data_payload['detection_count'].items():
                confidences = [obj['confidence'] for obj in data_payload['detections']
                               if obj['class'] == class_name]
                avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
                class_list.append({'class': class_name, 'confidence': avg_confidence, 'count': count})
            db_class.insert_batch_class(image_url=data_payload['image_url'], detections=class_list)
            print(f"Donnees inserees dans les deux DB")
        else:
            print(f"Erreur lors de l'insertion dans la DB")

        # 5. Envoi au frontend
        socketio.emit('new_detection', data_payload)
        socketio.emit('stats_update', get_db_stats())
        print(f"Traite : {image_name} | person={detection_count.get('person',0)} car={detection_count.get('car',0)}")

    except Exception as e:
        print(f"Erreur process_image : {e}")


def get_db_stats():
    """Construit le payload de stats depuis les deux DB."""
    class_stats = db_class.get_class_statistics()
    all_detections = db_main.get_all_detections()
    total_images = len(all_detections)
    total_objects = sum(d['num_detections'] for d in all_detections)
    return {
        'total_images': total_images,
        'total_objects': total_objects,
        'class_stats': class_stats
    }

class ImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            process_image(event.src_path)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stats")
def stats_page():
    return render_template("stats.html")

@app.route("/image/<filename>")
def get_image(filename):
    return send_file(os.path.join(IMAGE_OUT_DIR, filename))

@app.route("/api/detections")
def get_detections():
    """Endpoint pour récupérer toutes les détections"""
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)
    detections = db_main.get_all_detections(limit=limit, offset=offset)
    for det in detections:
        filename = det.get('image_url', '').split('/')[-1]
        classes = db_class.get_class_by_image(filename)
        det['class_counts'] = {c['class']: c['detection_count'] for c in classes}
    return jsonify(detections)

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


@app.route("/api/stats")
def get_stats():
    """Endpoint stats globales pour le dashboard"""
    return jsonify(get_db_stats())


@app.route("/api/db_stats")
def get_db_stats_endpoint():
    """Stats approfondies depuis la DB : timeline, heure, classes, résumé."""
    summary = db_main.get_summary()
    per_day = db_main.get_detections_per_day()
    hourly = db_main.get_hourly_activity()
    class_stats = db_class.get_class_statistics()
    class_trend = db_class.get_class_trend_per_day()
    per_frame = db_class.get_per_frame_counts()
    return jsonify({
        'summary': summary,
        'per_day': per_day,
        'hourly': hourly,
        'class_stats': class_stats,
        'class_trend': class_trend,
        'per_frame': per_frame
    })

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
    event_handler = ImageHandler()
    observer = Observer()
    for watch_dir in WATCH_DIRS:
        os.makedirs(watch_dir, exist_ok=True)
        observer.schedule(event_handler, watch_dir, recursive=False)
        print(f"Surveillance: {watch_dir}")
    observer.start()
    port = int(os.environ.get("PORT", "5000"))
    print(f"\nServeur Flask démarré sur http://0.0.0.0:{port}")
    print(f"DB Main: {db_main.db_path}")
    print(f"DB Class: {db_class.db_path}")
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)