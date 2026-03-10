"""
Script de fine-tuning YOLO avec MLflow pour tracker les métriques
"""
import os
import mlflow
import mlflow.pytorch
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO
import yaml
import json


class YOLOFineTunerWithMLflow:
    """
    Classe pour le fine-tuning de YOLO avec tracking MLflow
    """
    
    def __init__(
        self,
        model_name: str = "yolo11n.pt",
        model_path: str = None,
        mlflow_tracking_uri: str = "mlruns",
        experiment_name: str = "yolo_finetuning"
    ):
        """
        Initialise le fine-tuner avec MLflow
        
        Args:
            model_name: Nom du modèle (ex: yolo11n.pt, yolo11s.pt)
            model_path: Chemin complet du modèle (optionnel, si None utilise le nom)
            mlflow_tracking_uri: URI pour MLflow tracking
            experiment_name: Nom de l'expérience MLflow
        """
        # Configuration du modèle
        if model_path:
            self.model_path = model_path
        else:
            # Chercher dans le dossier local d'abord
            local_model_path = Path(f"data/final/weights_model/{model_name}")
            if local_model_path.exists():
                self.model_path = str(local_model_path)
            else:
                # Sinon utiliser le nom directement (téléchargement auto si supporté)
                self.model_path = model_name
        
        self.model_name = model_name
        self.model = None
        
        # Configuration MLflow
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        mlflow.set_experiment(experiment_name)
        
        print(f"[INFO] Fine-tuner initialisé:")
        print(f"  - Modèle: {self.model_path}")
        print(f"  - MLflow URI: {mlflow_tracking_uri}")
        print(f"  - Expérience: {experiment_name}")
    
    def load_model(self):
        """Charge le modèle YOLO"""
        if self.model is None:
            print(f"\n[INFO] Chargement du modèle: {self.model_path}")
            self.model = YOLO(self.model_path)
        return self.model
    
    def train(
        self,
        data_yaml: str,
        epochs: int = 100,
        batch_size: int = 16,
        imgsz: int = 640,
        lr0: float = 0.01,
        optimizer: str = "Adam",
        patience: int = 50,
        project: str = "runs/train",
        name: str = None,
        **kwargs
    ):
        """
        Lance l'entraînement avec tracking MLflow
        
        Args:
            data_yaml: Chemin vers le fichier data.yaml
            epochs: Nombre d'époques
            batch_size: Taille du batch
            imgsz: Taille des images
            lr0: Learning rate initial
            optimizer: Type d'optimiseur
            patience: Patience pour early stopping
            project: Dossier du projet
            name: Nom de l'expérience
            **kwargs: Autres paramètres YOLO
        """
        # Charger le modèle
        self.load_model()
        
        # Générer un nom si non fourni
        if name is None:
            name = f"{self.model_name.replace('.pt', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Paramètres d'entraînement
        train_params = {
            "data": data_yaml,
            "epochs": epochs,
            "batch": batch_size,
            "imgsz": imgsz,
            "lr0": lr0,
            "optimizer": optimizer,
            "patience": patience,
            "project": project,
            "name": name,
            "verbose": True,
            "device": 0,  # GPU (nécessite PyTorch avec CUDA installé)
            **kwargs
        }
        
        # Démarrer une run MLflow
        with mlflow.start_run(run_name=name):
            print(f"\n{'='*80}")
            print(f"[INFO] Début du fine-tuning avec MLflow")
            print(f"{'='*80}")
            
            # Logger les paramètres
            print("\n[INFO] Logging des paramètres...")
            mlflow.log_params({
                "model_name": self.model_name,
                "model_path": self.model_path,
                "epochs": epochs,
                "batch_size": batch_size,
                "image_size": imgsz,
                "learning_rate": lr0,
                "optimizer": optimizer,
                "patience": patience
            })
            
            # Logger les autres paramètres custom
            for key, value in kwargs.items():
                try:
                    mlflow.log_param(key, value)
                except:
                    pass
            
            # Lancer l'entraînement
            print("\n[INFO] Entraînement en cours...")
            try:
                results = self.model.train(**train_params)
                
                # Extraire les métriques finales
                metrics = self._extract_final_metrics(results)
                
                # Logger les métriques avec MLflow
                print("\n[INFO] Logging des métriques...")
                for metric_name, metric_value in metrics.items():
                    if isinstance(metric_value, (int, float)):
                        mlflow.log_metric(metric_name, metric_value)
                
                # Logger les courbes d'entraînement si disponibles
                self._log_training_curves(project, name)
                
                # Logger le modèle final
                print("\n[INFO] Sauvegarde du modèle dans MLflow...")
                best_model_path = Path(project) / name / "weights" / "best.pt"
                if best_model_path.exists():
                    mlflow.log_artifact(str(best_model_path), "model")
                
                # Logger le fichier de résultats
                results_csv = Path(project) / name / "results.csv"
                if results_csv.exists():
                    mlflow.log_artifact(str(results_csv), "results")
                
                print(f"\n{'='*80}")
                print("[OK] Fine-tuning terminé avec succès!")
                print(f"{'='*80}")
                print("\n[INFO] Métriques finales:")
                for metric_name, metric_value in metrics.items():
                    if isinstance(metric_value, (int, float)):
                        print(f"  - {metric_name}: {metric_value:.4f}")
                
                print(f"\n[INFO] Résultats sauvegardés dans: {Path(project) / name}")
                print(f"[INFO] Run MLflow: {mlflow.active_run().info.run_id}")
                
                return {
                    "success": True,
                    "metrics": metrics,
                    "model_path": str(best_model_path),
                    "results_dir": str(Path(project) / name),
                    "mlflow_run_id": mlflow.active_run().info.run_id
                }
                
            except Exception as e:
                print(f"\n[ERREUR] Erreur lors de l'entraînement: {str(e)}")
                mlflow.log_param("error", str(e))
                raise e
    
    def _extract_final_metrics(self, results):
        """
        Extrait les métriques finales de l'entraînement
        
        Args:
            results: Résultats de l'entraînement YOLO
            
        Returns:
            Dictionnaire des métriques
        """
        metrics = {}
        
        try:
            # Métriques de précision
            if hasattr(results, 'results_dict'):
                metrics_dict = results.results_dict
                
                # Précision pour la détection d'objets
                if 'metrics/precision(B)' in metrics_dict:
                    metrics['precision'] = metrics_dict['metrics/precision(B)']
                if 'metrics/recall(B)' in metrics_dict:
                    metrics['recall'] = metrics_dict['metrics/recall(B)']
                if 'metrics/mAP50(B)' in metrics_dict:
                    metrics['mAP50'] = metrics_dict['metrics/mAP50(B)']
                if 'metrics/mAP50-95(B)' in metrics_dict:
                    metrics['mAP50_95'] = metrics_dict['metrics/mAP50-95(B)']
                
                # Pertes
                if 'train/box_loss' in metrics_dict:
                    metrics['train_box_loss'] = metrics_dict['train/box_loss']
                if 'train/cls_loss' in metrics_dict:
                    metrics['train_cls_loss'] = metrics_dict['train/cls_loss']
                if 'train/dfl_loss' in metrics_dict:
                    metrics['train_dfl_loss'] = metrics_dict['train/dfl_loss']
                
                # Pertes de validation
                if 'val/box_loss' in metrics_dict:
                    metrics['val_box_loss'] = metrics_dict['val/box_loss']
                if 'val/cls_loss' in metrics_dict:
                    metrics['val_cls_loss'] = metrics_dict['val/cls_loss']
                if 'val/dfl_loss' in metrics_dict:
                    metrics['val_dfl_loss'] = metrics_dict['val/dfl_loss']
            
        except Exception as e:
            print(f"[WARN] Erreur lors de l'extraction des métriques: {e}")
        
        return metrics
    
    def _log_training_curves(self, project: str, name: str):
        """
        Enregistre les courbes d'entraînement dans MLflow
        
        Args:
            project: Dossier du projet
            name: Nom de l'expérience
        """
        try:
            # Chercher les images de résultats
            results_dir = Path(project) / name
            
            # Logger les graphiques si disponibles
            for img_file in results_dir.glob("*.png"):
                mlflow.log_artifact(str(img_file), "plots")
            
            # Logger la confusion matrix si disponible
            confusion_matrix = results_dir / "confusion_matrix.png"
            if confusion_matrix.exists():
                mlflow.log_artifact(str(confusion_matrix), "evaluation")
            
        except Exception as e:
            print(f"[WARN] Erreur lors du logging des courbes: {e}")


def quick_train(
    data_yaml: str = "data/final/data.yaml",
    model_name: str = "yolo11n.pt",
    epochs: int = 100,
    batch_size: int = 16,
    imgsz: int = 640
):
    """
    Fonction pratique pour lancer rapidement un entraînement
    
    Args:
        data_yaml: Chemin vers data.yaml
        model_name: Nom du modèle
        epochs: Nombre d'époques
        batch_size: Taille du batch
        imgsz: Taille des images
    """
    # Créer le trainer
    trainer = YOLOFineTunerWithMLflow(
        model_name=model_name,
        experiment_name="place_publique_detection"
    )
    
    # Lancer l'entraînement
    results = trainer.train(
        data_yaml=data_yaml,
        epochs=epochs,
        batch_size=batch_size,
        imgsz=imgsz,
        project="runs/train",
        save=True,
        plots=True,
        val=True
    )
    
    return results


if __name__ == "__main__":
    # Configuration
    DATA_YAML = "data/final/data.yaml"
    MODEL_NAME = "yolo11n.pt"  # Modèle nano pour test rapide
    EPOCHS = 50  # Augmenter pour un vrai entraînement
    BATCH_SIZE = 16
    IMAGE_SIZE = 640
    
    print("="*80)
    print("FINE-TUNING YOLO AVEC MLFLOW")
    print("="*80)
    
    # Lancer l'entraînement
    results = quick_train(
        data_yaml=DATA_YAML,
        model_name=MODEL_NAME,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        imgsz=IMAGE_SIZE
    )
    
    if results["success"]:
        print("\n" + "="*80)
        print("[OK] ENTRAÎNEMENT TERMINÉ AVEC SUCCÈS!")
        print("="*80)
        print(f"\n[INFO] Métriques principales:")
        print(f"  - mAP50: {results['metrics'].get('mAP50', 0):.4f}")
        print(f"  - mAP50-95: {results['metrics'].get('mAP50_95', 0):.4f}")
        print(f"  - Precision: {results['metrics'].get('precision', 0):.4f}")
        print(f"  - Recall: {results['metrics'].get('recall', 0):.4f}")
        print(f"\n[INFO] Modèle sauvegardé: {results['model_path']}")
        print(f"[INFO] Résultats: {results['results_dir']}")
        print(f"[INFO] MLflow Run ID: {results['mlflow_run_id']}")
        print("\n[INFO] Pour visualiser les résultats MLflow:")
        print("   mlflow ui")
        print("   Puis ouvrir: http://localhost:5000")
