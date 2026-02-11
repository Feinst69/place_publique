"""
Classe YOLO configurable pour le fine-tuning avec grid search
"""
from ultralytics import YOLO
import torch
from typing import Optional, Dict, Any, List
import yaml
import os
from datetime import datetime
from pathlib import Path
import pandas as pd


class YOLOFineTuner:
    """
    Classe wrapper pour le fine-tuning de modèles YOLO avec paramètres configurables
    """
    
    def __init__(
        self,
        # Paramètres du modèle
        model_name: str = "yolo11n.pt",
        model_path: Optional[str] = None,
        
        # Paramètres d'entraînement
        epochs: int = 100,
        batch_size: int = 16,
        imgsz: int = 640,
        
        # Optimiseur
        optimizer: str = "Adam",  # SGD, Adam, AdamW, NAdam, RAdam, RMSProp
        lr0: float = 0.01,  # learning rate initial
        lrf: float = 0.01,  # learning rate final (lr0 * lrf)
        momentum: float = 0.937,
        weight_decay: float = 0.0005,
        
        # Scheduler
        warmup_epochs: float = 3.0,
        warmup_momentum: float = 0.8,
        warmup_bias_lr: float = 0.1,
        
        # Data augmentation
        hsv_h: float = 0.015,  # Hue augmentation
        hsv_s: float = 0.7,    # Saturation augmentation
        hsv_v: float = 0.4,    # Value augmentation
        degrees: float = 0.0,  # Rotation
        translate: float = 0.1,  # Translation
        scale: float = 0.5,    # Scale
        shear: float = 0.0,    # Shear
        perspective: float = 0.0,  # Perspective
        flipud: float = 0.0,   # Flip up-down
        fliplr: float = 0.5,   # Flip left-right
        mosaic: float = 1.0,   # Mosaic augmentation
        mixup: float = 0.0,    # Mixup augmentation
        copy_paste: float = 0.0,  # Copy-paste augmentation
        
        # Loss weights
        box_gain: float = 7.5,
        cls_gain: float = 0.5,
        dfl_gain: float = 1.5,
        
        # Regularization
        dropout: float = 0.0,
        
        # Performance
        patience: int = 50,  # Early stopping patience
        close_mosaic: int = 10,  # Epochs to disable mosaic
        amp: bool = True,  # Automatic Mixed Precision
        
        # Hardware
        device: str = "auto",  # cuda, cpu, mps, auto
        workers: int = 8,
        
        # Autres
        seed: int = 0,
        deterministic: bool = True,
        save: bool = True,
        save_period: int = -1,  # Save checkpoint every x epochs (-1 = disabled)
        cache: bool = False,  # Cache images for faster training
        project: str = "runs/train",
        name: str = "exp",
        exist_ok: bool = False,
        pretrained: bool = True,
        verbose: bool = True,
        
        # Validation
        val: bool = True,
        fraction: float = 1.0,  # Dataset fraction to train on
    ):
        """
        Initialise le fine-tuner avec tous les paramètres configurables
        
        Args:
            model_name: Nom du modèle de base (yolo11n.pt, yolo11s.pt, etc.)
            model_path: Chemin complet vers le modèle (si fourni, écrase model_name)
            epochs: Nombre d'époques d'entraînement
            batch_size: Taille du batch
            imgsz: Taille des images (640, 1280, etc.)
            optimizer: Type d'optimiseur
            lr0: Learning rate initial
            lrf: Learning rate final (fraction de lr0)
            momentum: Momentum pour SGD
            weight_decay: Weight decay pour régularisation L2
            ... (voir paramètres ci-dessus)
        """
        # Configuration du modèle
        if model_path:
            self.model_path = model_path
        else:
            self.model_path = f"data/final/weights_model/{model_name}"
        
        self.model_name = model_name
        self.model = None
        
        # Stockage de tous les paramètres
        self.params = {
            # Training
            "epochs": epochs,
            "batch": batch_size,
            "imgsz": imgsz,
            
            # Optimizer
            "optimizer": optimizer,
            "lr0": lr0,
            "lrf": lrf,
            "momentum": momentum,
            "weight_decay": weight_decay,
            
            # Scheduler
            "warmup_epochs": warmup_epochs,
            "warmup_momentum": warmup_momentum,
            "warmup_bias_lr": warmup_bias_lr,
            
            # Augmentation
            "hsv_h": hsv_h,
            "hsv_s": hsv_s,
            "hsv_v": hsv_v,
            "degrees": degrees,
            "translate": translate,
            "scale": scale,
            "shear": shear,
            "perspective": perspective,
            "flipud": flipud,
            "fliplr": fliplr,
            "mosaic": mosaic,
            "mixup": mixup,
            "copy_paste": copy_paste,
            
            # Loss
            "box": box_gain,
            "cls": cls_gain,
            "dfl": dfl_gain,
            
            # Regularization
            "dropout": dropout,
            
            # Performance
            "patience": patience,
            "close_mosaic": close_mosaic,
            "amp": amp,
            
            # Hardware
            "device": device,
            "workers": workers,
            
            # Misc
            "seed": seed,
            "deterministic": deterministic,
            "save": save,
            "save_period": save_period,
            "cache": cache,
            "project": project,
            "name": name,
            "exist_ok": exist_ok,
            "pretrained": pretrained,
            "verbose": verbose,
            
            # Validation
            "val": val,
            "fraction": fraction,
        }
        
        self.train_results = None
        
    def load_model(self):
        """Charge le modèle YOLO"""
        if self.model is None:
            print(f"Chargement du modèle: {self.model_path}")
            self.model = YOLO(self.model_path)
        return self.model
    
    def train(self, data_yaml: str, **override_params) -> Dict[str, Any]:
        """
        Lance l'entraînement du modèle
        
        Args:
            data_yaml: Chemin vers le fichier data.yaml (dataset config)
            **override_params: Paramètres supplémentaires qui écrasent la config par défaut
            
        Returns:
            Dictionnaire contenant les résultats de l'entraînement
        """
        # Charger le modèle
        self.load_model()
        
        # Fusionner les paramètres
        train_params = self.params.copy()
        train_params.update(override_params)
        train_params["data"] = data_yaml
        
        print(f"\n{'='*60}")
        print(f"Début de l'entraînement avec les paramètres:")
        print(f"{'='*60}")
        for key, value in train_params.items():
            print(f"  {key}: {value}")
        print(f"{'='*60}\n")
        
        # Lancer l'entraînement
        try:
            results = self.model.train(**train_params)
            self.train_results = results
            
            # Extraire les métriques principales
            metrics = self._extract_metrics(results)
            
            return {
                "success": True,
                "model_path": self.model_path,
                "params": train_params,
                "metrics": metrics,
                "results": results
            }
            
        except Exception as e:
            print(f"Erreur lors de l'entraînement: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "model_path": self.model_path,
                "params": train_params
            }
    
    def _extract_metrics(self, results) -> Dict[str, float]:
        """
        Extrait les métriques principales des résultats
        
        Args:
            results: Résultats de l'entraînement YOLO
            
        Returns:
            Dictionnaire de métriques
        """
        try:
            # Accéder aux métriques finales
            metrics = {}
            
            # Métriques de validation
            if hasattr(results, 'results_dict'):
                metrics = results.results_dict
            elif hasattr(results, 'maps'):
                metrics['mAP50'] = results.maps[0] if len(results.maps) > 0 else 0
                metrics['mAP50-95'] = results.maps[1] if len(results.maps) > 1 else 0
            
            # Essayer d'accéder aux métriques via le validateur
            if hasattr(results, 'validator') and results.validator:
                validator = results.validator
                if hasattr(validator, 'metrics'):
                    m = validator.metrics
                    metrics.update({
                        'precision': getattr(m, 'p', [0])[0] if hasattr(m, 'p') else 0,
                        'recall': getattr(m, 'r', [0])[0] if hasattr(m, 'r') else 0,
                        'mAP50': getattr(m, 'ap50', 0) if hasattr(m, 'ap50') else 0,
                        'mAP50-95': getattr(m, 'ap', 0) if hasattr(m, 'ap') else 0,
                    })
            
            # Si pas de métriques, lire depuis les fichiers CSV
            if not metrics:
                results_dir = Path(results.save_dir) if hasattr(results, 'save_dir') else None
                if results_dir and results_dir.exists():
                    csv_file = results_dir / 'results.csv'
                    if csv_file.exists():
                        df = pd.read_csv(csv_file)
                        # Prendre la dernière ligne
                        last_row = df.iloc[-1]
                        metrics = {
                            'mAP50': last_row.get('metrics/mAP50(B)', 0),
                            'mAP50-95': last_row.get('metrics/mAP50-95(B)', 0),
                        }
            
            return metrics
            
        except Exception as e:
            print(f"Erreur lors de l'extraction des métriques: {str(e)}")
            return {}
    
    def validate(self, data_yaml: str, **kwargs) -> Dict[str, Any]:
        """
        Valide le modèle sur un dataset
        
        Args:
            data_yaml: Chemin vers le fichier data.yaml
            **kwargs: Paramètres supplémentaires pour la validation
            
        Returns:
            Résultats de validation
        """
        self.load_model()
        
        val_params = {
            "data": data_yaml,
            "imgsz": self.params["imgsz"],
            "batch": self.params["batch"],
            "device": self.params["device"],
        }
        val_params.update(kwargs)
        
        results = self.model.val(**val_params)
        return results
    
    def get_config(self) -> Dict[str, Any]:
        """Retourne la configuration complète"""
        return {
            "model_path": self.model_path,
            "model_name": self.model_name,
            "params": self.params
        }
    
    def save_config(self, filepath: str):
        """Sauvegarde la configuration dans un fichier YAML"""
        config = self.get_config()
        with open(filepath, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        print(f"Configuration sauvegardée: {filepath}")
    
    @classmethod
    def from_config(cls, filepath: str):
        """Charge une configuration depuis un fichier YAML"""
        with open(filepath, 'r') as f:
            config = yaml.safe_load(f)
        
        return cls(
            model_name=config.get('model_name', 'yolo11n.pt'),
            model_path=config.get('model_path'),
            **config.get('params', {})
        )


def get_default_params() -> Dict[str, List[Any]]:
    """
    Retourne les paramètres par défaut pour un grid search
    
    Returns:
        Dictionnaire avec des listes de valeurs à tester pour chaque paramètre
    """
    return {
        # Modèles à tester
        "model_name": ["yolo11n.pt", "yolo11s.pt", "yolo11m.pt"],
        
        # Training hyperparams
        "epochs": [50, 100, 150],
        "batch_size": [8, 16, 32],
        "imgsz": [640, 1280],
        
        # Optimizer
        "optimizer": ["Adam", "AdamW", "SGD"],
        "lr0": [0.001, 0.01, 0.1],
        "lrf": [0.01, 0.1],
        "weight_decay": [0.0005, 0.001, 0.005],
        
        # Data augmentation
        "mosaic": [0.0, 1.0],
        "mixup": [0.0, 0.15],
        "degrees": [0.0, 10.0],
        "translate": [0.1, 0.2],
        "scale": [0.5, 0.9],
        "fliplr": [0.5],
        
        # Regularization
        "dropout": [0.0, 0.1, 0.2],
        
        # Performance
        "patience": [30, 50, 100],
        "amp": [True, False],
    }


def get_minimal_grid() -> Dict[str, List[Any]]:
    """
    Retourne un grid search minimal pour tests rapides
    """
    return {
        "model_name": ["yolo11n.pt"],
        "epochs": [10, 20],
        "batch_size": [16],
        "lr0": [0.001, 0.01],
        "optimizer": ["Adam", "SGD"],
    }


def get_aggressive_augmentation_grid() -> Dict[str, List[Any]]:
    """
    Grid search focalisé sur l'augmentation de données
    """
    return {
        "model_name": ["yolo11n.pt"],
        "epochs": [100],
        "batch_size": [16],
        
        # Forte augmentation
        "hsv_h": [0.015, 0.05],
        "hsv_s": [0.7, 0.9],
        "hsv_v": [0.4, 0.6],
        "degrees": [0.0, 15.0, 30.0],
        "translate": [0.1, 0.2, 0.3],
        "scale": [0.5, 0.7, 0.9],
        "mosaic": [0.5, 1.0],
        "mixup": [0.0, 0.15, 0.3],
        "copy_paste": [0.0, 0.1],
    }
