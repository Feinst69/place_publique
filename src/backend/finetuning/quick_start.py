"""
Script de démarrage rapide pour le fine-tuning YOLO
Usage: python quick_start.py
"""
import sys
from pathlib import Path

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées"""
    print("Vérification des dépendances...")
    
    missing = []
    dependencies = {
        'ultralytics': 'ultralytics',
        'pandas': 'pandas',
        'yaml': 'pyyaml',
        'tqdm': 'tqdm',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
    }
    
    for module, package in dependencies.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (manquant)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Dépendances manquantes: {', '.join(missing)}")
        print(f"Installez-les avec: pip install {' '.join(missing)}")
        return False
    
    print("✓ Toutes les dépendances sont installées!\n")
    return True


def check_dataset_structure(data_yaml_path):
    """Vérifie la structure du dataset"""
    print(f"Vérification du dataset: {data_yaml_path}")
    
    if not Path(data_yaml_path).exists():
        print(f"  ✗ Fichier data.yaml non trouvé: {data_yaml_path}")
        return False
    
    print(f"  ✓ Fichier data.yaml trouvé")
    
    # Charger le fichier YAML
    import yaml
    with open(data_yaml_path, 'r') as f:
        data_config = yaml.safe_load(f)
    
    # Vérifier les champs requis
    required_fields = ['path', 'train', 'val', 'nc', 'names']
    for field in required_fields:
        if field in data_config:
            print(f"  ✓ {field}: {data_config[field]}")
        else:
            print(f"  ✗ Champ manquant: {field}")
            return False
    
    # Vérifier que les dossiers existent
    dataset_path = Path(data_config['path'])
    train_path = dataset_path / data_config['train']
    val_path = dataset_path / data_config['val']
    
    if not train_path.exists():
        print(f"  ✗ Dossier train non trouvé: {train_path}")
        return False
    print(f"  ✓ Dossier train: {train_path}")
    
    if not val_path.exists():
        print(f"  ✗ Dossier val non trouvé: {val_path}")
        return False
    print(f"  ✓ Dossier val: {val_path}")
    
    print("✓ Structure du dataset valide!\n")
    return True


def quick_test():
    """Lance un test rapide pour vérifier que tout fonctionne"""
    print("="*60)
    print("TEST RAPIDE - Vérification de l'installation")
    print("="*60)
    print()
    
    # Vérifier les dépendances
    if not check_dependencies():
        return False
    
    # Demander le chemin du dataset
    print("Veuillez fournir le chemin vers votre fichier data.yaml")
    print("Exemple: data/dataset/data.yaml")
    data_yaml = input("\nChemin data.yaml: ").strip()
    
    if not data_yaml:
        print("⚠️  Aucun chemin fourni. Test annulé.")
        return False
    
    print()
    
    # Vérifier le dataset
    if not check_dataset_structure(data_yaml):
        print("\n⚠️  Problème avec la structure du dataset.")
        print("Consultez le fichier data.yaml.example pour un exemple.")
        return False
    
    # Lancer un entraînement de test (5 epochs)
    print("="*60)
    print("Lancement d'un entraînement de test (5 epochs)")
    print("="*60)
    print()
    
    from yolo_model import YOLOFineTuner
    
    trainer = YOLOFineTuner(
        model_name="yolo11n.pt",
        epochs=5,
        batch_size=16,
        imgsz=640,
        verbose=True
    )
    
    print("Entraînement en cours...")
    results = trainer.train(
        data_yaml=data_yaml,
        project="runs/quick_test",
        name="test_run"
    )
    
    print()
    print("="*60)
    if results["success"]:
        print("✓ TEST RÉUSSI!")
        print("="*60)
        print("\nVotre environnement est correctement configuré.")
        print("Vous pouvez maintenant utiliser:")
        print("  - example_usage.py pour des exemples détaillés")
        print("  - grid_search_training.py pour le grid search")
        print()
        print(f"Métriques: {results['metrics']}")
        return True
    else:
        print("✗ TEST ÉCHOUÉ")
        print("="*60)
        print(f"\nErreur: {results.get('error', 'Inconnue')}")
        return False


def interactive_menu():
    """Menu interactif pour choisir une action"""
    print("\n" + "="*60)
    print("YOLO FINE-TUNING - Menu Principal")
    print("="*60)
    print("\n1. Test rapide (5 epochs)")
    print("2. Entraînement simple")
    print("3. Grid search minimal")
    print("4. Grid search personnalisé")
    print("5. Voir les exemples")
    print("6. Créer un template de dataset")
    print("0. Quitter")
    
    choice = input("\nVotre choix (0-6): ").strip()
    
    if choice == "1":
        quick_test()
    
    elif choice == "2":
        print("\n" + "="*60)
        print("ENTRAÎNEMENT SIMPLE")
        print("="*60)
        
        data_yaml = input("\nChemin data.yaml: ").strip()
        if not data_yaml or not Path(data_yaml).exists():
            print("⚠️  Fichier data.yaml non trouvé")
            return
        
        epochs = int(input("Nombre d'epochs (ex: 100): ").strip() or "100")
        batch_size = int(input("Batch size (ex: 16): ").strip() or "16")
        
        from yolo_model import YOLOFineTuner
        
        trainer = YOLOFineTuner(
            model_name="yolo11n.pt",
            epochs=epochs,
            batch_size=batch_size
        )
        
        results = trainer.train(
            data_yaml=data_yaml,
            project="runs/train",
            name=f"training_e{epochs}_b{batch_size}"
        )
        
        if results["success"]:
            print(f"\n✓ Entraînement réussi! Métriques: {results['metrics']}")
        else:
            print(f"\n✗ Erreur: {results['error']}")
    
    elif choice == "3":
        print("\n" + "="*60)
        print("GRID SEARCH MINIMAL")
        print("="*60)
        
        data_yaml = input("\nChemin data.yaml: ").strip()
        if not data_yaml or not Path(data_yaml).exists():
            print("⚠️  Fichier data.yaml non trouvé")
            return
        
        from grid_search_training import GridSearchTrainer, get_minimal_grid
        
        trainer = GridSearchTrainer(
            data_yaml=data_yaml,
            param_grid=get_minimal_grid(),
            output_dir="runs/grid_search"
        )
        
        results = trainer.run()
        trainer.analyze_results()
        
        print(f"\n✓ Grid search terminé! Meilleur score: {trainer.best_score:.4f}")
    
    elif choice == "4":
        print("\n" + "="*60)
        print("GRID SEARCH PERSONNALISÉ")
        print("="*60)
        print("\nCréez votre propre grille de recherche dans le code")
        print("Consultez example_usage.py pour des exemples")
    
    elif choice == "5":
        print("\n" + "="*60)
        print("EXEMPLES D'UTILISATION")
        print("="*60)
        print("\nConsultez les fichiers suivants:")
        print("  - example_usage.py : Exemples détaillés")
        print("  - README.md : Documentation complète")
        print("\nExécutez: python example_usage.py")
    
    elif choice == "6":
        print("\n" + "="*60)
        print("CRÉER UN TEMPLATE DE DATASET")
        print("="*60)
        
        output_path = input("\nChemin de sortie (ex: data/my_dataset/data.yaml): ").strip()
        if not output_path:
            print("⚠️  Aucun chemin fourni")
            return
        
        # Créer le dossier parent
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Copier le template
        import shutil
        shutil.copy("data.yaml.example", output_path)
        
        print(f"✓ Template créé: {output_path}")
        print("  Éditez ce fichier pour configurer votre dataset")
    
    elif choice == "0":
        print("\nAu revoir!")
        return
    
    else:
        print("\n⚠️  Choix invalide")


def main():
    """Point d'entrée principal"""
    print("\n" + "="*60)
    print("🚀 YOLO FINE-TUNING - DÉMARRAGE RAPIDE")
    print("="*60)
    
    # Vérifier les dépendances
    if not check_dependencies():
        sys.exit(1)
    
    # Menu interactif
    while True:
        try:
            interactive_menu()
            
            again = input("\n\nAutre action? (o/n): ").strip().lower()
            if again != 'o':
                break
        except KeyboardInterrupt:
            print("\n\nInterrompu par l'utilisateur.")
            break
        except Exception as e:
            print(f"\n✗ Erreur: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n👋 Merci d'avoir utilisé YOLO Fine-Tuning!")


if __name__ == "__main__":
    main()
