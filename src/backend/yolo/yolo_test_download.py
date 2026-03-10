"""
download_model.py - Script pour télécharger un modèle YOLO pré-entraîné
Exécutez ce script AVANT save_model.py si vous n'avez pas encore de modèle
"""
from ultralytics import YOLO
import os

def download_yolo_model(model_name='yolo11n.pt'):
    """
    Télécharge un modèle YOLO pré-entraîné
    
    Args:
        model_name: Nom du modèle à télécharger
                   Options: yolo11n, yolo11s, yolo11m, yolo11l, yolo11x
                   OU: yolov8n, yolov8s, yolov8m, yolov8l, yolov8x
    """
    print("=== Téléchargement d'un modèle YOLO ===\n")
    
    # Informations sur les modèles YOLO11
    models_info = {
        'yolo11n.pt': 'Nano - Le plus rapide et léger (~2.6M paramètres)',
        'yolo11s.pt': 'Small - Bon équilibre vitesse/précision (~9.4M paramètres)',
        'yolo11m.pt': 'Medium - Plus précis (~20.1M paramètres)',
        'yolo11l.pt': 'Large - Haute précision (~25.3M paramètres)',
        'yolo11x.pt': 'XLarge - Maximum de précision (~56.9M paramètres)',
        'yolov8n.pt': 'YOLOv8 Nano - Alternative stable',
        'yolov8s.pt': 'YOLOv8 Small - Alternative stable',
    }
    
    print("Modèles disponibles:")
    for model, desc in models_info.items():
        marker = " <- Choisi" if model == model_name else ""
        print(f"  - {model}: {desc}{marker}")
    
    print(f"\nTéléchargement de: {model_name}")
    print("Cela peut prendre quelques minutes selon votre connexion...\n")
    
    try:
        # Extraire le nom sans l'extension .pt
        model_base_name = model_name.replace('.pt', '')
        
        # Télécharger et charger le modèle (YOLO télécharge automatiquement)
        print(f"Tentative de téléchargement: {model_base_name}")
        model = YOLO(model_base_name)  # Sans le .pt, YOLO gère automatiquement
        print(f"{model_name} téléchargé avec succès!")
        
        # Vérifier le chemin du modèle
        if hasattr(model, 'ckpt_path'):
            print(f"Modèle sauvegardé dans: {model.ckpt_path}")
        
        # Afficher les informations
        print(f"\nInformations sur le modèle:")
        print(f"  - Nombre de classes: {len(model.names)}")
        print(f"  - Classes détectables: {list(model.names.values())[:10]}... (et {len(model.names)-10} autres)")
        
        # Test rapide
        print(f"\nTest rapide du modèle...")
        results = model.predict('https://ultralytics.com/images/bus.jpg', verbose=False)
        print(f"Test réussi - {len(results[0].boxes)} objets détectés")
        
        print(f"\n{'='*50}")
        print(f"Modèle prêt à l'emploi!")
        print(f"Vous pouvez maintenant exécuter: save_model.py")
        print(f"{'='*50}")
        
        return model
        
    except Exception as e:
        print(f"Erreur lors du téléchargement: {e}")
        print("\nSi YOLO11 ne fonctionne pas, essayez YOLOv8:")
        print("  - Changez MODEL_NAME en 'yolov8n.pt'")
        print("\nVérifiez aussi:")
        print("  - Votre connexion internet")
        print("  - Que vous avez installé ultralytics: pip install ultralytics")
        print("  - Votre version d'ultralytics: pip install --upgrade ultralytics")
        return None


def download_all_models():
    """Télécharge tous les modèles YOLO11"""
    models = ['yolo11n.pt', 'yolo11s.pt', 'yolo11m.pt', 'yolo11l.pt', 'yolo11x.pt']
    
    print("=== Téléchargement de TOUS les modèles YOLO11 ===")
    print("Attention: Cela va télécharger ~300MB de données!\n")
    
    response = input("Voulez-vous continuer? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("Annulé.")
        return
    
    for model_name in models:
        print(f"\n--- {model_name} ---")
        download_yolo_model(model_name)
    
    print("\nTous les modèles ont été téléchargés!")


if __name__ == "__main__":
    # Configuration
    MODEL_NAME = 'yolov8n.pt'  # Utilisez YOLOv8 si YOLO11 ne fonctionne pas
    
    print("Note: Si YOLO11 ne fonctionne pas, le script essaiera YOLOv8\n")
    
    # Option 1: Télécharger un seul modèle (recommandé pour commencer)
    model = download_yolo_model(MODEL_NAME)
    
    # Si échec avec YOLO11, essayer YOLOv8
    if model is None and 'yolo11' in MODEL_NAME:
        print("\n" + "="*50)
        print("Tentative avec YOLOv8 à la place...")
        print("="*50 + "\n")
        MODEL_NAME = MODEL_NAME.replace('yolo11', 'yolov8')
        download_yolo_model(MODEL_NAME)
    
    # Option 2: Télécharger tous les modèles (décommenter si besoin)
    # download_all_models()