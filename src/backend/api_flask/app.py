import os
import cv2
import uuid
import time
import json
from flask import Flask, render_template, send_file, jsonify, request
from flask_socketio import SocketIO
from ultralytics import YOLO
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys
from pathlib import Path
import base64

# Ajouter le répertoire place_publique au path
# app.py est à: place_publique/src/backend/api_flask/
# On monte de 3 niveaux pour arriver à place_publique
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Maintenant on peut importer depuis src
from src.database.db_detection_main import DetectionMainDatabase
from src.database.db_detection_class import DetectionClassDatabase
from src.config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR

# Charger la configuration des caméras
CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'cameras.json')

def load_cameras_config():
    """Charge la configuration des caméras depuis le fichier JSON"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement du fichier config: {e}")
        return None

# Configuration des chemins
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SRC_DIR = os.path.join(BASE_DIR, 'src')
FRONTEND_DIR = os.path.join(SRC_DIR, 'frontend')
MODEL_PATH = os.path.join(BASE_DIR, "data/final/weights_model/yolo11x.pt")
IMAGE_OUT_DIR = os.path.join(BASE_DIR, "data/final/image_annoted")
JSON_OUT_DIR = os.path.join(BASE_DIR, "data/final/yolo_json")
WATCH_DIR = r"C:\Users\idirs\Desktop\M2IA\place_publique\data\raw\webcam_snapshots"

# Configuration des caméras dynamique
camera_config = load_cameras_config()
print(f"📷 Configuration des caméras chargée: {camera_config}")
WEBCAM_STORAGE = {}

if camera_config:
    for cam in camera_config.get('cameras', []):
        if cam.get('enabled', True):
            camera_name = cam['name']
            WEBCAM_STORAGE[camera_name] = {
                "name": camera_name,
                "display_name": cam.get('display_name', camera_name),
                "input_dir": os.path.join(BASE_DIR, f"data/raw/webcam_snapshots"),
                "latest_image": None,
                "latest_timestamp": None
            }
            os.makedirs(WEBCAM_STORAGE[camera_name]['input_dir'], exist_ok=True)
    print(f"✅ WEBCAM_STORAGE initialisé avec {len(WEBCAM_STORAGE)} caméras: {list(WEBCAM_STORAGE.keys())}")
else:
    print("❌ Erreur: configuration des caméras non chargée")

app = Flask(__name__, template_folder=FRONTEND_DIR, static_folder=FRONTEND_DIR, static_url_path='')
socketio = SocketIO(app, cors_allowed_origins="*")

# Creation des dossiers de sauvegarde
os.makedirs(IMAGE_OUT_DIR, exist_ok=True)
os.makedirs(JSON_OUT_DIR, exist_ok=True)

# Initialisation des deux bases de données
db_main = DetectionMainDatabase()
db_class = DetectionClassDatabase()

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
            "date": time.strftime("%Y-%m-%d"),  # Ajout de la date
            "time": time.strftime("%H:%M:%S"),  # Heure
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S"),  # Date et heure combinées
            "num_detections": len(detections),
            "detection_count": detection_count,
            "detections": detections,
            "image_url": f"/image/{image_name}"
        }

        # 3. Sauvegarde du fichier JSON
        json_name = f"data_{timestamp}_{uid}.json"
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/image/<filename>")
def get_image(filename):
    return send_file(os.path.join(IMAGE_OUT_DIR, filename))

@app.route("/api/detections")
def get_detections():
    """Endpoint pour récupérer toutes les détections"""
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)
    detections = db_main.get_all_detections(limit=limit, offset=offset)
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
    """Endpoint pour récupérer les statistiques globales"""
    stats = db_class.get_class_statistics()
    return jsonify(stats)

@app.route("/api/statistics/webcam")
def get_webcam_summary():
    """Endpoint pour récupérer le résumé des statistiques par webcam"""
    summary = db_class.get_webcam_summary()
    return jsonify(summary)

@app.route("/api/statistics/webcam/<webcam_name>")
def get_webcam_statistics(webcam_name):
    """Endpoint pour récupérer les statistiques détaillées d'une webcam"""
    stats = db_class.get_statistics_by_webcam(webcam_name)
    return jsonify(stats)

@app.route("/api/statistics/timeline")
def get_detection_timeline():
    """Endpoint pour récupérer l'évolution temporelle des détections"""
    webcam_filter = request.args.get('webcam', None)
    timeline = db_class.get_detection_timeline(webcam_filter)
    return jsonify(timeline)

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

# ============ ENDPOINTS WEBCAMS ============

@app.route("/api/webcam", methods=['POST'])
def upload_webcam_image():
    """Reçoit et stocke les images des webcams, lance YOLO et envoie les stats"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        webcam_name = request.form.get('webcam_name', 'unknown')
        timestamp = request.form.get('timestamp', '')
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Vérifier que la webcam est reconnue
        if webcam_name not in WEBCAM_STORAGE:
            return jsonify({"error": f"Webcam '{webcam_name}' not found in configuration"}), 404
        
        # Créer le répertoire s'il n'existe pas
        webcam_dir = WEBCAM_STORAGE[webcam_name]['input_dir']
        os.makedirs(webcam_dir, exist_ok=True)
        
        # Sauvegarder l'image
        filename = f"{webcam_name}_{timestamp}.png"
        filepath = os.path.join(webcam_dir, filename)
        file.save(filepath)
        
        # ========== YOLO DETECTION ==========
        time.sleep(0.3)  # Sécurité pour l'écriture
        results = model.predict(source=filepath, conf=0.25, save=False, verbose=False)
        result = results[0]
        
        uid = uuid.uuid4().hex
        
        # Sauvegarder l'image annotée
        annotated_name = f"{webcam_name}_det_{timestamp}_{uid}.png"
        annotated_path = os.path.join(IMAGE_OUT_DIR, annotated_name)
        annotated_img = result.plot()
        cv2.imwrite(annotated_path, annotated_img)
        
        # Compter les détections par classe
        detections = []
        detection_count = {}
        class_confidences = {}  # Pour stocker les confidences par classe
        
        if result.boxes is not None:
            for box in result.boxes:
                class_name = model.names[int(box.cls[0])]
                confidence = round(float(box.conf[0]), 2)
                detections.append({
                    "class": class_name,
                    "confidence": confidence
                })
                detection_count[class_name] = detection_count.get(class_name, 0) + 1
                
                # Stocker les confidences pour calculer la moyenne
                if class_name not in class_confidences:
                    class_confidences[class_name] = []
                class_confidences[class_name].append(confidence)
        
        # Préparer les données
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        data_payload = {
            "image_id": uid,
            "webcam_name": webcam_name,
            "date": time.strftime("%Y-%m-%d"),
            "time": time.strftime("%H:%M:%S"),
            "datetime": current_time,
            "num_detections": len(detections),
            "detection_count": detection_count,
            "detections": detections,
            "image_url": f"/image/{annotated_name}"
        }
        
        # Sauvegarder dans la base de données
        db_main.insert_detection(
            image_url=data_payload['image_url'],
            date=data_payload['date'],
            time=data_payload['time'],
            datetime_str=data_payload['datetime'],
            num_detections=data_payload['num_detections']
        )
        
        # Sauvegarder les détections par classe
        for class_name, count in detection_count.items():
            # Calculer la confiance moyenne pour cette classe
            avg_confidence = sum(class_confidences[class_name]) / len(class_confidences[class_name])
            
            db_class.insert_detection_class(
                image_url=data_payload['image_url'],
                class_name=class_name,
                confidence=round(avg_confidence, 2),
                detection_count=count,
                webcam_name=webcam_name
            )
        
        # Stocker l'image annotée en mémoire
        with open(annotated_path, 'rb') as f:
            WEBCAM_STORAGE[webcam_name]['latest_image'] = base64.b64encode(f.read()).decode('utf-8')
        WEBCAM_STORAGE[webcam_name]['latest_timestamp'] = timestamp
        WEBCAM_STORAGE[webcam_name]['latest_stats'] = detection_count
        
        # Envoyer via WebSocket avec les statistiques
        socketio.emit('new_webcam', {
            'webcam_name': webcam_name,
            'timestamp': timestamp,
            'image': WEBCAM_STORAGE[webcam_name]['latest_image'],
            'stats': detection_count,
            'num_detections': len(detections)
        })
        
        print(f"✅ {webcam_name}: {len(detections)} détections - {detection_count}")
        
        return jsonify({
            "status": "success",
            "webcam": webcam_name,
            "filename": filename,
            "message": f"Image from {webcam_name} received",
            "stats": detection_count
        }), 200
    
    except Exception as e:
        print(f"Erreur lors de la réception de l'image webcam: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/webcam/<webcam_name>")
def get_latest_webcam(webcam_name):
    """Récupère la dernière image d'une webcam"""
    if webcam_name not in WEBCAM_STORAGE:
        return jsonify({"error": "Webcam not found"}), 404
    
    storage = WEBCAM_STORAGE[webcam_name]
    
    if storage['latest_image'] is None:
        return jsonify({"error": "No image available"}), 404
    
    return jsonify({
        "webcam_name": webcam_name,
        "timestamp": storage['latest_timestamp'],
        "image": f"data:image/png;base64,{storage['latest_image']}"
    }), 200

@app.route("/api/webcams")
def get_all_webcams():
    """Récupère les dernières images de toutes les webcams"""
    result = {}
    for webcam_name, storage in WEBCAM_STORAGE.items():
        if storage['latest_image'] is not None:
            result[webcam_name] = {
                "name": webcam_name,
                "display_name": storage.get('display_name', webcam_name),
                "timestamp": storage['latest_timestamp'],
                "image": f"data:image/png;base64,{storage['latest_image']}"
            }
    
    return jsonify(result), 200

@app.route("/api/cameras/config")
def get_cameras_config():
    """Récupère la configuration des caméras pour le frontend"""
    return jsonify(WEBCAM_STORAGE), 200

if __name__ == "__main__":
    event_handler = ImageHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    print(f"Serveur Flask démarré sur http://0.0.0.0:5000")
    print(f"DB Main: {db_main.db_path}")
    print(f"DB Class: {db_class.db_path}")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)