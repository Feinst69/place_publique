# Fine-Tuning YOLO avec Grid Search

Ce dossier contient des outils pour fine-tuner des modèles YOLO avec recherche de paramètres optimaux (grid search).

## Fichiers

- **`yolo_model.py`** : Classe `YOLOFineTuner` avec tous les paramètres configurables de YOLO
- **`grid_search_training.py`** : Script pour effectuer un grid search automatique
- **`example_usage.py`** : Exemples d'utilisation simples

## Installation

```bash
pip install ultralytics pandas pyyaml tqdm matplotlib seaborn
```

## Structure du Dataset

Votre dataset YOLO doit avoir cette structure :

```
dataset/
├── data.yaml          # Configuration du dataset
├── images/
│   ├── train/        # Images d'entraînement
│   └── val/          # Images de validation
└── labels/
    ├── train/        # Labels au format YOLO (.txt)
    └── val/          # Labels de validation
```

Exemple de fichier `data.yaml` :

```yaml
path: /path/to/dataset  # Chemin racine du dataset
train: images/train     # Chemin relatif vers images d'entraînement
val: images/val         # Chemin relatif vers images de validation

# Classes
names:
  0: person
  1: car
  2: bicycle
  # ... autres classes
```

## Utilisation Simple

### 1. Entraîner un modèle avec des paramètres spécifiques

```python
from yolo_model import YOLOFineTuner

# Créer le fine-tuner
trainer = YOLOFineTuner(
    model_name="yolo11n.pt",
    epochs=100,
    batch_size=16,
    lr0=0.01,
    optimizer="Adam"
)

# Lancer l'entraînement
results = trainer.train(data_yaml="path/to/data.yaml")

# Afficher les résultats
print(f"mAP50-95: {results['metrics'].get('mAP50-95', 0):.4f}")
```

### 2. Grid Search Minimal (Test Rapide)

```python
from grid_search_training import GridSearchTrainer, get_minimal_grid

# Configuration
trainer = GridSearchTrainer(
    data_yaml="path/to/data.yaml",
    param_grid=get_minimal_grid(),
    metric_to_optimize="mAP50-95"
)

# Lancer le grid search
results = trainer.run()

# Analyser les résultats
trainer.analyze_results()
```

### 3. Grid Search Complet

```python
from grid_search_training import GridSearchTrainer, get_default_params

# Grid search exhaustif (peut prendre plusieurs jours!)
trainer = GridSearchTrainer(
    data_yaml="path/to/data.yaml",
    param_grid=get_default_params(),
    metric_to_optimize="mAP50-95",
    max_combinations=50  # Limiter à 50 combinaisons
)

results = trainer.run()
trainer.analyze_results()
```

### 4. Grid Search Personnalisé

```python
from grid_search_training import GridSearchTrainer

# Définir vos propres paramètres à tester
custom_grid = {
    "model_name": ["yolo11n.pt", "yolo11s.pt"],
    "epochs": [50, 100],
    "batch_size": [8, 16, 32],
    "lr0": [0.001, 0.01],
    "optimizer": ["Adam", "SGD", "AdamW"],
    "dropout": [0.0, 0.1, 0.2],
    "mosaic": [0.0, 1.0],
    "mixup": [0.0, 0.15],
}

trainer = GridSearchTrainer(
    data_yaml="path/to/data.yaml",
    param_grid=custom_grid,
    metric_to_optimize="mAP50-95"
)

results = trainer.run()
```

## Paramètres Disponibles

### Modèles
- `model_name`: "yolo11n.pt", "yolo11s.pt", "yolo11m.pt", "yolo11l.pt", "yolo11x.pt"
- `yolov8n.pt`, etc.

### Entraînement
- `epochs`: Nombre d'époques (ex: 50, 100, 150)
- `batch_size`: Taille du batch (ex: 8, 16, 32)
- `imgsz`: Taille des images (ex: 640, 1280)

### Optimisation
- `optimizer`: "Adam", "AdamW", "SGD", "NAdam", "RAdam", "RMSProp"
- `lr0`: Learning rate initial (ex: 0.001, 0.01, 0.1)
- `lrf`: Learning rate final en fraction de lr0 (ex: 0.01, 0.1)
- `momentum`: Pour SGD (ex: 0.9, 0.937)
- `weight_decay`: Régularisation L2 (ex: 0.0005, 0.001)

### Data Augmentation
- `hsv_h`: Augmentation de teinte (ex: 0.0, 0.015)
- `hsv_s`: Augmentation de saturation (ex: 0.0, 0.7)
- `hsv_v`: Augmentation de valeur (ex: 0.0, 0.4)
- `degrees`: Rotation en degrés (ex: 0.0, 10.0, 30.0)
- `translate`: Translation (ex: 0.0, 0.1, 0.2)
- `scale`: Mise à l'échelle (ex: 0.5, 0.9)
- `flipud`: Flip vertical (ex: 0.0, 0.5)
- `fliplr`: Flip horizontal (ex: 0.0, 0.5)
- `mosaic`: Augmentation mosaic (ex: 0.0, 1.0)
- `mixup`: Augmentation mixup (ex: 0.0, 0.15)
- `copy_paste`: Copy-paste augmentation (ex: 0.0, 0.1)

### Régularisation
- `dropout`: Dropout (ex: 0.0, 0.1, 0.2)

### Performance
- `patience`: Early stopping (ex: 30, 50, 100)
- `amp`: Automatic Mixed Precision (True/False)

## Résultats du Grid Search

Après l'exécution, les résultats sont sauvegardés dans `runs/grid_search/session_YYYYMMDD_HHMMSS/` :

```
session_YYYYMMDD_HHMMSS/
├── grid_search_config.json    # Configuration du grid search
├── results.json                # Résultats complets (JSON)
├── results.csv                 # Résultats en CSV (facile à analyser)
├── best_config.json            # Meilleure configuration trouvée
├── best_params.yaml            # Paramètres du meilleur modèle
├── summary_report.txt          # Rapport de synthèse
├── analysis_plots.png          # Graphiques d'analyse
├── statistics.txt              # Statistiques détaillées
└── experiments/                # Tous les modèles entraînés
    ├── exp_000_yolo11n_e50_b16_lr0.01_Adam/
    ├── exp_001_yolo11n_e100_b16_lr0.01_SGD/
    └── ...
```

## Métriques d'Optimisation

Vous pouvez optimiser selon différentes métriques :
- `mAP50-95`: mAP à IoU de 0.5 à 0.95 (métrique standard COCO)
- `mAP50`: mAP à IoU de 0.5
- `precision`: Précision
- `recall`: Rappel

Exemple :
```python
trainer = GridSearchTrainer(
    data_yaml="path/to/data.yaml",
    param_grid=my_grid,
    metric_to_optimize="precision"  # Optimiser pour la précision
)
```

## Conseils

### Pour un test rapide (5-10 minutes)
```python
quick_test = {
    "model_name": ["yolo11n.pt"],
    "epochs": [5],
    "batch_size": [16],
    "lr0": [0.01],
}
```

### Pour une exploration complète (plusieurs heures/jours)
```python
full_search = get_default_params()
# Limiter le nombre de combinaisons
trainer = GridSearchTrainer(
    ...,
    param_grid=full_search,
    max_combinations=100  # Teste 100 combinaisons aléatoires
)
```

### Pour focus sur l'augmentation de données
```python
from grid_search_training import get_aggressive_augmentation_grid
trainer = GridSearchTrainer(
    data_yaml="path/to/data.yaml",
    param_grid=get_aggressive_augmentation_grid()
)
```

## Analyse des Résultats

Après le grid search, analysez les résultats :

```python
# Charger les résultats
import pandas as pd
df = pd.read_csv("runs/grid_search/session_XXX/results.csv")

# Voir les meilleures expériences
top_10 = df.nlargest(10, 'metric_mAP50-95')
print(top_10[['experiment_name', 'metric_mAP50-95']])

# Analyser l'impact d'un paramètre
impact_lr = df.groupby('param_lr0')['metric_mAP50-95'].mean()
print(impact_lr)
```

## Exemple Complet

Voir le fichier `example_usage.py` pour des exemples complets et détaillés.

## Troubleshooting

### Erreur "CUDA out of memory"
- Réduire `batch_size`
- Réduire `imgsz`
- Utiliser `amp=True`

### Entraînement très lent
- Augmenter `workers` (ex: 8, 16)
- Utiliser `cache=True` pour cacher les images en mémoire
- Réduire `imgsz` si possible

### Mauvaises performances
- Augmenter `epochs`
- Essayer différents `optimizer`
- Augmenter la data augmentation
- Essayer un modèle plus gros (yolo11s, yolo11m)

## Support

Pour plus d'informations sur YOLO et ultralytics :
- Documentation : https://docs.ultralytics.com/
- GitHub : https://github.com/ultralytics/ultralytics
