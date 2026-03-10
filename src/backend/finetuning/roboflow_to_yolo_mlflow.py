"""
Script complet: Téléchargement des données depuis Roboflow + Fine-tuning YOLO11 avec MLflow
"""
import os
import sys
from pathlib import Path
from roboflow import Roboflow
import shutil

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent))

from train_with_mlflow import YOLOFineTunerWithMLflow


def download_dataset_from_roboflow(
    api_key: str,
    workspace: str,
    project: str,
    version: int = 1,
    download_format: str = "yolov11",
    output_dir: str = "data/roboflow_dataset"
):
    """
    Télécharge un dataset depuis Roboflow
    
    Args:
        api_key: Clé API Roboflow
        workspace: Nom du workspace
        project: Nom du projet
        version: Version du dataset
        download_format: Format de téléchargement (yolov11, yolov5, coco, etc.)
        output_dir: Répertoire de destination
        
    Returns:
        Chemin vers le dataset téléchargé
    """
    print("="*80)
    print("TÉLÉCHARGEMENT DES DONNÉES DEPUIS ROBOFLOW")
    print("="*80)
    
    print(f"\nConfiguration:")
    print(f"  • Workspace: {workspace}")
    print(f"  • Project: {project}")
    print(f"  • Version: {version}")
    print(f"  • Format: {download_format}")
    print(f"  • Destination: {output_dir}")
    
    try:
        # Initialiser Roboflow
        print(f"\nConnexion à Roboflow...")
        rf = Roboflow(api_key=api_key)
        
        # Accéder au projet
        print(f"Accès au projet '{project}'...")
        project_obj = rf.workspace(workspace).project(project)
        
        # Récupérer la version
        print(f"Récupération de la version {version}...")
        version_obj = project_obj.version(version)
        
        # Télécharger le dataset
        print(f"\nTéléchargement du dataset (format: {download_format})...")
        dataset = version_obj.download(download_format, location=output_dir)
        
        print(f"\nDataset téléchargé avec succès!")
        print(f"Emplacement: {dataset.location}")
        
        # Afficher les informations sur le dataset
        if hasattr(dataset, 'location'):
            dataset_path = Path(dataset.location)
            
            # Compter les images
            train_images = list((dataset_path / "train" / "images").glob("*")) if (dataset_path / "train" / "images").exists() else []
            val_images = list((dataset_path / "valid" / "images").glob("*")) if (dataset_path / "valid" / "images").exists() else []
            test_images = list((dataset_path / "test" / "images").glob("*")) if (dataset_path / "test" / "images").exists() else []
            
            print(f"\nStatistiques du dataset:")
            print(f"  • Images d'entraînement: {len(train_images)}")
            print(f"  • Images de validation: {len(val_images)}")
            print(f"  • Images de test: {len(test_images)}")
            print(f"  • Total: {len(train_images) + len(val_images) + len(test_images)}")
            
            # Vérifier le fichier data.yaml
            data_yaml = dataset_path / "data.yaml"
            if data_yaml.exists():
                print(f"\nFichier data.yaml trouvé")
                return str(data_yaml), str(dataset_path)
            else:
                print(f"\nFichier data.yaml non trouvé à {data_yaml}")
                return None, str(dataset_path)
        
        return None, None
        
    except Exception as e:
        print(f"\nErreur lors du téléchargement: {e}")
        raise e


def run_complete_pipeline(
    # Paramètres Roboflow
    roboflow_api_key: str,
    roboflow_workspace: str,
    roboflow_project: str,
    roboflow_version: int = 1,
    
    # Paramètres de fine-tuning
    model_name: str = "yolo11n.pt",
    epochs: int = 100,
    batch_size: int = 16,
    imgsz: int = 640,
    lr0: float = 0.01,
    
    # Options
    skip_download: bool = False,
    dataset_path: str = None
):
    """
    Pipeline complet: Téléchargement + Fine-tuning
    
    Args:
        roboflow_api_key: Clé API Roboflow
        roboflow_workspace: Workspace Roboflow
        roboflow_project: Projet Roboflow
        roboflow_version: Version du dataset
        model_name: Modèle YOLO à utiliser
        epochs: Nombre d'époques
        batch_size: Taille du batch
        imgsz: Taille des images
        lr0: Learning rate
        skip_download: Si True, skip le téléchargement et utilise dataset_path
        dataset_path: Chemin vers un dataset existant (si skip_download=True)
    """
    print("\n" + "="*80)
    print("PIPELINE COMPLET: ROBOFLOW -> YOLO11 FINE-TUNING -> MLFLOW")
    print("="*80)
    
    # =========================================================================
    # ÉTAPE 1: Téléchargement depuis Roboflow
    # =========================================================================
    if not skip_download:
        try:
            data_yaml_path, dataset_dir = download_dataset_from_roboflow(
                api_key=roboflow_api_key,
                workspace=roboflow_workspace,
                project=roboflow_project,
                version=roboflow_version,
                download_format="yolov11",
                output_dir="data/roboflow_dataset"
            )
            
            if not data_yaml_path:
                print("\nImpossible de trouver le fichier data.yaml")
                return None
                
        except Exception as e:
            print(f"\nErreur lors du téléchargement: {e}")
            return None
    else:
        print("\nTéléchargement ignoré, utilisation du dataset existant")
        if dataset_path and Path(dataset_path).exists():
            data_yaml_path = str(Path(dataset_path) / "data.yaml")
            dataset_dir = dataset_path
        else:
            print("Dataset path invalide")
            return None
    
    # =========================================================================
    # ÉTAPE 2: Vérification du dataset
    # =========================================================================
    print("\n" + "="*80)
    print("VÉRIFICATION DU DATASET")
    print("="*80)
    
    data_yaml = Path(data_yaml_path)
    if not data_yaml.exists():
        print(f"Fichier data.yaml non trouvé: {data_yaml}")
        return None
    
    print(f"Dataset prêt: {dataset_dir}")
    print(f"Configuration: {data_yaml}")
    
    # Vérifier le modèle pré-entraîné
    model_path = Path(f"data/final/weights_model/{model_name}")
    if not model_path.exists():
        print(f"\nModèle {model_name} non trouvé dans data/final/weights_model/")
        print("Téléchargement automatique par Ultralytics...")
    
    # =========================================================================
    # ÉTAPE 3: Fine-tuning avec MLflow
    # =========================================================================
    print("\n" + "="*80)
    print("FINE-TUNING AVEC MLFLOW")
    print("="*80)
    
    try:
        # Créer le trainer avec MLflow
        trainer = YOLOFineTunerWithMLflow(
            model_name=model_name,
            mlflow_tracking_uri="mlruns",
            experiment_name=f"{roboflow_project}_detection"
        )
        
        # Lancer l'entraînement
        print(f"\nDémarrage de l'entraînement...")
        results = trainer.train(
            data_yaml=str(data_yaml),
            epochs=epochs,
            batch_size=batch_size,
            imgsz=imgsz,
            lr0=lr0,
            optimizer="Adam",
            patience=50,
            project="runs/train",
            save=True,
            plots=True,
            val=True,
            # Augmentation de données
            hsv_h=0.015,
            hsv_s=0.7,
            hsv_v=0.4,
            degrees=0.0,
            translate=0.1,
            scale=0.5,
            fliplr=0.5,
            mosaic=1.0,
            mixup=0.0,
        )
        
        # =====================================================================
        # ÉTAPE 4: Résumé des résultats
        # =====================================================================
        print("\n" + "="*80)
        print("RÉSULTATS DU FINE-TUNING")
        print("="*80)
        
        if results["success"]:
            print("\nFine-tuning terminé avec succès!\n")
            
            metrics = results["metrics"]
            print("Métriques de performance:")
            print(f"  • mAP@50      : {metrics.get('mAP50', 0):.4f}")
            print(f"  • mAP@50-95   : {metrics.get('mAP50_95', 0):.4f}")
            print(f"  • Precision   : {metrics.get('precision', 0):.4f}")
            print(f"  • Recall      : {metrics.get('recall', 0):.4f}")
            
            print(f"\nFichiers générés:")
            print(f"  • Modèle      : {results['model_path']}")
            print(f"  • Résultats   : {results['results_dir']}")
            print(f"  • MLflow Run  : {results['mlflow_run_id']}")
            
            print(f"\nVisualisation MLflow:")
            print(f"  Lancez: mlflow ui")
            print(f"  Puis ouvrez: http://localhost:5000")
            
            print("\n" + "="*80)
            print("PIPELINE TERMINÉ AVEC SUCCÈS!")
            print("="*80)
            
            return results
        else:
            print("\nErreur lors du fine-tuning")
            return None
            
    except Exception as e:
        print(f"\nErreur lors du fine-tuning: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # =========================================================================
    # CONFIGURATION - À PERSONNALISER
    # =========================================================================
    
    # Paramètres Roboflow
    ROBOFLOW_API_KEY = ""  # Insérez votre clé API ici
    ROBOFLOW_WORKSPACE = "placepublique-vldvp"  # Votre workspace
    ROBOFLOW_PROJECT = "dataset"  # Votre projet
    ROBOFLOW_VERSION = 1  # Version du dataset
    
    # Paramètres du modèle
    MODEL_NAME = "yolo11n.pt"  # yolo11n.pt, yolo11s.pt, yolo11m.pt, yolo11l.pt, yolo11x.pt
    
    # Paramètres d'entraînement
    EPOCHS = 100
    BATCH_SIZE = 16
    IMAGE_SIZE = 640
    LEARNING_RATE = 0.01
    
    # Options
    SKIP_DOWNLOAD = False  # Mettre True si dataset déjà téléchargé
    EXISTING_DATASET_PATH = "data/roboflow_dataset/dataset"  # Si SKIP_DOWNLOAD=True
    
    # =========================================================================
    # VÉRIFICATION
    # =========================================================================
    if not ROBOFLOW_API_KEY:
        print("ERREUR: Veuillez configurer votre ROBOFLOW_API_KEY")
        print("\nPour obtenir votre clé API:")
        print("   1. Allez sur https://app.roboflow.com/")
        print("   2. Settings → Roboflow API → Private API Key")
        print("   3. Copiez la clé et collez-la dans ROBOFLOW_API_KEY")
        sys.exit(1)
    
    # =========================================================================
    # LANCER LE PIPELINE
    # =========================================================================
    results = run_complete_pipeline(
        # Roboflow
        roboflow_api_key=ROBOFLOW_API_KEY,
        roboflow_workspace=ROBOFLOW_WORKSPACE,
        roboflow_project=ROBOFLOW_PROJECT,
        roboflow_version=ROBOFLOW_VERSION,
        
        # Fine-tuning
        model_name=MODEL_NAME,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        imgsz=IMAGE_SIZE,
        lr0=LEARNING_RATE,
        
        # Options
        skip_download=SKIP_DOWNLOAD,
        dataset_path=EXISTING_DATASET_PATH if SKIP_DOWNLOAD else None
    )
    
    if results:
        print("\n" + "="*80)
        print("TOUT EST TERMINÉ!")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("UNE ERREUR EST SURVENUE")
        print("="*80)
