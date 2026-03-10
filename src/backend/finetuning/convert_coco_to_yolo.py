"""
Script de conversion annotations COCO vers format YOLO
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple


def convert_bbox_coco_to_yolo(bbox: List[float], img_width: int, img_height: int) -> Tuple[float, float, float, float]:
    """
    Convertit une bbox du format COCO [x_min, y_min, width, height] 
    vers le format YOLO [x_center, y_center, width, height] (normalisé)
    
    Args:
        bbox: [x_min, y_min, width, height] en pixels
        img_width: Largeur de l'image
        img_height: Hauteur de l'image
        
    Returns:
        (x_center, y_center, width, height) normalisés entre 0 et 1
    """
    x_min, y_min, width, height = bbox
    
    # Calculer le centre
    x_center = x_min + width / 2
    y_center = y_min + height / 2
    
    # Normaliser par rapport aux dimensions de l'image
    x_center_norm = x_center / img_width
    y_center_norm = y_center / img_height
    width_norm = width / img_width
    height_norm = height / img_height
    
    # S'assurer que les valeurs sont dans [0, 1]
    x_center_norm = max(0, min(1, x_center_norm))
    y_center_norm = max(0, min(1, y_center_norm))
    width_norm = max(0, min(1, width_norm))
    height_norm = max(0, min(1, height_norm))
    
    return x_center_norm, y_center_norm, width_norm, height_norm


def convert_coco_to_yolo(
    coco_json_path: str,
    output_dir: str,
    images_dir: str = None
) -> Dict[str, any]:
    """
    Convertit un fichier d'annotations COCO en format YOLO
    
    Args:
        coco_json_path: Chemin vers le fichier _annotations.coco.json
        output_dir: Répertoire de sortie pour les labels YOLO
        images_dir: Répertoire contenant les images (même dossier si None)
        
    Returns:
        Dictionnaire avec les statistiques de conversion
    """
    # Charger les annotations COCO
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)
    
    # Créer le répertoire de sortie
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Créer un mapping image_id -> image_info
    images_map = {img['id']: img for img in coco_data['images']}
    
    # Créer un mapping category_id -> index YOLO (0-indexed)
    unique_categories = sorted(set(cat['id'] for cat in coco_data['categories']))
    category_map = {cat_id: idx for idx, cat_id in enumerate(unique_categories)}
    
    # Créer un mapping category_id -> name
    category_names = {cat['id']: cat['name'] for cat in coco_data['categories']}
    
    # Grouper les annotations par image
    annotations_by_image = {}
    for ann in coco_data['annotations']:
        image_id = ann['image_id']
        if image_id not in annotations_by_image:
            annotations_by_image[image_id] = []
        annotations_by_image[image_id].append(ann)
    
    # Statistiques
    stats = {
        'images_processed': 0,
        'annotations_converted': 0,
        'categories': len(unique_categories),
        'category_names': [category_names[cat_id] for cat_id in unique_categories],
        'category_map': category_map
    }
    
    # Convertir chaque image
    for image_id, image_info in images_map.items():
        file_name = image_info['file_name']
        img_width = image_info['width']
        img_height = image_info['height']
        
        # Nom du fichier de sortie (même nom que l'image mais avec .txt)
        label_file = file_name.replace('.jpg', '.txt').replace('.png', '.txt').replace('.jpeg', '.txt')
        label_path = output_path / label_file
        
        # Récupérer les annotations pour cette image
        annotations = annotations_by_image.get(image_id, [])
        
        # Écrire les annotations en format YOLO
        with open(label_path, 'w') as f:
            for ann in annotations:
                # Ignorer les annotations sans bbox
                if 'bbox' not in ann:
                    continue
                
                # Convertir la catégorie
                category_id = ann['category_id']
                yolo_class = category_map[category_id]
                
                # Convertir la bbox
                bbox = ann['bbox']
                x_center, y_center, width, height = convert_bbox_coco_to_yolo(
                    bbox, img_width, img_height
                )
                
                # Écrire la ligne au format YOLO: class x_center y_center width height
                f.write(f"{yolo_class} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                stats['annotations_converted'] += 1
        
        stats['images_processed'] += 1
    
    print(f"\n[OK] Conversion terminée:")
    print(f"  - Images traitées: {stats['images_processed']}")
    print(f"  - Annotations converties: {stats['annotations_converted']}")
    print(f"  - Catégories: {stats['categories']}")
    print(f"  - Noms des catégories: {stats['category_names']}")
    print(f"  - Labels YOLO sauvegardés dans: {output_dir}")
    
    return stats


def prepare_dataset_for_yolo(
    train_dir: str,
    output_base_dir: str = None
) -> Dict[str, str]:
    """
    Prépare le dataset complet pour YOLO (train/val/test)
    
    Args:
        train_dir: Répertoire contenant les images et _annotations.coco.json
        output_base_dir: Répertoire de base pour la sortie
        
    Returns:
        Dictionnaire avec les chemins créés
    """
    train_path = Path(train_dir)
    
    if output_base_dir is None:
        output_base_dir = train_path.parent / "yolo_format"
    else:
        output_base_dir = Path(output_base_dir)
    
    # Créer la structure de répertoires YOLO
    images_train_dir = output_base_dir / "images" / "train"
    labels_train_dir = output_base_dir / "labels" / "train"
    
    images_train_dir.mkdir(parents=True, exist_ok=True)
    labels_train_dir.mkdir(parents=True, exist_ok=True)
    
    # Copier les images
    print(f"\n[INFO] Copie des images...")
    import shutil
    for img_file in train_path.glob("*.png"):
        shutil.copy(img_file, images_train_dir / img_file.name)
    for img_file in train_path.glob("*.jpg"):
        shutil.copy(img_file, images_train_dir / img_file.name)
    
    # Convertir les annotations
    print(f"\n[INFO] Conversion des annotations...")
    coco_json = train_path / "_annotations.coco.json"
    if coco_json.exists():
        stats = convert_coco_to_yolo(
            str(coco_json),
            str(labels_train_dir),
            str(images_train_dir)
        )
    else:
        raise FileNotFoundError(f"Fichier d'annotations non trouvé: {coco_json}")
    
    paths = {
        'base_dir': str(output_base_dir),
        'images_train': str(images_train_dir),
        'labels_train': str(labels_train_dir),
        'stats': stats
    }
    
    return paths


if __name__ == "__main__":
    # Configuration
    TRAIN_DIR = "data/final/train"
    OUTPUT_DIR = "data/final/yolo_format"
    
    # Préparer le dataset
    print("[INFO] Préparation du dataset pour YOLO...")
    paths = prepare_dataset_for_yolo(TRAIN_DIR, OUTPUT_DIR)
    
    print(f"\n[OK] Dataset YOLO prêt!")
    print(f"[INFO] Répertoire de base: {paths['base_dir']}")
    print(f"[INFO] Images d'entraînement: {paths['images_train']}")
    print(f"[INFO] Labels d'entraînement: {paths['labels_train']}")
