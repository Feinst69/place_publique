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
import json
import os

def setup_driver():
    """Configure Chrome headless (local + Docker)."""
    chrome_options = Options()

    # Selenium/Chrome flags stables in CI/containers
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Pour éviter la détection de bot
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    # Docker-friendly binary path if provided
    chrome_bin = os.environ.get("CHROME_BIN")
    if chrome_bin:
        chrome_options.binary_location = chrome_bin

    chrome_driver_path = os.environ.get("CHROMEDRIVER_PATH")
    if chrome_driver_path:
        service = Service(chrome_driver_path)
        return webdriver.Chrome(service=service, options=chrome_options)

    return webdriver.Chrome(options=chrome_options)

def load_metadata(metadata_file):
    """Charge le fichier JSON de métadonnées"""
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"captures": []}

def save_metadata(metadata_file, data):
    """Sauvegarde le fichier JSON de métadonnées"""
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(data, indent=2, ensure_ascii=False, fp=f)

def capture_webcam(driver, SAVE_DIR, WEBCAM_URL, WAIT_TIME, metadata_file):
    """Capture une frame de la webcam.
    Relance tout le processus (refresh -> cookies -> vidéo -> fullscreen)
    tant que le plein écran n'est pas obtenu via un bouton dédié.
    """
    COOKIE_SELECTORS = [
        # Didomi (utilisé par skylinewebcams)
        "#didomi-notice-agree-button",
        ".didomi-button",
        "button[id*='didomi' i]",
        # Cookiebot
        "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
        # OneTrust
        ".onetrust-accept-btn-handler",
        "#onetrust-accept-btn-handler",
        # Génériques
        "button[id*='accept' i]",
        "button[class*='accept' i]",
        "button[id*='consent' i]",
        "button[class*='consent' i]",
        "button[id*='cookie' i]",
        "button[class*='cookie' i]",
        "a[class*='accept' i]",
        "div[class*='accept' i]",
        ".fc-button-label",
        ".fc-cta-consent",
        # Texte "Accepter"
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accepter')]",
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept all')]",
    ]
    VIDEO_SELECTORS = [
        "video",
        "button[aria-label*='play' i]",
        "button[class*='play' i]",
        ".video-play-button",
        "div[class*='player' i]",
        "iframe"
    ]
    FULLSCREEN_SELECTORS = [
        "button[aria-label*='fullscreen' i]",
        "button[class*='fullscreen' i]",
        "button[title*='plein écran' i]",
        ".vjs-fullscreen-control",
        "button[data-title*='fullscreen' i]"
    ]
    MAX_ATTEMPTS = 10

    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    webcam_name = SAVE_DIR.name.replace("webcam_", "").replace("_snapshots", "")
    filename = SAVE_DIR / f"{webcam_name}_{timestamp_str}.png"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(f"Chargement de la webcam... (tentative {attempt}/{MAX_ATTEMPTS})")
            driver.get(WEBCAM_URL)
            time.sleep(3)

            # Étape 1 : Cookies
            print("Tentative de clic sur les cookies...")
            cookie_clicked = False
            for selector in COOKIE_SELECTORS:
                try:
                    # Support XPath pour les sélecteurs qui commencent par //
                    if selector.startswith("//"):
                        el = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        el = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    el.click()
                    print(f"  → Cookies acceptés via: {selector}")
                    cookie_clicked = True
                    time.sleep(1)
                    break
                except:
                    continue
            if not cookie_clicked:
                print("  → Aucune bannière cookie trouvée (on continue)")

            # Étape 2 : Lancer la vidéo
            video_clicked = False
            for selector in VIDEO_SELECTORS:
                try:
                    el = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    el.click()
                    print(f"Clic vidéo: {selector}")
                    video_clicked = True
                    time.sleep(2)
                    break
                except:
                    continue
            if not video_clicked:
                print("Vidéo non trouvée, clic au centre de l'écran...")
                ActionChains(driver).move_by_offset(960, 400).click().perform()
                time.sleep(2)

            # Étape 3 : Plein écran (bouton uniquement — pas de JS fallback)
            fullscreen_clicked = False
            for sel in FULLSCREEN_SELECTORS:
                try:
                    el = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                    )
                    el.click()
                    print(f"Plein écran activé via: {sel}")
                    fullscreen_clicked = True
                    break
                except:
                    continue

            if not fullscreen_clicked:
                print(f"Plein écran échoué (tentative {attempt}), rechargement...")
                time.sleep(2)
                continue  # relance la boucle : refresh complet

            # Plein écran obtenu -> stabilisation + screenshot
            print(f"Attente de {WAIT_TIME}s pour stabilisation...")
            time.sleep(WAIT_TIME)
            driver.save_screenshot(str(filename))
            file_size = filename.stat().st_size / 1024
            print(f"Snapshot sauvegardé: {filename.name} ({file_size:.1f} KB)")

            # Métadonnées
            metadata = load_metadata(metadata_file)
            metadata["captures"].append({
                "filename": filename.name,
                "timestamp": timestamp.isoformat(),
                "file_size_kb": round(file_size, 2)
            })
            save_metadata(metadata_file, metadata)
            print(f"Métadonnées sauvegardées dans {metadata_file.name}")
            return True

        except Exception as e:
            print(f"Erreur tentative {attempt}: {e}")
            time.sleep(2)

    print(f"Abandon après {MAX_ATTEMPTS} tentatives.")
    return False

def run_scheduled(driver, SAVE_DIR, WEBCAM_URL, WAIT_TIME, metadata_file):
    """Exécute la capture selon le planning"""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Démarrage de la capture...")
    capture_webcam(driver, SAVE_DIR, WEBCAM_URL, WAIT_TIME, metadata_file)
