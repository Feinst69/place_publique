
"""
Exemple simple de téléchargement de dataset depuis Roboflow

NOTE: Pour un pipeline complet avec fine-tuning et MLflow,
utilisez plutôt: roboflow_to_yolo_mlflow.py
ou lancez: .\launch_roboflow_pipeline.ps1
"""
from roboflow import Roboflow

# =============================================================================
# CONFIGURATION - Personnalisez vos informations ici
# =============================================================================
ROBOFLOW_API_KEY = ""  # IMPORTANT: Insérez votre clé API ici
WORKSPACE = "placepublique-vldvp"  # Votre workspace
PROJECT = "dataset"  # Votre projet
VERSION = 1  # Version du dataset
DOWNLOAD_FORMAT = "yolov11"  # Format: yolov11, yolov5, coco, etc.
OUTPUT_LOCATION = "data/roboflow_dataset"  # Dossier de destination

# =============================================================================
# TÉLÉCHARGEMENT
# =============================================================================
if __name__ == "__main__":
    print("[INFO] Téléchargement du dataset depuis Roboflow...")
    print(f"  - Workspace: {WORKSPACE}")
    print(f"  - Projet: {PROJECT}")
    print(f"  - Version: {VERSION}")
    print(f"  - Format: {DOWNLOAD_FORMAT}")
    
    # Connexion à Roboflow
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    
    # Accès au projet
    project = rf.workspace(WORKSPACE).project(PROJECT)
    
    # Récupération de la version
    version = project.version(VERSION)
    
    # Téléchargement (recommandé pour YOLO11)
    dataset = version.download(DOWNLOAD_FORMAT, location=OUTPUT_LOCATION)
    
    print(f"\n[OK] Dataset téléchargé avec succès!")
    print(f"[INFO] Emplacement: {dataset.location}")
    print(f"\n[INFO] Pour lancer le fine-tuning avec MLflow:")
    print(f"   python roboflow_to_yolo_mlflow.py")
    print(f"   ou: .\\launch_roboflow_pipeline.ps1")
