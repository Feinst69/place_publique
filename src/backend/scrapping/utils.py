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

def setup_driver():
    """Configure le navigateur Chrome en mode headless"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Mode sans interface
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--mute-audio")
    
    # Pour éviter la détection de bot
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

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
    """Capture une frame de la webcam"""
    try:
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = SAVE_DIR / f"bergen_{timestamp_str}.png"
        
        print(f"Chargement de la webcam...")
        driver.get(WEBCAM_URL)
        
        # Attendre le chargement initial
        time.sleep(3)
        
        # ÉTAPE 1 : Accepter les cookies / consentement
        print(f"Recherche du bouton d'acceptation des cookies...")
        cookie_selectors = [
            "button[id*='accept' i]",
            "button[class*='accept' i]",
            "button[id*='consent' i]",
            "button[class*='consent' i]",
            "a[class*='accept' i]",
            "div[class*='accept' i]",
            "button:contains('Accept')",
            "button:contains('Accepter')",
            "button:contains('J\'accepte')",
            ".fc-button-label",  # Format courant pour les cookies
            "#didomi-notice-agree-button",  # Didomi
            ".didomi-button"
        ]
        
        for selector in cookie_selectors:
            try:
                element = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                element.click()
                print(f"✓ Cookies acceptés via: {selector}")
                time.sleep(1)
                break
            except:
                continue
        
        # ÉTAPE 2 : Cliquer sur la vidéo pour la lancer
        print(f"Tentative de clic sur la vidéo...")
        video_selectors = [
            "video",
            "button[aria-label*='play' i]",
            "button[class*='play' i]",
            ".video-play-button",
            "div[class*='player' i]",
            "iframe"
        ]
        
        video_clicked = False
        for selector in video_selectors:
            try:
                element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                element.click()
                print(f"✓ Clic sur la vidéo réussi: {selector}")
                video_clicked = True
                time.sleep(2)
                break
            except:
                continue
        
        if not video_clicked:
            print("Vidéo non trouvée par sélecteur, clic au centre de l'écran...")
            actions = ActionChains(driver)
            actions.move_by_offset(960, 400).click().perform()
            time.sleep(2)
        
        # ÉTAPE 3 : Mettre en plein écran
        print(f"Passage en plein écran...")
        try:
            # Essayer avec le bouton fullscreen
            fullscreen_selectors = [
                "button[aria-label*='fullscreen' i]",
                "button[class*='fullscreen' i]",
                "button[title*='plein écran' i]",
                ".vjs-fullscreen-control",
                "button[data-title*='fullscreen' i]"
            ]
            
            fullscreen_clicked = False
            for selector in fullscreen_selectors:
                try:
                    element = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.click()
                    print(f"✓ Plein écran activé via: {selector}")
                    fullscreen_clicked = True
                    break
                except:
                    continue
            
            # Si pas de bouton fullscreen, utiliser JavaScript
            if not fullscreen_clicked:
                print("Bouton fullscreen non trouvé, utilisation de JavaScript...")
                driver.execute_script("""
                    var elem = document.querySelector('video') || document.documentElement;
                    if (elem.requestFullscreen) {
                        elem.requestFullscreen();
                    } else if (elem.webkitRequestFullscreen) {
                        elem.webkitRequestFullscreen();
                    } else if (elem.mozRequestFullScreen) {
                        elem.mozRequestFullScreen();
                    } else if (elem.msRequestFullscreen) {
                        elem.msRequestFullscreen();
                    }
                """)
                print("✓ Plein écran activé via JavaScript")
                
        except Exception as e:
            print(f"Impossible de passer en plein écran: {e}")
        
        # Attendre que la vidéo soit bien lancée
        print(f"Attente de {WAIT_TIME} secondes pour stabilisation...")
        time.sleep(WAIT_TIME)
        
        # ÉTAPE 4 : Prendre le screenshot
        driver.save_screenshot(str(filename))
        
        file_size = filename.stat().st_size / 1024
        print(f"✓ Snapshot sauvegardé: {filename.name} ({file_size:.1f} KB)")
        
        # ÉTAPE 5 : Sauvegarder les métadonnées en JSON
        metadata = load_metadata(metadata_file)
        metadata["captures"].append({
            "filename": filename.name,
            "timestamp": timestamp.isoformat(),
            "file_size_kb": round(file_size, 2)
        })
        save_metadata(metadata_file, metadata)
        print(f"✓ Métadonnées sauvegardées dans {metadata_file.name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors de la capture: {e}")
        return False

def run_scheduled(driver, SAVE_DIR, WEBCAM_URL, WAIT_TIME, metadata_file):
    """Exécute la capture selon le planning"""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Démarrage de la capture...")
    capture_webcam(driver, SAVE_DIR, WEBCAM_URL, WAIT_TIME, metadata_file)
