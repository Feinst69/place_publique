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
from utils import *

# Ajouter le dossier racine au PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR

# Configuration
WEBCAM_URL = "https://www.skylinewebcams.com/fr/webcam/norge/western-norway/bergen/bergen.html"
SAVE_DIR = Path(RAW_DATA_DIR) / "webcam_bergen_snapshots"
METADATA_DIR = Path(PROCESSED_DATA_DIR) / "web_cam_bergen_metadata"
METADATA_FILE = METADATA_DIR / "captures_metadata.json"
INTERVAL_MINUTES = 1  # Modifier selon vos besoins
WAIT_TIME = 15  # Secondes d'attente pour le chargement de la vidéo

# Créer les dossiers de sauvegarde
SAVE_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)


def main():
    """Fonction principale"""
    print("=" * 70)
    print("Script de capture Webcam Bergen - Norvège")
    print("=" * 70)
    print(f"URL: {WEBCAM_URL}")
    print(f"Dossier de sauvegarde: {SAVE_DIR.absolute()}")
    print(f"Dossier métadonnées: {METADATA_DIR.absolute()}")
    print(f"Intervalle: {INTERVAL_MINUTES} minutes")
    print(f"Temps d'attente vidéo: {WAIT_TIME} secondes")
    print("=" * 70)
    
    # Initialiser le navigateur
    print("\n Initialisation du navigateur Chrome...")
    driver = setup_driver()
    
    try:
        # Capture immédiate au lancement
        print("\n Capture initiale...")
        capture_webcam(driver, SAVE_DIR, WEBCAM_URL, WAIT_TIME, METADATA_FILE)
        
        # Planification des captures suivantes
        schedule.every(INTERVAL_MINUTES).minutes.do(lambda: run_scheduled(driver, SAVE_DIR, WEBCAM_URL, WAIT_TIME, METADATA_FILE))
        
        print(f"\n Captures programmées toutes les {INTERVAL_MINUTES} minutes")
        print("Appuyez sur Ctrl+C pour arrêter\n")
        
        # Boucle principale
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n Arrêt du script demandé par l'utilisateur")
    finally:
        driver.quit()
        print(f" Images sauvegardées dans: {SAVE_DIR.absolute()}")

if __name__ == "__main__":
    main()
