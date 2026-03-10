# Fine-tuning YOLO avec Roboflow et MLflow

Ce guide explique comment utiliser le nouveau système de fine-tuning qui intègre Roboflow et MLflow.

## Lancement rapide

### Option 1: Script PowerShell (Recommandé sur Windows)

```powershell
.\launch_roboflow_finetuning.ps1
```

### Option 2: Commande Python directe

```bash
# Activer l'environnement virtuel
.\pb_env\Scripts\Activate.ps1

# Lancer le script
python .\src\backend\finetuning\train_roboflow.py
```

## Modes disponibles

Le script propose **deux modes** d'entraînement :

### 1. Mode TEST (Recommandé pour débuter)
- **10 images** seulement (6 train, 2 val, 2 test)
- **10 époques** d'entraînement
- Temps d'exécution : **~2-5 minutes**
- Idéal pour :
  - Tester la configuration
  - Vérifier que MLflow fonctionne
  - Déboguer le pipeline

### 2. Mode COMPLET
- **Toutes les images** du dataset Roboflow
- **100 époques** d'entraînement
- Temps d'exécution : **Variable selon le nombre d'images**
- Pour l'entraînement final

## Ce que fait le script

1. **Recherche** le dataset en local (Place_publique-4) ou le télécharge depuis Roboflow si nécessaire
2. **Prépare** le dataset :
   - Mode TEST : Crée un subset de 10 images
   - Mode COMPLET : Utilise toutes les images
3. **Lance** le fine-tuning avec tracking MLflow
4. **Sauvegarde** :
   - Le modèle entraîné
   - Les métriques dans MLflow
   - Les courbes d'apprentissage

## Configuration

### Paramètres Roboflow

Dans `train_roboflow.py`, ligne 166-168 :

```python
ROBOFLOW_API_KEY = "UFIRA1AKd6lJ9VxThoY3"
PROJECT_ID = "place_publique"
VERSION = 4  # Changez pour utiliser une autre version
```

### Paramètres d'entraînement

#### Mode TEST (lignes 185-191)

```python
MODEL_NAME = "yolo11n.pt"      # Modèle le plus léger
EPOCHS = 10                     # Peu d'époques pour test rapide
BATCH_SIZE = 4                  # Petit batch
IMAGE_SIZE = 640
LEARNING_RATE = 0.01
PATIENCE = 5                    # Early stopping après 5 époques
```

#### Mode COMPLET (lignes 193-199)

```python
MODEL_NAME = "yolo11n.pt"      # Vous pouvez changer : yolo11s.pt, yolo11m.pt, yolo11l.pt, yolo11x.pt
EPOCHS = 100                    # Plus d'époques pour convergence
BATCH_SIZE = 16                 # Batch plus grand
IMAGE_SIZE = 640
LEARNING_RATE = 0.01
PATIENCE = 50                   # Early stopping après 50 époques
```

## Visualiser les résultats avec MLflow

Après l'entraînement, lancez l'interface MLflow :

```bash
mlflow ui --backend-store-uri mlruns
```

Puis ouvrez votre navigateur sur : **http://localhost:5000**

Vous pourrez voir :
- Les courbes de loss (train/val)
- Les métriques (mAP, precision, recall)
- Les paramètres du modèle
- Le temps d'entraînement
- Les artifacts (modèle, résultats)

## Structure des fichiers générés

```
place_publique/
├── Place_publique-4/           # Dataset téléchargé depuis Roboflow
│   ├── train/
│   ├── valid/
│   ├── test/
│   └── data.yaml
├── data/roboflow_test_subset/  # Subset de 10 images (mode TEST)
│   ├── train/
│   ├── valid/
│   ├── test/
│   └── data.yaml
├── runs/roboflow_train/        # Résultats d'entraînement
│   └── test_yolo11n/           # ou full_yolo11n
│       ├── weights/
│       │   ├── best.pt         # Meilleur modèle
│       │   └── last.pt         # Dernier checkpoint
│       └── results.csv         # Métriques par époque
└── mlruns/                     # Base de données MLflow
```

## Dépannage

### Dataset local non détecté

Le script recherche automatiquement le dataset dans ces emplacements :
- `Place_publique-4/`
- `place_publique-4/`
- `Place_publique/`
- `place_publique/`

**Si votre dataset est ailleurs**, déplacez-le ou créez un lien symbolique :
```powershell
# Exemple si votre dataset est dans un autre dossier
Move-Item "chemin/vers/votre/dataset" "Place_publique-4"
```

### Erreur de téléchargement Roboflow

```
Erreur lors du téléchargement: RuntimeError...
```

**Solutions** :
- Vérifiez votre connexion Internet
- Vérifiez que la clé API est valide
- Vérifiez que le projet "place_publique" existe sur Roboflow
- Vérifiez que la version 4 existe

### Erreur MLflow

```
No module named 'mlflow'
```

**Solution** :
```bash
pip install mlflow
```

### Erreur CUDA/GPU

Si vous avez une erreur CUDA mais voulez utiliser le CPU :

Dans `train_roboflow.py`, modifiez la ligne dans `train_params` :

```python
"device": "cpu",  # Au lieu de "auto"
```

## Conseils

1. **Commencez toujours par le mode TEST** pour vérifier que tout fonctionne
2. **Surveillez les métriques dans MLflow** pendant l'entraînement
3. **Ajustez les hyperparamètres** selon vos besoins :
   - EPOCHS : Plus = meilleur apprentissage (mais plus long)
   - BATCH_SIZE : Plus grand = plus rapide (mais plus de mémoire)
   - LEARNING_RATE : Plus petit = apprentissage plus stable
   - PATIENCE : Plus grand = moins d'early stopping

4. **Choix du modèle** :
   - `yolo11n.pt` : Le plus rapide, moins précis (TEST)
   - `yolo11s.pt` : Bon compromis vitesse/précision
   - `yolo11m.pt` : Plus précis, plus lent
   - `yolo11l.pt` : Très précis, très lent
   - `yolo11x.pt` : Maximum de précision, très très lent

## Support

Pour toute question, consultez :
- [Documentation YOLO](https://docs.ultralytics.com/)
- [Documentation MLflow](https://mlflow.org/docs/latest/index.html)
- [Documentation Roboflow](https://docs.roboflow.com/)
