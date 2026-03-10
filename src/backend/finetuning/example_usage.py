"""
Exemples d'utilisation du système de fine-tuning YOLO
"""
from yolo_model import YOLOFineTuner, get_minimal_grid, get_default_params, get_aggressive_augmentation_grid
from grid_search_training import GridSearchTrainer


# =============================================================================
# EXEMPLE 1: Entraînement simple avec paramètres par défaut
# =============================================================================
def example_simple_training():
    """Entraînement basique d'un modèle YOLO"""
    print("\n" + "="*60)
    print("EXEMPLE 1: Entraînement Simple")
    print("="*60)
    
    # Créer le fine-tuner
    trainer = YOLOFineTuner(
        model_name="yolo11n.pt",
        epochs=50,
        batch_size=16,
        imgsz=640
    )
    
    # Lancer l'entraînement
    results = trainer.train(
        data_yaml="data/dataset/data.yaml",
        project="runs/train",
        name="my_first_model"
    )
    
    # Afficher les résultats
    if results["success"]:
        print("\n✓ Entraînement réussi!")
        print(f"Métriques: {results['metrics']}")
    else:
        print(f"\n✗ Erreur: {results['error']}")


# =============================================================================
# EXEMPLE 2: Entraînement avec paramètres personnalisés
# =============================================================================
def example_custom_training():
    """Entraînement avec configuration personnalisée"""
    print("\n" + "="*60)
    print("EXEMPLE 2: Entraînement Personnalisé")
    print("="*60)
    
    # Configuration personnalisée
    trainer = YOLOFineTuner(
        model_name="yolo11s.pt",  # Modèle plus gros
        
        # Training
        epochs=100,
        batch_size=32,
        imgsz=1280,  # Images plus grandes
        
        # Optimizer
        optimizer="AdamW",
        lr0=0.001,  # Learning rate plus faible
        weight_decay=0.001,
        
        # Data augmentation forte
        hsv_h=0.05,
        hsv_s=0.9,
        hsv_v=0.6,
        degrees=15.0,
        mosaic=1.0,
        mixup=0.15,
        
        # Regularization
        dropout=0.1,
        
        # Performance
        patience=50,
        amp=True,
    )
    
    # Sauvegarder la configuration
    trainer.save_config("configs/my_custom_config.yaml")
    
    # Entraîner
    results = trainer.train(
        data_yaml="data/dataset/data.yaml",
        project="runs/train",
        name="custom_model_v1"
    )
    
    print(f"\n✓ Résultats: {results['metrics']}")


# =============================================================================
# EXEMPLE 3: Grid search minimal (test rapide)
# =============================================================================
def example_minimal_grid_search():
    """Grid search rapide pour tester le système"""
    print("\n" + "="*60)
    print("EXEMPLE 3: Grid Search Minimal (Rapide)")
    print("="*60)
    
    # Utiliser le grid minimal prédéfini
    param_grid = get_minimal_grid()
    
    print(f"Paramètres à tester: {param_grid}")
    
    # Créer le trainer
    trainer = GridSearchTrainer(
        data_yaml="data/dataset/data.yaml",
        param_grid=param_grid,
        output_dir="runs/grid_search",
        metric_to_optimize="mAP50-95"
    )
    
    # Lancer
    results = trainer.run()
    
    # Analyser
    trainer.analyze_results()
    
    print(f"\n✓ Meilleur score: {trainer.best_score:.4f}")
    print(f"✓ Meilleure config: {trainer.best_config['experiment_name']}")


# =============================================================================
# EXEMPLE 4: Grid search personnalisé
# =============================================================================
def example_custom_grid_search():
    """Grid search avec paramètres personnalisés"""
    print("\n" + "="*60)
    print("EXEMPLE 4: Grid Search Personnalisé")
    print("="*60)
    
    # Définir votre propre grid
    my_grid = {
        # Tester différents modèles
        "model_name": ["yolo11n.pt", "yolo11s.pt"],
        
        # Tester différentes durées d'entraînement
        "epochs": [50, 100, 150],
        
        # Tester différentes tailles de batch
        "batch_size": [16, 32],
        
        # Tester différents learning rates
        "lr0": [0.0001, 0.001, 0.01],
        
        # Tester différents optimiseurs
        "optimizer": ["Adam", "AdamW", "SGD"],
        
        # Tester avec/sans dropout
        "dropout": [0.0, 0.1],
        
        # Tester différents niveaux d'augmentation
        "mosaic": [0.0, 1.0],
        "mixup": [0.0, 0.15],
    }
    
    # Calculer le nombre de combinaisons
    import itertools
    total_combinations = 1
    for values in my_grid.values():
        total_combinations *= len(values)
    
    print(f"Nombre total de combinaisons: {total_combinations}")
    
    # Créer le trainer avec limitation
    trainer = GridSearchTrainer(
        data_yaml="data/dataset/data.yaml",
        param_grid=my_grid,
        output_dir="runs/grid_search",
        metric_to_optimize="mAP50-95",
        max_combinations=20,  # Limiter à 20 combinaisons aléatoires
        save_all_models=False
    )
    
    # Lancer
    results = trainer.run()
    
    # Analyser
    trainer.analyze_results()


# =============================================================================
# EXEMPLE 5: Focus sur l'augmentation de données
# =============================================================================
def example_augmentation_focus():
    """Grid search focalisé sur la data augmentation"""
    print("\n" + "="*60)
    print("EXEMPLE 5: Focus Augmentation de Données")
    print("="*60)
    
    # Utiliser le grid d'augmentation agressive
    param_grid = get_aggressive_augmentation_grid()
    
    trainer = GridSearchTrainer(
        data_yaml="data/dataset/data.yaml",
        param_grid=param_grid,
        output_dir="runs/grid_search_augmentation",
        metric_to_optimize="mAP50-95"
    )
    
    results = trainer.run()
    trainer.analyze_results()


# =============================================================================
# EXEMPLE 6: Charger et réutiliser une configuration
# =============================================================================
def example_load_and_reuse_config():
    """Charger une config sauvegardée et l'utiliser"""
    print("\n" + "="*60)
    print("EXEMPLE 6: Réutiliser une Configuration")
    print("="*60)
    
    # Supposons que vous avez trouvé la meilleure config avec grid search
    # Elle est sauvegardée dans best_params.yaml
    
    # Charger la configuration
    best_config_path = "runs/grid_search/session_XXX/best_params.yaml"
    
    # Option 1: Charger depuis YAML
    import yaml
    with open("configs/best_config.yaml", 'r') as f:
        best_params = yaml.safe_load(f)
    
    # Créer le trainer avec ces paramètres
    trainer = YOLOFineTuner(**best_params)
    
    # Entraîner avec la meilleure config
    results = trainer.train(
        data_yaml="data/dataset/data.yaml",
        project="runs/train",
        name="production_model_v1"
    )
    
    print(f"✓ Modèle final entraîné: {results['metrics']}")


# =============================================================================
# EXEMPLE 7: Optimiser pour différentes métriques
# =============================================================================
def example_different_metrics():
    """Optimiser selon différentes métriques"""
    print("\n" + "="*60)
    print("EXEMPLE 7: Optimiser Différentes Métriques")
    print("="*60)
    
    param_grid = {
        "model_name": ["yolo11n.pt"],
        "epochs": [50],
        "lr0": [0.001, 0.01],
        "optimizer": ["Adam", "SGD"],
    }
    
    # Test 1: Optimiser pour mAP50-95
    print("\nTest 1: Optimiser mAP50-95")
    trainer1 = GridSearchTrainer(
        data_yaml="data/dataset/data.yaml",
        param_grid=param_grid,
        metric_to_optimize="mAP50-95",
        output_dir="runs/grid_search_map5095"
    )
    trainer1.run()
    
    # Test 2: Optimiser pour precision
    print("\nTest 2: Optimiser Precision")
    trainer2 = GridSearchTrainer(
        data_yaml="data/dataset/data.yaml",
        param_grid=param_grid,
        metric_to_optimize="precision",
        output_dir="runs/grid_search_precision"
    )
    trainer2.run()
    
    # Test 3: Optimiser pour recall
    print("\nTest 3: Optimiser Recall")
    trainer3 = GridSearchTrainer(
        data_yaml="data/dataset/data.yaml",
        param_grid=param_grid,
        metric_to_optimize="recall",
        output_dir="runs/grid_search_recall"
    )
    trainer3.run()


# =============================================================================
# EXEMPLE 8: Pipeline complet de recherche de paramètres
# =============================================================================
def example_complete_pipeline():
    """Pipeline complet: test rapide -> grid search -> modèle final"""
    print("\n" + "="*60)
    print("EXEMPLE 8: Pipeline Complet")
    print("="*60)
    
    DATA_YAML = "data/dataset/data.yaml"
    
    # ÉTAPE 1: Test rapide pour vérifier que tout fonctionne
    print("\n[1/3] Test rapide...")
    quick_grid = {
        "model_name": ["yolo11n.pt"],
        "epochs": [5],
        "batch_size": [16],
    }
    
    quick_trainer = GridSearchTrainer(
        data_yaml=DATA_YAML,
        param_grid=quick_grid,
        output_dir="runs/pipeline/01_quick_test"
    )
    quick_trainer.run()
    
    if not quick_trainer.best_config:
        print("✗ Problème détecté lors du test rapide. Vérifiez votre dataset.")
        return
    
    print("✓ Test rapide réussi!")
    
    # ÉTAPE 2: Grid search principal
    print("\n[2/3] Grid search principal...")
    main_grid = {
        "model_name": ["yolo11n.pt", "yolo11s.pt"],
        "epochs": [50, 100],
        "batch_size": [16, 32],
        "lr0": [0.001, 0.01],
        "optimizer": ["Adam", "AdamW"],
        "dropout": [0.0, 0.1],
    }
    
    main_trainer = GridSearchTrainer(
        data_yaml=DATA_YAML,
        param_grid=main_grid,
        output_dir="runs/pipeline/02_main_search",
        max_combinations=20
    )
    main_trainer.run()
    main_trainer.analyze_results()
    
    print(f"✓ Meilleur modèle: {main_trainer.best_config['experiment_name']}")
    print(f"✓ Score: {main_trainer.best_score:.4f}")
    
    # ÉTAPE 3: Entraîner le modèle final avec les meilleurs paramètres
    print("\n[3/3] Entraînement du modèle final...")
    best_params = main_trainer.best_config["params"]
    
    final_trainer = YOLOFineTuner(**best_params)
    final_trainer.params["epochs"] = 200  # Plus d'époques pour le modèle final
    
    final_results = final_trainer.train(
        data_yaml=DATA_YAML,
        project="runs/pipeline/03_final_model",
        name="production_model"
    )
    
    print("\n" + "="*60)
    print("PIPELINE TERMINÉ")
    print("="*60)
    print(f"✓ Modèle de production prêt!")
    print(f"✓ Métriques finales: {final_results['metrics']}")
    print(f"✓ Modèle sauvegardé dans: runs/pipeline/03_final_model/production_model")
    print("="*60)


# =============================================================================
# MAIN - Choisir l'exemple à exécuter
# =============================================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("EXEMPLES D'UTILISATION - YOLO FINE-TUNING")
    print("="*60)
    
    print("\nChoisissez un exemple à exécuter:")
    print("1. Entraînement simple")
    print("2. Entraînement personnalisé")
    print("3. Grid search minimal (rapide)")
    print("4. Grid search personnalisé")
    print("5. Focus augmentation de données")
    print("6. Réutiliser une configuration")
    print("7. Optimiser différentes métriques")
    print("8. Pipeline complet")
    print("0. Quitter")
    
    choice = input("\nVotre choix (0-8): ").strip()
    
    examples = {
        "1": example_simple_training,
        "2": example_custom_training,
        "3": example_minimal_grid_search,
        "4": example_custom_grid_search,
        "5": example_augmentation_focus,
        "6": example_load_and_reuse_config,
        "7": example_different_metrics,
        "8": example_complete_pipeline,
    }
    
    if choice in examples:
        print("\n" + "="*60)
        print(f"Exécution de l'exemple {choice}...")
        print("="*60)
        
        # IMPORTANT: Avant d'exécuter, vérifiez que le chemin DATA_YAML est correct!
        print("\nATTENTION: Assurez-vous que le chemin vers data.yaml est correct!")
        print("Modifiez la variable DATA_YAML dans le code si nécessaire.")
        
        confirm = input("\nContinuer? (o/n): ").strip().lower()
        if confirm == 'o':
            examples[choice]()
        else:
            print("Annulé.")
    elif choice == "0":
        print("Au revoir!")
    else:
        print("Choix invalide.")
