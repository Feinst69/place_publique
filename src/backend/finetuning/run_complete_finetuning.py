"""
Script principal pour lancer le fine-tuning YOLO complet
Ce script automatise:
1. La conversion des annotations COCO vers YOLO
2. La préparation du dataset
3. Le fine-tuning avec tracking MLflow
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent))

from convert_coco_to_yolo import prepare_dataset_for_yolo
from train_with_mlflow import YOLOFineTunerWithMLflow


def main():
    """
    Pipeline complet de fine-tuning
    """
    print("="*80)
    print("PIPELINE COMPLET DE FINE-TUNING YOLO")
    print("="*80)
    
    # =========================================================================
    # ÉTAPE 1: Configuration
    # =========================================================================
    print("\nÉTAPE 1: Configuration")
    print("-" * 80)
    
    # Chemins
    TRAIN_DIR = "data/final/train"
    OUTPUT_DIR = "data/final/yolo_format"
    DATA_YAML = "data/final/data.yaml"
    
    # Paramètres d'entraînement
    MODEL_NAME = "yolo11n.pt"  # Options: yolo11n.pt, yolo11s.pt, yolo11m.pt, yolo11l.pt, yolo11x.pt
    EPOCHS = 100
    BATCH_SIZE = 16
    IMAGE_SIZE = 640
    LEARNING_RATE = 0.01
    PATIENCE = 50
    
    print(f"  Répertoire d'entraînement: {TRAIN_DIR}")
    print(f"  Répertoire de sortie: {OUTPUT_DIR}")
    print(f"  Fichier de configuration: {DATA_YAML}")
    print(f"  Modèle: {MODEL_NAME}")
    print(f"  Époques: {EPOCHS}")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Taille d'image: {IMAGE_SIZE}")
    
    # =========================================================================
    # ÉTAPE 2: Conversion et préparation du dataset
    # =========================================================================
    print("\n" + "="*80)
    print("ÉTAPE 2: Conversion COCO vers YOLO")
    print("-" * 80)
    
    try:
        # Vérifier si le dataset est déjà converti
        yolo_format_path = Path(OUTPUT_DIR)
        if yolo_format_path.exists() and (yolo_format_path / "images" / "train").exists():
            print("\nDataset YOLO déjà existant")
            response = input("Voulez-vous reconvertir le dataset? (y/N): ").strip().lower()
            
            if response == 'y':
                print("\nReconversion du dataset...")
                paths = prepare_dataset_for_yolo(TRAIN_DIR, OUTPUT_DIR)
            else:
                print("\nUtilisation du dataset existant")
        else:
            print("\nConversion du dataset...")
            paths = prepare_dataset_for_yolo(TRAIN_DIR, OUTPUT_DIR)
            
        print("\nDataset prêt pour l'entraînement")
        
    except Exception as e:
        print(f"\nErreur lors de la préparation du dataset: {e}")
        return
    
    # =========================================================================
    # ÉTAPE 3: Vérification du fichier data.yaml
    # =========================================================================
    print("\n" + "="*80)
    print("ÉTAPE 3: Vérification de la configuration")
    print("-" * 80)
    
    if not Path(DATA_YAML).exists():
        print(f"Fichier {DATA_YAML} non trouvé!")
        print("\nCréez un fichier data.yaml avec le contenu suivant:")
        print(f"""
# Configuration YOLO Dataset
path: {Path(OUTPUT_DIR).absolute()}
train: images/train
val: images/train  # Split automatique si pas de val séparé
nc: 1
names:
  0: person
        """)
        return
    
    print(f"Fichier de configuration trouvé: {DATA_YAML}")
    
    # =========================================================================
    # ÉTAPE 4: Fine-tuning avec MLflow
    # =========================================================================
    print("\n" + "="*80)
    print("ÉTAPE 4: Fine-tuning avec MLflow")
    print("-" * 80)
    
    try:
        # Créer le trainer avec MLflow
        trainer = YOLOFineTunerWithMLflow(
            model_name=MODEL_NAME,
            mlflow_tracking_uri="mlruns",
            experiment_name="place_publique_person_detection"
        )
        
        # Lancer l'entraînement
        print("\nDémarrage de l'entraînement...")
        results = trainer.train(
            data_yaml=DATA_YAML,
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            imgsz=IMAGE_SIZE,
            lr0=LEARNING_RATE,
            optimizer="Adam",
            patience=PATIENCE,
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
        # ÉTAPE 5: Résumé des résultats
        # =====================================================================
        print("\n" + "="*80)
        print("ÉTAPE 5: Résultats du fine-tuning")
        print("="*80)
        
        if results["success"]:
            print("\nFine-tuning terminé avec succès!\n")
            
            metrics = results["metrics"]
            print("Métriques de performance:")
            print(f"  • mAP@50      : {metrics.get('mAP50', 0):.4f} (précision à IoU=0.5)")
            print(f"  • mAP@50-95   : {metrics.get('mAP50_95', 0):.4f} (précision moyenne)")
            print(f"  • Precision   : {metrics.get('precision', 0):.4f} (précision)")
            print(f"  • Recall      : {metrics.get('recall', 0):.4f} (rappel)")
            
            if 'val_box_loss' in metrics:
                print(f"\nPertes de validation:")
                print(f"  • Box Loss    : {metrics.get('val_box_loss', 0):.4f}")
                print(f"  • Class Loss  : {metrics.get('val_cls_loss', 0):.4f}")
                print(f"  • DFL Loss    : {metrics.get('val_dfl_loss', 0):.4f}")
            
            print(f"\nFichiers générés:")
            print(f"  • Modèle best : {results['model_path']}")
            print(f"  • Résultats   : {results['results_dir']}")
            print(f"  • MLflow Run  : {results['mlflow_run_id']}")
            
            print(f"\nVisualisation MLflow:")
            print(f"  1. Ouvrez un terminal")
            print(f"  2. Lancez: mlflow ui")
            print(f"  3. Ouvrez: http://localhost:5000")
            
            print("\n" + "="*80)
            print("PIPELINE TERMINÉ AVEC SUCCÈS!")
            print("="*80)
        else:
            print("\nErreur lors du fine-tuning")
        
    except Exception as e:
        print(f"\nErreur lors du fine-tuning: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    main()
