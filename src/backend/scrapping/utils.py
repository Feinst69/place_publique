from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
from pathlib import Path
import base64
import shutil
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
    
    chromium_path = shutil.which("chromium") or shutil.which("chromium-browser")
    if chromium_path:
        chrome_options.binary_location = chromium_path

    chromedriver_path = shutil.which("chromedriver")
    if chromedriver_path:
        driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)
    else:
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

def get_best_video_clip(driver):
    """Trouve la meilleure zone vidéo visible à capturer dans le viewport."""
    script = """
        const selectors = [
          "video",
          ".video-js video",
          ".vjs-tech",
          ".video-js",
          "iframe[src*='skyline']",
          "iframe[src*='player']",
          "iframe",
          "[class*='player' i]"
        ];
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const cx = vw / 2;
        const cy = vh / 2;

        function isVisible(el) {
          const style = window.getComputedStyle(el);
          if (style.display === "none" || style.visibility === "hidden" || parseFloat(style.opacity) === 0) return false;
          const rect = el.getBoundingClientRect();
          return rect.width > 120 && rect.height > 80;
        }

        const candidates = [];
        for (const selector of selectors) {
          for (const el of document.querySelectorAll(selector)) {
            if (!isVisible(el)) continue;
            const rect = el.getBoundingClientRect();
            const x = Math.max(0, rect.left);
            const y = Math.max(0, rect.top);
            const right = Math.min(vw, rect.right);
            const bottom = Math.min(vh, rect.bottom);
            const width = right - x;
            const height = bottom - y;
            if (width < 240 || height < 135) continue;

            const aspect = width / height;
            const area = width * height;
            const ex = x + width / 2;
            const ey = y + height / 2;
            const dist = Math.hypot(ex - cx, ey - cy);
            const aspectPenalty = (aspect < 1.2 || aspect > 2.4) ? 0.4 : 1.0;
            const score = area * aspectPenalty - dist * 200;

            candidates.push({x, y, width, height, selector, score});
          }
        }

        if (!candidates.length) return null;
        candidates.sort((a, b) => b.score - a.score);
        return candidates[0];
    """
    return driver.execute_script(script)

def save_clip_screenshot(driver, filename, clip):
    """Capture un screenshot d'une zone (clip) via le protocole DevTools."""
    result = driver.execute_cdp_cmd("Page.captureScreenshot", {
        "format": "png",
        "clip": {
            "x": float(clip["x"]),
            "y": float(clip["y"]),
            "width": float(clip["width"]),
            "height": float(clip["height"]),
            "scale": 1
        }
    })
    with open(filename, "wb") as f:
        f.write(base64.b64decode(result["data"]))

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
                print(f"Cookies acceptés via: {selector}")
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
        video_element = None
        for selector in video_selectors:
            try:
                element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                element.click()
                print(f"Clic sur la vidéo réussi: {selector}")
                video_clicked = True
                if selector in ("video", "div[class*='player' i]", "iframe"):
                    video_element = element
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
            
            # Tentative 1 : Chercher et cliquer sur le bouton fullscreen
            print("Tentative 1 : Recherche du bouton fullscreen...")
            for selector in fullscreen_selectors:
                try:
                    element = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.click()
                    print(f"Plein écran activé via: {selector} (Tentative 1)")
                    fullscreen_clicked = True
                    break
                except:
                    continue
            
            # Tentative 2 : Si échouée, attendre et réessayer
            if not fullscreen_clicked:
                print("Tentative 1 échouée. Attente 2 secondes...")
                time.sleep(2)
                print("Tentative 2 : Nouvelle recherche du bouton fullscreen...")
                for selector in fullscreen_selectors:
                    try:
                        element = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        element.click()
                        print(f"Plein écran activé via: {selector} (Tentative 2)")
                        fullscreen_clicked = True
                        break
                    except:
                        continue
            
            # Si pas de bouton fullscreen après 2 tentatives, utiliser JavaScript
            if not fullscreen_clicked:
                print("Tentative 2 échouée. Utilisation de JavaScript en fallback...")
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
                print("Plein écran activé via JavaScript (fallback)")
                
        except Exception as e:
            print(f"Impossible de passer en plein écran: {e}")
        
        # Attendre que la vidéo soit bien lancée
        print(f"Attente de {WAIT_TIME} secondes pour stabilisation...")
        time.sleep(WAIT_TIME)
        
        # ÉTAPE 4 : Capture robuste de la zone vidéo (CDP clip), puis fallback
        screenshot_done = False
        clip = get_best_video_clip(driver)
        if clip:
            try:
                save_clip_screenshot(driver, str(filename), clip)
                screenshot_done = True
                print(
                    f"Screenshot clip vidéo via CDP: selector={clip.get('selector')} "
                    f"rect=({int(clip['x'])},{int(clip['y'])},{int(clip['width'])}x{int(clip['height'])})"
                )
            except Exception as e:
                print(f"Échec capture clip CDP: {e}")
        
        if not screenshot_done and video_element is not None:
            try:
                video_element.screenshot(str(filename))
                screenshot_done = True
                print("Fallback: screenshot de l'élément vidéo détecté")
            except Exception as e:
                print(f"Échec fallback élément vidéo: {e}")
        
        if not screenshot_done:
            print("Aucun élément vidéo exploitable trouvé, fallback screenshot page entière")
            driver.save_screenshot(str(filename))
        
        file_size = filename.stat().st_size / 1024
        print(f"Snapshot sauvegardé: {filename.name} ({file_size:.1f} KB)")
        
        # ÉTAPE 5 : Sauvegarder les métadonnées en JSON
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
        print(f"Erreur lors de la capture: {e}")
        return False

def run_scheduled(driver, SAVE_DIR, WEBCAM_URL, WAIT_TIME, metadata_file):
    """Exécute la capture selon le planning"""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Démarrage de la capture...")
    capture_webcam(driver, SAVE_DIR, WEBCAM_URL, WAIT_TIME, metadata_file)
