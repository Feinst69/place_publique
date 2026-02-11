"""
Script de Grid Search pour le fine-tuning de modèles YOLO
Teste différentes combinaisons de paramètres et sauvegarde les résultats
"""
import itertools
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
from tqdm import tqdm
import yaml

from yolo_model import YOLOFineTuner, get_default_params, get_minimal_grid, get_aggressive_augmentation_grid


class GridSearchTrainer:
    """
    Classe pour effectuer un grid search sur les paramètres de fine-tuning YOLO
    """
    
    def __init__(
        self,
        data_yaml: str,
        param_grid: Optional[Dict[str, List[Any]]] = None,
        output_dir: str = "runs/grid_search",
        metric_to_optimize: str = "mAP50-95",
        max_combinations: Optional[int] = None,
        save_all_models: bool = False
    ):
        """
        Initialise le grid search
        
        Args:
            data_yaml: Chemin vers le fichier data.yaml du dataset
            param_grid: Dictionnaire de paramètres à tester (None = utilise get_default_params())
            output_dir: Dossier de sortie pour les résultats
            metric_to_optimize: Métrique à optimiser ('mAP50-95', 'mAP50', 'precision', 'recall')
            max_combinations: Nombre maximum de combinaisons à tester (None = toutes)
            save_all_models: Si True, garde tous les modèles entraînés
        """
        self.data_yaml = data_yaml
        self.param_grid = param_grid or get_minimal_grid()
        self.output_dir = Path(output_dir)
        self.metric_to_optimize = metric_to_optimize
        self.max_combinations = max_combinations
        self.save_all_models = save_all_models
        
        # Créer le dossier de sortie
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Timestamp pour cette session
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"session_{self.timestamp}"
        self.session_dir.mkdir(exist_ok=True)
        
        # Stockage des résultats
        self.results = []
        self.best_config = None
        self.best_score = float('-inf')
        
    def generate_combinations(self) -> List[Dict[str, Any]]:
        """
        Génère toutes les combinaisons de paramètres possibles
        
        Returns:
            Liste de dictionnaires de paramètres
        """
        # Extraire les clés et valeurs
        keys = list(self.param_grid.keys())
        values = [self.param_grid[k] if isinstance(self.param_grid[k], list) else [self.param_grid[k]] 
                  for k in keys]
        
        # Générer toutes les combinaisons
        combinations = []
        for combo in itertools.product(*values):
            param_dict = dict(zip(keys, combo))
            combinations.append(param_dict)
        
        print(f"\n{'='*60}")
        print(f"Grid Search Configuration")
        print(f"{'='*60}")
        print(f"Nombre total de combinaisons: {len(combinations)}")
        
        if self.max_combinations and len(combinations) > self.max_combinations:
            print(f"Limitation à {self.max_combinations} combinaisons (random sample)")
            import random
            random.seed(42)
            combinations = random.sample(combinations, self.max_combinations)
        
        print(f"Combinaisons à tester: {len(combinations)}")
        print(f"Dataset: {self.data_yaml}")
        print(f"Métrique optimisée: {self.metric_to_optimize}")
        print(f"Dossier de sortie: {self.session_dir}")
        print(f"{'='*60}\n")
        
        return combinations
    
    def run(self):
        """
        Exécute le grid search complet
        """
        # Générer les combinaisons
        combinations = self.generate_combinations()
        
        # Sauvegarder la configuration du grid search
        self._save_grid_config(combinations)
        
        # Boucle sur toutes les combinaisons
        print(f"Début du Grid Search - {len(combinations)} configurations à tester\n")
        
        for idx, params in enumerate(tqdm(combinations, desc="Grid Search Progress")):
            print(f"\n{'='*60}")
            print(f"Configuration {idx + 1}/{len(combinations)}")
            print(f"{'='*60}")
            
            # Créer le nom de l'expérience
            exp_name = self._create_experiment_name(idx, params)
            
            # Créer le fine-tuner avec ces paramètres
            trainer = YOLOFineTuner(**params)
            
            # Lancer l'entraînement
            result = trainer.train(
                data_yaml=self.data_yaml,
                project=str(self.session_dir / "experiments"),
                name=exp_name,
                exist_ok=True
            )
            
            # Stocker les résultats
            result_entry = {
                "experiment_id": idx,
                "experiment_name": exp_name,
                "params": params,
                "success": result["success"],
                "metrics": result.get("metrics", {}),
                "timestamp": datetime.now().isoformat()
            }
            
            if not result["success"]:
                result_entry["error"] = result.get("error", "Unknown error")
            
            self.results.append(result_entry)
            
            # Vérifier si c'est le meilleur modèle
            if result["success"]:
                score = result.get("metrics", {}).get(self.metric_to_optimize, 0)
                if score > self.best_score:
                    self.best_score = score
                    self.best_config = result_entry
                    print(f"\n🏆 Nouveau meilleur modèle! {self.metric_to_optimize}: {score:.4f}")
            
            # Sauvegarder les résultats intermédiaires
            self._save_results()
            
            print(f"Configuration {idx + 1} terminée\n")
        
        # Sauvegarder les résultats finaux
        self._save_final_results()
        
        # Afficher le résumé
        self._print_summary()
        
        return self.results
    
    def _create_experiment_name(self, idx: int, params: Dict[str, Any]) -> str:
        """
        Crée un nom descriptif pour l'expérience
        
        Args:
            idx: Index de l'expérience
            params: Paramètres de l'expérience
            
        Returns:
            Nom de l'expérience
        """
        model = params.get('model_name', 'yolo').split('.')[0]
        epochs = params.get('epochs', 0)
        batch = params.get('batch_size', 0)
        lr = params.get('lr0', 0)
        opt = params.get('optimizer', 'opt')
        
        name = f"exp_{idx:03d}_{model}_e{epochs}_b{batch}_lr{lr}_{opt}"
        return name
    
    def _save_grid_config(self, combinations: List[Dict[str, Any]]):
        """Sauvegarde la configuration du grid search"""
        config = {
            "timestamp": self.timestamp,
            "data_yaml": self.data_yaml,
            "param_grid": self.param_grid,
            "metric_to_optimize": self.metric_to_optimize,
            "total_combinations": len(combinations),
            "max_combinations": self.max_combinations,
            "save_all_models": self.save_all_models,
        }
        
        config_file = self.session_dir / "grid_search_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Configuration sauvegardée: {config_file}")
    
    def _save_results(self):
        """Sauvegarde les résultats intermédiaires"""
        # JSON complet
        results_file = self.session_dir / "results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # CSV pour analyse facile
        self._save_results_csv()
    
    def _save_results_csv(self):
        """Sauvegarde les résultats en format CSV"""
        if not self.results:
            return
        
        # Préparer les données pour le CSV
        csv_data = []
        for result in self.results:
            row = {
                "experiment_id": result["experiment_id"],
                "experiment_name": result["experiment_name"],
                "success": result["success"],
            }
            
            # Ajouter les paramètres
            for key, value in result["params"].items():
                row[f"param_{key}"] = value
            
            # Ajouter les métriques
            for key, value in result.get("metrics", {}).items():
                row[f"metric_{key}"] = value
            
            # Ajouter l'erreur si échec
            if not result["success"]:
                row["error"] = result.get("error", "")
            
            csv_data.append(row)
        
        # Créer le DataFrame et sauvegarder
        df = pd.DataFrame(csv_data)
        csv_file = self.session_dir / "results.csv"
        df.to_csv(csv_file, index=False)
    
    def _save_final_results(self):
        """Sauvegarde les résultats finaux avec analyse"""
        # Sauvegarder les résultats complets
        self._save_results()
        
        # Sauvegarder le meilleur modèle
        if self.best_config:
            best_file = self.session_dir / "best_config.json"
            with open(best_file, 'w') as f:
                json.dump(self.best_config, f, indent=2)
            
            # Créer un fichier YAML avec la meilleure config
            best_params_file = self.session_dir / "best_params.yaml"
            with open(best_params_file, 'w') as f:
                yaml.dump(self.best_config["params"], f, default_flow_style=False)
        
        # Créer un rapport de synthèse
        self._create_summary_report()
    
    def _create_summary_report(self):
        """Crée un rapport de synthèse du grid search"""
        report = []
        report.append("=" * 80)
        report.append("GRID SEARCH - RAPPORT FINAL")
        report.append("=" * 80)
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Session: {self.timestamp}")
        report.append(f"Dataset: {self.data_yaml}")
        report.append(f"Métrique optimisée: {self.metric_to_optimize}")
        report.append("")
        
        # Statistiques générales
        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total - successful
        
        report.append(f"Statistiques générales:")
        report.append(f"  - Total d'expériences: {total}")
        report.append(f"  - Réussites: {successful} ({successful/total*100:.1f}%)")
        report.append(f"  - Échecs: {failed} ({failed/total*100:.1f}%)")
        report.append("")
        
        # Meilleur modèle
        if self.best_config:
            report.append(f"Meilleur modèle:")
            report.append(f"  - Nom: {self.best_config['experiment_name']}")
            report.append(f"  - {self.metric_to_optimize}: {self.best_score:.4f}")
            report.append(f"  - Paramètres:")
            for key, value in self.best_config["params"].items():
                report.append(f"      {key}: {value}")
            report.append(f"  - Métriques:")
            for key, value in self.best_config.get("metrics", {}).items():
                report.append(f"      {key}: {value:.4f}")
        report.append("")
        
        # Top 5 modèles
        report.append("Top 5 modèles:")
        successful_results = [r for r in self.results if r["success"]]
        sorted_results = sorted(
            successful_results,
            key=lambda x: x.get("metrics", {}).get(self.metric_to_optimize, 0),
            reverse=True
        )[:5]
        
        for idx, result in enumerate(sorted_results, 1):
            score = result.get("metrics", {}).get(self.metric_to_optimize, 0)
            report.append(f"  {idx}. {result['experiment_name']} - {self.metric_to_optimize}: {score:.4f}")
        
        report.append("")
        report.append("=" * 80)
        
        # Sauvegarder le rapport
        report_text = "\n".join(report)
        report_file = self.session_dir / "summary_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print("\n" + report_text)
    
    def _print_summary(self):
        """Affiche un résumé dans la console"""
        print("\n" + "=" * 60)
        print("GRID SEARCH TERMINÉ")
        print("=" * 60)
        print(f"Résultats sauvegardés dans: {self.session_dir}")
        print(f"Nombre d'expériences: {len(self.results)}")
        
        if self.best_config:
            print(f"\nMeilleur modèle: {self.best_config['experiment_name']}")
            print(f"{self.metric_to_optimize}: {self.best_score:.4f}")
        
        print("=" * 60 + "\n")
    
    def analyze_results(self):
        """
        Analyse les résultats du grid search et génère des visualisations
        """
        if not self.results:
            print("Aucun résultat à analyser")
            return
        
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Préparer les données
            df = pd.read_csv(self.session_dir / "results.csv")
            df_success = df[df['success'] == True].copy()
            
            if len(df_success) == 0:
                print("Aucune expérience réussie à analyser")
                return
            
            # Configuration des graphiques
            sns.set_style("whitegrid")
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(f'Grid Search Analysis - {self.timestamp}', fontsize=16)
            
            # 1. Distribution de la métrique principale
            ax1 = axes[0, 0]
            metric_col = f"metric_{self.metric_to_optimize}"
            if metric_col in df_success.columns:
                df_success[metric_col].hist(bins=20, ax=ax1, edgecolor='black')
                ax1.set_xlabel(self.metric_to_optimize)
                ax1.set_ylabel('Fréquence')
                ax1.set_title(f'Distribution de {self.metric_to_optimize}')
                ax1.axvline(self.best_score, color='red', linestyle='--', label='Meilleur score')
                ax1.legend()
            
            # 2. Impact du learning rate
            ax2 = axes[0, 1]
            if 'param_lr0' in df_success.columns and metric_col in df_success.columns:
                lr_groups = df_success.groupby('param_lr0')[metric_col].mean().sort_index()
                lr_groups.plot(kind='bar', ax=ax2, color='skyblue', edgecolor='black')
                ax2.set_xlabel('Learning Rate')
                ax2.set_ylabel(f'Moyenne {self.metric_to_optimize}')
                ax2.set_title('Impact du Learning Rate')
                ax2.tick_params(axis='x', rotation=45)
            
            # 3. Impact de l'optimiseur
            ax3 = axes[1, 0]
            if 'param_optimizer' in df_success.columns and metric_col in df_success.columns:
                opt_groups = df_success.groupby('param_optimizer')[metric_col].mean()
                opt_groups.plot(kind='bar', ax=ax3, color='lightcoral', edgecolor='black')
                ax3.set_xlabel('Optimiseur')
                ax3.set_ylabel(f'Moyenne {self.metric_to_optimize}')
                ax3.set_title('Impact de l\'Optimiseur')
                ax3.tick_params(axis='x', rotation=45)
            
            # 4. Top 10 expériences
            ax4 = axes[1, 1]
            if metric_col in df_success.columns:
                top10 = df_success.nlargest(10, metric_col)
                y_pos = range(len(top10))
                ax4.barh(y_pos, top10[metric_col].values, color='lightgreen', edgecolor='black')
                ax4.set_yticks(y_pos)
                ax4.set_yticklabels([f"Exp {int(x)}" for x in top10['experiment_id'].values])
                ax4.set_xlabel(self.metric_to_optimize)
                ax4.set_title('Top 10 Expériences')
                ax4.invert_yaxis()
            
            plt.tight_layout()
            
            # Sauvegarder la figure
            plot_file = self.session_dir / "analysis_plots.png"
            plt.savefig(plot_file, dpi=150, bbox_inches='tight')
            print(f"Graphiques d'analyse sauvegardés: {plot_file}")
            
            plt.close()
            
            # Générer des statistiques supplémentaires
            self._generate_statistics(df_success)
            
        except ImportError:
            print("matplotlib et seaborn requis pour l'analyse. Installez-les avec:")
            print("  pip install matplotlib seaborn")
        except Exception as e:
            print(f"Erreur lors de l'analyse: {str(e)}")
    
    def _generate_statistics(self, df_success: pd.DataFrame):
        """Génère des statistiques détaillées"""
        stats_file = self.session_dir / "statistics.txt"
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write("STATISTIQUES DÉTAILLÉES\n")
            f.write("=" * 60 + "\n\n")
            
            # Statistiques sur la métrique principale
            metric_col = f"metric_{self.metric_to_optimize}"
            if metric_col in df_success.columns:
                f.write(f"Statistiques pour {self.metric_to_optimize}:\n")
                f.write(f"  Moyenne: {df_success[metric_col].mean():.4f}\n")
                f.write(f"  Médiane: {df_success[metric_col].median():.4f}\n")
                f.write(f"  Écart-type: {df_success[metric_col].std():.4f}\n")
                f.write(f"  Min: {df_success[metric_col].min():.4f}\n")
                f.write(f"  Max: {df_success[metric_col].max():.4f}\n\n")
            
            # Impact des paramètres
            param_cols = [col for col in df_success.columns if col.startswith('param_')]
            f.write("Impact des paramètres (par moyenne):\n")
            for param in param_cols:
                param_name = param.replace('param_', '')
                if metric_col in df_success.columns:
                    impact = df_success.groupby(param)[metric_col].mean().sort_values(ascending=False)
                    f.write(f"\n  {param_name}:\n")
                    for value, score in impact.items():
                        f.write(f"    {value}: {score:.4f}\n")
        
        print(f"Statistiques détaillées sauvegardées: {stats_file}")


def main():
    """
    Fonction principale - Exemple d'utilisation
    """
    print("=" * 60)
    print("YOLO GRID SEARCH TRAINER")
    print("=" * 60)
    
    # Configuration
    DATA_YAML = "path/to/your/data.yaml"  # À MODIFIER
    
    # Choisir le type de grid search
    print("\nChoisissez le type de grid search:")
    print("1. Minimal (rapide, pour tests)")
    print("2. Complet (long, exploration complète)")
    print("3. Augmentation agressive (focus sur data augmentation)")
    print("4. Personnalisé")
    
    choice = input("\nVotre choix (1-4): ").strip()
    
    if choice == "1":
        param_grid = get_minimal_grid()
        print("\n✓ Grid search minimal sélectionné")
    elif choice == "2":
        param_grid = get_default_params()
        print("\n✓ Grid search complet sélectionné")
    elif choice == "3":
        param_grid = get_aggressive_augmentation_grid()
        print("\n✓ Grid search augmentation agressive sélectionné")
    else:
        # Grid personnalisé
        param_grid = {
            "model_name": ["yolo11n.pt", "yolo11s.pt"],
            "epochs": [50, 100],
            "batch_size": [16],
            "lr0": [0.001, 0.01],
            "optimizer": ["Adam", "SGD"],
            "dropout": [0.0, 0.1],
        }
        print("\n✓ Grid search personnalisé sélectionné")
    
    # Créer le grid search trainer
    trainer = GridSearchTrainer(
        data_yaml=DATA_YAML,
        param_grid=param_grid,
        output_dir="runs/grid_search",
        metric_to_optimize="mAP50-95",
        max_combinations=None,  # None = toutes les combinaisons
        save_all_models=False
    )
    
    # Lancer le grid search
    results = trainer.run()
    
    # Analyser les résultats
    print("\nAnalyse des résultats...")
    trainer.analyze_results()
    
    print("\n✓ Grid search terminé avec succès!")
    print(f"Consultez les résultats dans: {trainer.session_dir}")


if __name__ == "__main__":
    # Exemple d'utilisation rapide
    
    # CONFIGURATION À MODIFIER
    DATA_YAML = "data/dataset/data.yaml"  # Chemin vers votre dataset YOLO
    
    # Grid search minimal pour test rapide
    param_grid_test = {
        "model_name": ["yolo11n.pt"],
        "epochs": [5, 10],
        "batch_size": [16],
        "lr0": [0.01],
        "optimizer": ["Adam"],
    }
    
    # Créer et lancer le trainer
    trainer = GridSearchTrainer(
        data_yaml=DATA_YAML,
        param_grid=param_grid_test,
        output_dir="runs/grid_search",
        metric_to_optimize="mAP50-95"
    )
    
    # Décommenter pour lancer
    # results = trainer.run()
    # trainer.analyze_results()
    
    print("\n" + "=" * 60)
    print("Script prêt!")
    print("Modifiez DATA_YAML avec le chemin vers votre dataset")
    print("Décommentez les lignes à la fin pour lancer le grid search")
    print("=" * 60)
