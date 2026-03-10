# Fine-Tuning YOLO avec MLflow

Ce dossier contient tous les scripts nécessaires pour fine-tuner un modèle YOLO sur votre dataset d'images annotées, avec tracking des métriques via MLflow.

## Structure du Dataset

Votre dataset doit être organisé comme suit:
```
data/final/
├── train/
│   ├── _annotations.coco.json
│   ├── image1.png
│   ├── image2.png
│   └── ...
├── weights_model/
│   ├── yolo11n.pt
│   ├── yolo11s.pt
│   ├── yolo11m.pt
│   └── ...
└── data.yaml (généré automatiquement)
```

## Lancement Rapide

### Option 1: Pipeline Complet Automatique (RECOMMANDÉ)

Lancez simplement:
```bash
cd src/backend/finetuning
python run_complete_finetuning.py
```

Ce script va automatiquement:
1. Convertir les annotations COCO vers le format YOLO
2. Préparer le dataset
3. Lancer le fine-tuning
4. Tracker toutes les métriques avec MLflow

### Option 2: Étape par Étape

#### Étape 1: Convertir les annotations COCO vers YOLO
```bash
python convert_coco_to_yolo.py
```

#### Étape 2: Lancer le fine-tuning avec MLflow
```bash
python train_with_mlflow.py
```

## Visualiser les Résultats avec MLflow

Une fois l'entraînement lancé, vous pouvez visualiser les métriques en temps réel:

```bash
# Dans un nouveau terminal
mlflow ui
```

Puis ouvrez votre navigateur à: http://localhost:5000

Vous y verrez:
- Courbes d'entraînement (loss, mAP, precision, recall)
- Comparaison entre différentes runs
- Tous les hyperparamètres utilisés
- Modèles sauvegardés

## Configuration du Fine-Tuning

### Modifier les Paramètres d'Entraînement

Éditez le fichier [run_complete_finetuning.py](run_complete_finetuning.py):

```python
# Paramètres d'entraînement
MODEL_NAME = "yolo11n.pt"  # Choisissez votre modèle
EPOCHS = 100               # Nombre d'époques
BATCH_SIZE = 16            # Taille du batch
IMAGE_SIZE = 640           # Taille des images
LEARNING_RATE = 0.01       # Learning rate
PATIENCE = 50              # Early stopping patience
```

### Modèles Disponibles

Dans `data/final/weights_model/`:
- **yolo11n.pt** - Nano (le plus rapide, moins précis)
- **yolo11s.pt** - Small
- **yolo11m.pt** - Medium
- **yolo11l.pt** - Large
- **yolo11x.pt** - Extra Large (le plus précis, plus lent)

## Métriques Trackées par MLflow

### Métriques de Performance
- **mAP@50** - Mean Average Precision à IoU=0.5
- **mAP@50-95** - Mean Average Precision moyennée sur IoU 0.5 à 0.95
- **Precision** - Précision de détection
- **Recall** - Rappel (taux de détection)

### Losses
- **Box Loss** - Perte de localisation des boîtes
- **Class Loss** - Perte de classification
- **DFL Loss** - Distribution Focal Loss

### Hyperparamètres
Tous les hyperparamètres sont automatiquement loggés:
- Learning rate
- Batch size
- Image size
- Optimizer
- Augmentation parameters
- etc.

## Résultats de l'Entraînement

Les résultats sont sauvegardés dans:
```
runs/train/
└── exp_YYYYMMDD_HHMMSS/
    ├── weights/
    │   ├── best.pt    # Meilleur modèle
    │   └── last.pt    # Dernier modèle
    ├── results.csv    # Métriques par époque
    ├── confusion_matrix.png
    ├── results.png
    └── ...
```

## Scripts Disponibles

### 1. convert_coco_to_yolo.py
Convertit les annotations du format COCO JSON vers le format YOLO (txt).

**Usage:**
```python
from convert_coco_to_yolo import prepare_dataset_for_yolo

paths = prepare_dataset_for_yolo(
    train_dir="data/final/train",
    output_base_dir="data/final/yolo_format"
)
```

### 2. train_with_mlflow.py
Lance le fine-tuning avec tracking MLflow.

**Usage:**
```python
from train_with_mlflow import YOLOFineTunerWithMLflow

trainer = YOLOFineTunerWithMLflow(
    model_name="yolo11n.pt",
    experiment_name="mon_experience"
)

results = trainer.train(
    data_yaml="data/final/data.yaml",
    epochs=100,
    batch_size=16,
    imgsz=640
)
```

### 3. run_complete_finetuning.py
Pipeline complet automatique (recommandé).

## Format YOLO

Chaque image doit avoir un fichier `.txt` correspondant avec le format:
```
<class_id> <x_center> <y_center> <width> <height>
```

Toutes les valeurs sont normalisées entre 0 et 1.

Exemple:
```
0 0.5 0.5 0.2 0.3
0 0.7 0.3 0.15 0.25
```

## Résolution de Problèmes

### Erreur: "Fichier data.yaml non trouvé"
Assurez-vous que le fichier `data/final/data.yaml` existe avec le bon contenu.

### Erreur: "CUDA out of memory"
Réduisez le `BATCH_SIZE` dans la configuration.

### Erreur: "No annotations found"
Vérifiez que le fichier `_annotations.coco.json` est présent dans `data/final/train/`.

## Conseils pour de Meilleurs Résultats

1. **Augmentation de données** - Activée par défaut pour améliorer la généralisation
2. **Early stopping** - Arrête automatiquement si pas d'amélioration (patience=50)
3. **Validation** - 20% du dataset utilisé pour validation
4. **Checkpoints** - Le meilleur modèle est automatiquement sauvegardé

## Ressources

- [Documentation YOLO](https://docs.ultralytics.com/)
- [Documentation MLflow](https://mlflow.org/docs/latest/index.html)
- [COCO Format](https://cocodataset.org/#format-data)

## Support

Pour toute question ou problème, vérifiez:
1. Les logs d'entraînement dans le terminal
2. Les métriques dans MLflow UI
3. Les fichiers de résultats dans `runs/train/`
