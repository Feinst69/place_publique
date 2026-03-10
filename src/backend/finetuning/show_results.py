"""
Script pour afficher les résultats du fine-tuning
"""
import pandas as pd
from pathlib import Path

results_path = Path("runs/detect/runs/roboflow_train/test_yolov8n/results.csv")

if results_path.exists():
    df = pd.read_csv(results_path)
    df.columns = df.columns.str.strip()
    
    print("="*80)
    print("RÉSULTATS DU FINE-TUNING")
    print("="*80)
    print(f"\nNombre d'époques entraînées: {len(df)}")
    
    # Dernière époque
    last_epoch = df.iloc[-1]
    
    print(f"\nMÉTRIQUES FINALES (Époque {int(last_epoch['epoch'])}):")
    print("-" * 80)
    
    metrics = {
        'Box Loss (train)': last_epoch.get('train/box_loss', 'N/A'),
        'Class Loss (train)': last_epoch.get('train/cls_loss', 'N/A'),
        'DFL Loss (train)': last_epoch.get('train/dfl_loss', 'N/A'),
        'Precision': last_epoch.get('metrics/precision(B)', 'N/A'),
        'Recall': last_epoch.get('metrics/recall(B)', 'N/A'),
        'mAP50': last_epoch.get('metrics/mAP50(B)', 'N/A'),
        'mAP50-95': last_epoch.get('metrics/mAP50-95(B)', 'N/A'),
    }
    
    for name, value in metrics.items():
        if value != 'N/A':
            print(f"  {name:25s}: {value:.4f}")
        else:
            print(f"  {name:25s}: {value}")
    
    # Meilleure époque pour mAP50
    if 'metrics/mAP50(B)' in df.columns:
        best_idx = df['metrics/mAP50(B)'].idxmax()
        best_epoch = df.iloc[best_idx]
        
        print(f"\nMEILLEURE ÉPOQUE (Époque {int(best_epoch['epoch'])}):")
        print("-" * 80)
        print(f"  mAP50                     : {best_epoch['metrics/mAP50(B)']:.4f}")
        print(f"  mAP50-95                  : {best_epoch['metrics/mAP50-95(B)']:.4f}")
        print(f"  Precision                 : {best_epoch['metrics/precision(B)']:.4f}")
        print(f"  Recall                    : {best_epoch['metrics/recall(B)']:.4f}")
    
    print("\n" + "="*80)
    print("FICHIERS GÉNÉRÉS:")
    print("="*80)
    
    results_dir = results_path.parent
    print(f"\nModèle entraîné:")
    print(f"   {results_dir / 'weights' / 'best.pt'}")
    print(f"\nCourbes et graphiques:")
    for img in results_dir.glob("*.png"):
        print(f"   {img.name}")
    print(f"\nRésultats complets:")
    print(f"   {results_path}")
    
else:
    print("Fichier results.csv non trouvé")
