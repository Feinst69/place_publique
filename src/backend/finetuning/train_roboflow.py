"""
Script de fine-tuning YOLO avec données Roboflow et MLflow
Ce script permet de :
1. Télécharger les données depuis Roboflow
2. Créer un subset de test (10 images) ou utiliser le dataset complet
3. Lancer le fine-tuning avec tracking MLflow
"""
import os
import sys
import shutil
from pathlib import Path
from roboflow import Roboflow
import yaml
import random
from train_with_mlflow import YOLOFineTunerWithMLflow


def get_or_download_dataset(project_id: str, version: int = 4, api_key: str = None):
    """
    Recherche le dataset en local ou le télécharge depuis Roboflow si nécessaire
    
    Args:
        project_id: ID du projet
        version: Numéro de version du dataset
        api_key: Clé API Roboflow (seulement si téléchargement nécessaire)
    
    Returns:
        Chemin du dataset
    """
    print("="*80)
    print("RECHERCHE DU DATASET")
    print("="*80)
    
    # Chercher le dataset local
    possible_paths = [
        f"Place_publique-{version}",
        f"{project_id}-{version}",
        f"Place_publique",
        f"{project_id}"
    ]
    
    dataset_path = None
    for path in possible_paths:
        if Path(path).exists():
            dataset_path = path
            print(f"\nDataset trouvé en local: {path}")
            
            # Vérifier qu'il contient bien les données
            has_data_yaml = (Path(path) / "data.yaml").exists()
            has_images = (Path(path) / "train" / "images").exists() or \
                        (Path(path) / "train").exists()
            
            if has_data_yaml and has_images:
                print(f"   Contient data.yaml")
                print(f"   Contient les images")
                
                # Compter les images
                train_dir = Path(path) / "train" / "images" if (Path(path) / "train" / "images").exists() else Path(path) / "train"
                images = list(train_dir.glob("*.jpg")) + list(train_dir.glob("*.png"))
                print(f"   {len(images)} images trouvées")
                
                use_local = input("\nUtiliser ce dataset local? (O/n): ").strip().lower()
                if use_local != 'n':
                    return dataset_path
            break
    
    # Si pas de dataset local ou utilisateur refuse, télécharger
    print("\nTéléchargement du dataset depuis Roboflow...")
    
    if not api_key:
        print("Clé API Roboflow nécessaire pour le téléchargement")
        raise ValueError("API key required for download")
    
    rf = Roboflow(api_key=api_key)
    workspace = rf.workspace()
    project = workspace.project(project_id)
    
    print(f"\n[INFO] Téléchargement de la version {version}...")
    dataset_version = project.version(version)
    dataset = dataset_version.download("yolov11")
    
    print(f"\nDataset téléchargé dans: {dataset.location}")
    return dataset.location


def create_test_subset(dataset_path: str, output_path: str, n_train: int = 6, n_val: int = 2, n_test: int = 2):
    """
    Crée un subset du dataset pour les tests rapides
    
    Args:
        dataset_path: Chemin du dataset complet
        output_path: Chemin de sortie du subset
        n_train: Nombre d'images pour le train
        n_val: Nombre d'images pour la validation
        n_test: Nombre d'images pour le test
    """
    print("\n" + "="*80)
    print("CRÉATION DU SUBSET DE TEST")
    print("="*80)
    
    dataset_path = Path(dataset_path)
    output_path = Path(output_path)
    
    # Créer les dossiers
    for split in ['train', 'valid', 'test']:
        (output_path / split / 'images').mkdir(parents=True, exist_ok=True)
        (output_path / split / 'labels').mkdir(parents=True, exist_ok=True)
    
    # Copier les images et labels
    splits_config = {
        'train': n_train,
        'valid': n_val,
        'test': n_test
    }
    
    for split, n_images in splits_config.items():
        print(f"\n[INFO] Traitement du split '{split}' ({n_images} images)...")
        
        # Lister les images disponibles
        source_images_dir = dataset_path / split / 'images'
        if not source_images_dir.exists():
            print(f"  Répertoire {source_images_dir} non trouvé, skip...")
            continue
        
        available_images = list(source_images_dir.glob('*.jpg')) + list(source_images_dir.glob('*.png'))
        
        if len(available_images) < n_images:
            print(f"  Seulement {len(available_images)} images disponibles (demandé: {n_images})")
            n_images = len(available_images)
        
        # Sélectionner aléatoirement
        selected_images = random.sample(available_images, n_images)
        
        # Copier les fichiers
        for img_path in selected_images:
            # Copier l'image
            dest_img = output_path / split / 'images' / img_path.name
            shutil.copy2(img_path, dest_img)
            
            # Copier le label correspondant
            label_name = img_path.stem + '.txt'
            source_label = dataset_path / split / 'labels' / label_name
            if source_label.exists():
                dest_label = output_path / split / 'labels' / label_name
                shutil.copy2(source_label, dest_label)
        
        print(f"  {n_images} images copiées")
    
    # Créer le fichier data.yaml
    create_data_yaml(output_path, dataset_path)
    
    print(f"\nSubset créé dans: {output_path}")
    return str(output_path)


def create_data_yaml(output_path: Path, source_dataset_path: Path):
    """
    Crée le fichier data.yaml pour le dataset
    
    Args:
        output_path: Chemin du dataset
        source_dataset_path: Chemin du dataset source pour copier les noms de classes
    """
    # Lire le data.yaml source pour obtenir les classes
    source_yaml = source_dataset_path / 'data.yaml'
    if source_yaml.exists():
        with open(source_yaml, 'r') as f:
            source_config = yaml.safe_load(f)
        nc = source_config.get('nc', 1)
        names = source_config.get('names', ['person'])
    else:
        nc = 1
        names = ['person']
    
    # Créer le nouveau data.yaml
    data_config = {
        'path': str(output_path.absolute()),
        'train': 'train/images',
        'val': 'valid/images',
        'test': 'test/images',
        'nc': nc,
        'names': names
    }
    
    yaml_path = output_path / 'data.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(data_config, f, default_flow_style=False)
    
    print(f"\n[INFO] Fichier data.yaml créé: {yaml_path}")


def main():
    """
    Pipeline complet de fine-tuning avec Roboflow
    """
    print("="*80)
    print("FINE-TUNING YOLO AVEC ROBOFLOW + MLFLOW")
    print("="*80)
    
    # =========================================================================
    # CONFIGURATION
    # =========================================================================
    print("\nConfiguration")
    print("-" * 80)
    
    # Configuration Roboflow
    ROBOFLOW_API_KEY = "UFIRA1AKd6lJ9VxThoY3"
    PROJECT_ID = "place_publique"
    VERSION = 4
    
    # Configuration du mode
    print("\nChoisissez le mode d'entraînement:")
    print("  1. Mode TEST - 10 images (6 train, 2 val, 2 test) - Rapide pour tester")
    print("  2. Mode COMPLET - Toutes les images du dataset")
    
    mode = input("\nVotre choix (1 ou 2): ").strip()
    
    TEST_MODE = (mode == "1")
    
    # Dataset paths
    ROBOFLOW_DATASET_DIR = "Place_publique-4"  # Le nom sera généré par Roboflow
    TEST_SUBSET_DIR = "data/roboflow_test_subset"
    
    # Paramètres d'entraînement
    if TEST_MODE:
        print("\nMODE TEST activé")
        MODEL_NAME = "yolo11x.pt"  # YOLO11 xlarge - MAXIMUM de précision
        EPOCHS = 10
        BATCH_SIZE = 1  # Batch minimal pour yolo11x (très gros)
        IMAGE_SIZE = 640
        LEARNING_RATE = 0.01
        PATIENCE = 5
    else:
        print("\nMODE COMPLET activé")
        MODEL_NAME = "yolo11x.pt"  # YOLO11 xlarge - MAXIMUM de précision
        EPOCHS = 100
        BATCH_SIZE = 4  # Batch très réduit pour yolo11x (très gros modèle)
        IMAGE_SIZE = 640
        LEARNING_RATE = 0.01
        PATIENCE = 50
    
    print(f"\n  Modèle: {MODEL_NAME}")
    print(f"  Époques: {EPOCHS}")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Taille d'image: {IMAGE_SIZE}")
    
    # =========================================================================
    # ÉTAPE 1: Récupération du dataset (local ou téléchargement)
    # =========================================================================
    try:
        dataset_path = get_or_download_dataset(
            project_id=PROJECT_ID,
            version=VERSION,
            api_key=ROBOFLOW_API_KEY
        )
    except Exception as e:
        print(f"\nErreur lors de la récupération du dataset: {e}")
        print("\nVérifiez que:")
        print("  - Le dataset existe en local (Place_publique-4)")
        print("  - OU la clé API Roboflow est correcte pour le téléchargement")
        return
    
    # =========================================================================
    # ÉTAPE 2: Préparation du dataset
    # =========================================================================
    if TEST_MODE:
        # Créer un subset de test
        try:
            working_dataset_path = create_test_subset(
                dataset_path=dataset_path,
                output_path=TEST_SUBSET_DIR,
                n_train=6,
                n_val=2,
                n_test=2
            )
            data_yaml_path = str(Path(working_dataset_path) / "data.yaml")
        except Exception as e:
            print(f"\nErreur lors de la création du subset: {e}")
            return
    else:
        # Utiliser le dataset complet
        working_dataset_path = dataset_path
        data_yaml_path = str(Path(working_dataset_path) / "data.yaml")
        print(f"\nUtilisation du dataset complet: {working_dataset_path}")
    
    # =========================================================================
    # ÉTAPE 3: Vérification du dataset
    # =========================================================================
    print("\n" + "="*80)
    print("VÉRIFICATION DU DATASET")
    print("-" * 80)
    
    data_yaml_file = Path(data_yaml_path)
    if not data_yaml_file.exists():
        print(f"Fichier {data_yaml_path} non trouvé!")
        return
    
    with open(data_yaml_path, 'r') as f:
        data_config = yaml.safe_load(f)
    
    # Si le path n'est pas défini, utiliser le répertoire du dataset
    if 'path' not in data_config or data_config['path'] is None:
        dataset_base = Path(working_dataset_path).absolute()
        data_config['path'] = str(dataset_base)
        
        # Mettre à jour le fichier data.yaml
        with open(data_yaml_path, 'w') as f:
            yaml.dump(data_config, f, default_flow_style=False)
        
        print(f"\nPath ajouté au data.yaml: {dataset_base}")
    else:
        dataset_base = Path(data_config['path'])
    
    print(f"\nConfiguration du dataset:")
    print(f"  - Path: {data_config.get('path')}")
    print(f"  - Train: {data_config.get('train')}")
    print(f"  - Val: {data_config.get('val')}")
    print(f"  - Classes: {data_config.get('names')}")
    
    # Compter les images
    train_path = data_config.get('train', '').replace('../', '')
    train_images_dir = dataset_base / train_path
    if train_images_dir.exists():
        train_images = list(train_images_dir.glob('*.jpg')) + \
                       list(train_images_dir.glob('*.png'))
        print(f"  - Nombre d'images d'entraînement: {len(train_images)}")
    else:
        print(f"  Répertoire d'entraînement non trouvé: {train_images_dir}")
    
    # =========================================================================
    # ÉTAPE 4: Fine-tuning avec MLflow
    # =========================================================================
    print("\n" + "="*80)
    print("FINE-TUNING AVEC MLFLOW")
    print("-" * 80)
    
    # Initialiser le fine-tuner
    fine_tuner = YOLOFineTunerWithMLflow(
        model_name=MODEL_NAME,
        mlflow_tracking_uri="mlruns",
        experiment_name="yolo_roboflow_finetuning"
    )
    
    # Lancer l'entraînement
    try:
        results = fine_tuner.train(
            data_yaml=data_yaml_path,
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            imgsz=IMAGE_SIZE,
            lr0=LEARNING_RATE,
            optimizer="Adam",
            patience=PATIENCE,
            project="runs/roboflow_train",
            name=f"{'test' if TEST_MODE else 'full'}_{MODEL_NAME.replace('.pt', '')}"
        )
        
        print("\n" + "="*80)
        print("ENTRAÎNEMENT TERMINÉ AVEC SUCCÈS!")
        print("="*80)
        print(f"\nRésultats:")
        print(f"  - Modèle sauvegardé: {results['model_path']}")
        print(f"  - Répertoire de résultats: {results['results_dir']}")
        print(f"  - MLflow Run ID: {results['mlflow_run_id']}")
        
        print(f"\nPour visualiser les résultats dans MLflow:")
        print(f"   mlflow ui --backend-store-uri mlruns")
        
    except Exception as e:
        print(f"\nErreur lors de l'entraînement: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
