# Place Publique

Système de surveillance webcam avec détection d'objets (`person`, `car`) basé sur YOLO, API Flask et dashboard temps réel.

## Fonctionnalités
- Capture continue d'images webcam (rotation Cardiff / Murcia / La Palma).
- Inférence YOLO sur chaque image capturée.
- Sauvegarde des images annotées + résultats JSON.
- Stockage des résultats en base SQLite.
- Dashboard live (`/`) + page statistiques (`/stats`).
- Entraînement / fine-tuning YOLO (scripts `src/backend/finetuning`).

## Structure du projet
- `src/backend/api_flask/app.py` : API Flask + Socket.IO + inférence YOLO.
- `src/backend/scrapping/` : capture webcam Selenium.
- `src/backend/pipeline/run_all_wsl.py` : lanceur principal (API + scraping).
- `src/database/` : accès DB SQLite.
- `src/frontend/` : interface web (`index.html`, `stats.html`).
- `data/final/weights_model/` : poids YOLO (`.pt`).
- `architecture.md` : proposition d'architecture production.

## Prérequis
- Python 3.11
- Docker + Docker Compose (recommandé)
- Modèles présents dans `data/final/weights_model/`

## Lancement rapide (Docker)
Depuis la racine du projet:

```bash
docker compose down --remove-orphans
docker compose up -d --build
docker compose logs -f
```

Accès UI:
- `http://localhost:5000`
- Si problème de forwarding WSL: `http://<IP_WSL>:5000`

## Configuration modèles YOLO
Dans `docker-compose.yml`:

- `MODEL_PERSON_PATH=/app/data/final/weights_model/yolo11l.pt`
- `MODEL_CAR_PATH=/app/data/final/weights_model/yolo11l.pt`
- `YOLO_CONF_THRESHOLD=0.15`

Exemple pour passer en `yolo11x`:

```yaml
- MODEL_PERSON_PATH=/app/data/final/weights_model/yolo11x.pt
- MODEL_CAR_PATH=/app/data/final/weights_model/yolo11x.pt
```

Puis:

```bash
docker compose up -d --build
```

## Lancement local (sans Docker)

```bash
cd ~/projetcs/place_publique
source venv_yolo/bin/activate
python src/backend/pipeline/run_all_wsl.py
```

Mode API seul:

```bash
python src/backend/pipeline/run_all_wsl.py --no-scraping
```

## Données générées
- Images annotées: `data/final/image_annoted/`
- JSON inférence: `data/final/yolo_json/`
- DB principale: `data/final/db_detection_main.db`
- DB classes: `data/final/db_detection_class.db`

## Endpoints utiles
- `GET /` : dashboard live.
- `GET /stats` : dashboard statistiques.
- `GET /api/detections?limit=10`
- `GET /api/stats`
- `GET /api/db_stats`
- `GET /image/<filename>`

## Dépannage
### 1) Page stats bloquée sur "Chargement"
- Vérifier les logs JS/Flask.
- Rebuild complet:
  ```bash
  docker compose down
  docker compose up -d --build
  ```

### 2) Aucune détection
- Vérifier les logs au démarrage:
  - `Model person: ...`
  - `Model car: ...`
  - `Classes person utilisées: ...`
  - `Classes car utilisées: ...`
- Baisser `YOLO_CONF_THRESHOLD` (ex: `0.10`).
- Vérifier que le modèle `.pt` existe bien dans `data/final/weights_model/`.

### 3) Port déjà utilisé (`5000`)
- Soit arrêter le process local,
- soit lancer avec un autre port:
  ```bash
  HOST_PORT=5050 docker compose up -d --build
  ```

## Notes
- SQLite est utilisé pour le dev. Pour la prod, voir `architecture.md` (PostgreSQL + queue + monitoring).
- Le scraping webcam dépend de la disponibilité des sites source et des bannières cookies.
