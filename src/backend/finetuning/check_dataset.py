"""
Script pour vérifier le contenu du dataset Roboflow
"""
from pathlib import Path
import yaml

def check_dataset(dataset_path: str = "Place_publique-4"):
    """Affiche les informations sur le dataset"""
    
    print("="*80)
    print("VÉRIFICATION DU DATASET")
    print("="*80)
    
    dataset_path = Path(dataset_path)
    
    if not dataset_path.exists():
        print(f"Dataset non trouvé: {dataset_path}")
        return
    
    print(f"\nDataset trouvé: {dataset_path}")
    
    # Lire le data.yaml
    data_yaml = dataset_path / "data.yaml"
    if data_yaml.exists():
        with open(data_yaml, 'r') as f:
            config = yaml.safe_load(f)
        print(f"\nConfiguration (data.yaml):")
        print(f"   - Nombre de classes: {config.get('nc', '?')}")
        print(f"   - Classes: {config.get('names', '?')}")
    
    # Compter les images par split
    splits = ['train', 'valid', 'test']
    total_images = 0
    
    print(f"\nImages par split:")
    for split in splits:
        images_dir = dataset_path / split / 'images'
        if not images_dir.exists():
            images_dir = dataset_path / split
        
        if images_dir.exists():
            images = list(images_dir.glob('*.jpg')) + list(images_dir.glob('*.png'))
            labels_dir = dataset_path / split / 'labels'
            if labels_dir.exists():
                labels = list(labels_dir.glob('*.txt'))
            else:
                labels = []
            
            print(f"   - {split:6s}: {len(images):3d} images, {len(labels):3d} labels")
            total_images += len(images)
        else:
            print(f"   - {split:6s}: Non trouvé")
    
    print(f"\nTOTAL: {total_images} images")
    
    # Lire le README si disponible
    readme = dataset_path / "README.roboflow.txt"
    if readme.exists():
        print(f"\nInformation du README:")
        with open(readme, 'r') as f:
            for line in f:
                if "dataset includes" in line.lower() or "images" in line.lower():
                    print(f"   {line.strip()}")
                    break

if __name__ == "__main__":
    check_dataset()
