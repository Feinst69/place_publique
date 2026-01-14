from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
from pathlib import Path
import time
import schedule
import sys
import requests
import json
from utils import *

# Ajouter le dossier racine au PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR

# Charger la configuration des caméras depuis le fichier JSON
CONFIG_FILE = Path(__file__).resolve().parents[2] / "config" / "cameras.json"

def load_cameras_config():
    """Charge la configuration des caméras depuis le fichier JSON"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Erreur lors du chargement du fichier config: {e}")
        return None

# Charger la configuration
config = load_cameras_config()
if not config:
    print("Impossible de charger la configuration des caméras!")
    print(f"Fichier attendu: {CONFIG_FILE}")
    sys.exit(1)

# Valider que la config a au moins une caméra
if 'cameras' not in config or not config['cameras']:
    print("Erreur: Aucune caméra configurée dans le fichier!")
    sys.exit(1)

# Préparer les caméras actives
WEBCAMS = {}
for cam_config in config.get('cameras', []):
    if cam_config.get('enabled', True):
        camera_name = cam_config['name']
        WEBCAMS[camera_name] = {
            "url": cam_config['url'],
            "display_name": cam_config.get('display_name', camera_name),
            "save_dir": Path(RAW_DATA_DIR) / f"webcam_{camera_name}_snapshots",
            "metadata_dir": Path(PROCESSED_DATA_DIR) / f"web_cam_{camera_name}_metadata",
        }

INTERVAL_MINUTES = config.get('settings', {}).get('interval_minutes', 1)
WAIT_TIME = config.get('settings', {}).get('wait_time', 15)
API_URL = config.get('settings', {}).get('api_url', 'http://localhost:5000/api/webcam')

# Créer les dossiers de sauvegarde
for webcam_name, webcam_config in WEBCAMS.items():
    webcam_config["save_dir"].mkdir(parents=True, exist_ok=True)
    webcam_config["metadata_dir"].mkdir(parents=True, exist_ok=True)
    webcam_config["metadata_file"] = webcam_config["metadata_dir"] / "captures_metadata.json"


def send_to_api(webcam_name, image_path, timestamp):
    """Envoie l'image et les métadonnées à l'API Flask"""
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {
                'webcam_name': webcam_name,
                'timestamp': timestamp,
            }
            response = requests.post(API_URL, files=files, data=data, timeout=10)
            if response.status_code == 200:
                print(f"✓ Image envoyée à l'API Flask: {response.json()['message']}")
                return True
            else:
                print(f"✗ Erreur API: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"✗ Erreur lors de l'envoi à l'API: {e}")
        return False


def capture_and_send(driver, webcam_name, config):
    """Capture une webcam et envoie l'image à l'API"""
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    success = capture_webcam(
        driver,
        webcam_name,
        config["save_dir"],
        config["url"],
        WAIT_TIME,
        config["metadata_file"]
    )
    
    # Si la capture a réussi, envoyer à l'API
    if success:
        image_path = config["save_dir"] / f"{webcam_name}_{timestamp_str}.png"
        if image_path.exists():
            send_to_api(webcam_name, str(image_path), timestamp_str)
    
    return success


def main():
    """Fonction principale"""
    print("=" * 70)
    print("Script de capture Webcam - Cardiff & Trevi")
    print("=" * 70)
    
    # Afficher la configuration
    for webcam_name, config in WEBCAMS.items():
        print(f"\n{webcam_name.upper()}:")
        print(f"  URL: {config['url']}")
        print(f"  Dossier: {config['save_dir'].absolute()}")
    
    print(f"\nIntervalle: {INTERVAL_MINUTES} minutes")
    print(f"Temps d'attente vidéo: {WAIT_TIME} secondes")
    print("=" * 70)
    
    # Initialiser les navigateurs dynamiquement
    print("\nInitialisation des navigateurs Chrome...")
    drivers = {}
    for webcam_name in WEBCAMS.keys():
        print(f"Initialisation du navigateur pour {webcam_name}...")
        drivers[webcam_name] = setup_driver()
    
    try:
        # Capture immédiate au lancement
        print("\nCapture initiale...")
        for webcam_name, config in WEBCAMS.items():
            print(f"\n[{webcam_name.upper()}] Capture en cours...")
            capture_and_send(drivers[webcam_name], webcam_name, config)
        
        # Planification des captures suivantes
        for webcam_name, config in WEBCAMS.items():
            schedule.every(INTERVAL_MINUTES).minutes.do(
                lambda wname=webcam_name, cfg=config: capture_and_send(
                    drivers[wname],
                    wname,
                    cfg
                )
            )
        
        print(f"\n Captures programmées toutes les {INTERVAL_MINUTES} minutes")
        print("Appuyez sur Ctrl+C pour arrêter\n")
        
        # Boucle principale
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n Arrêt du script demandé par l'utilisateur")
    finally:
        for driver in drivers.values():
            driver.quit()
        
        print("\n" + "=" * 70)
        for webcam_name, config in WEBCAMS.items():
            print(f"{webcam_name.upper()}: Images sauvegardées dans {config['save_dir'].absolute()}")
        print("=" * 70)

if __name__ == "__main__":
    main()
