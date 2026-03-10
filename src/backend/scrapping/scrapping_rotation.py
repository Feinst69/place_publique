"""
Script de scrapping en rotation : Cardiff -> Murcia -> La Palma -> Cardiff ...
Un seul navigateur Chrome tourne et capture chaque webcam à la suite.
"""
from pathlib import Path
import time
import sys

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR
from utils import setup_driver, capture_webcam, load_metadata

# Délai entre deux captures de la même caméra (en secondes)
# Avec 3 caméras et 30s entre chaque, chaque caméra est capturée toutes les ~90s
DELAY_BETWEEN_CAMERAS = 30

WEBCAMS = [
    {
        "label": "Cardiff",
        "url": "https://www.skylinewebcams.com/fr/webcam/ellada/naigaio/dodecanisa/rhodes-sea-gate.html",
        "save_dir":     Path(RAW_DATA_DIR) / "webcam_cardiff_snapshots",
        "metadata_dir": Path(PROCESSED_DATA_DIR) / "web_cam_cardiff_metadata",
    },
    {
        "label": "Murcia",
        "url": "https://www.skylinewebcams.com/fr/webcam/espana/region-de-murcia/murcia/bullas-plaza-de-espana.html",
        "save_dir":     Path(RAW_DATA_DIR) / "webcam_murcia_snapshots",
        "metadata_dir": Path(PROCESSED_DATA_DIR) / "web_cam_murcia_metadata",
    },
    {
        "label": "La Palma",
        "url": "https://www.skylinewebcams.com/fr/webcam/espana/canarias/santa-cruz-de-tenerife/los-llanos-de-aridane-la-palma.html",
        "save_dir":     Path(RAW_DATA_DIR) / "webcam_lapalma_snapshots",
        "metadata_dir": Path(PROCESSED_DATA_DIR) / "web_cam_lapalma_metadata",
    },
]

# Créer les dossiers
for cam in WEBCAMS:
    cam["save_dir"].mkdir(parents=True, exist_ok=True)
    cam["metadata_dir"].mkdir(parents=True, exist_ok=True)
    cam["metadata_file"] = cam["metadata_dir"] / "captures_metadata.json"


def main():
    print("=" * 70)
    print("Scrapping en rotation : Cardiff -> Murcia -> La Palma")
    print(f"Délai entre caméras : {DELAY_BETWEEN_CAMERAS}s")
    print("=" * 70)

    print("\nInitialisation du navigateur Chrome...")
    driver = setup_driver()

    cycle = 0
    try:
        while True:
            cycle += 1
            print(f"\n{'=' * 70}")
            print(f"Cycle #{cycle}")
            print(f"{'=' * 70}")

            for i, cam in enumerate(WEBCAMS):
                print(f"\n[{i+1}/{len(WEBCAMS)}] Capture {cam['label']}...")
                try:
                    capture_webcam(
                        driver,
                        cam["save_dir"],
                        cam["url"],
                        15,  # WAIT_TIME
                        cam["metadata_file"]
                    )
                    print(f"  {cam['label']} : capture OK")
                except Exception as e:
                    print(f"  {cam['label']} : erreur - {e}")

                if i < len(WEBCAMS) - 1:
                    print(f"  Attente {DELAY_BETWEEN_CAMERAS}s avant {WEBCAMS[i+1]['label']}...")
                    time.sleep(DELAY_BETWEEN_CAMERAS)

            print(f"\nCycle #{cycle} terminé. Attente {DELAY_BETWEEN_CAMERAS}s avant le prochain cycle...")
            time.sleep(DELAY_BETWEEN_CAMERAS)

    except KeyboardInterrupt:
        print("\n\nArrêt demandé par l'utilisateur")
    finally:
        driver.quit()
        print("Navigateur fermé.")


if __name__ == "__main__":
    main()
