# Techniques Selenium - Webcam Capture

## Setup Browser

- **Chrome headless mode**
- Options: `--no-sandbox`, `--disable-dev-shm-usage`, `--window-size=1920,1080`
- User-agent personnalisé anti-détection bot

## Gestion Cookies

- Multiple CSS selectors: `button[id*='accept']`, `button[class*='consent']`
- WebDriverWait timeout 2s par sélecteur
- Loop sur liste sélecteurs jusqu'à succès

## Click Vidéo

- Sélecteurs: `video`, `button[aria-label*='play']`, `iframe`
- Fallback: `ActionChains.move_by_offset().click()`
- `time.sleep()` après chaque action

## Fullscreen

- **Méthode 1**: Bouton fullscreen via CSS selectors
- **Méthode 2**: JavaScript `requestFullscreen()` sur `<video>`
- Gestion cross-browser: `webkitRequestFullscreen`, `mozRequestFullScreen`

## Screenshot

- `driver.save_screenshot(filename)`
- Timestamp format: `YYYYMMDD_HHMMSS`
- Stockage en PNG

## Scheduling

- Module `schedule` pour captures périodiques
- `schedule.every(X).minutes.do(function)`
- Loop infinie avec `schedule.run_pending()`

## Error Handling

- `Try/except` sur chaque étape
- Continue sur échec de sélecteur individuel
- Logs détaillés pour debugging