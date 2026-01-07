#!/usr/bin/env python
"""
Script de lancement complet :
- Lance le scrapping webcam (capture d'images)
- Lance l'API Flask (traitement des images)
Les deux processus tournent en parallèle
"""

import subprocess
import sys
import time
import os
from pathlib import Path

# Déterminer le répertoire racine (remonter 3 niveaux : pipeline -> backend -> src -> racine)
BASE_DIR = Path(__file__).resolve().parents[3]

# Chemins des scripts
SCRAPPING_SCRIPT = BASE_DIR / "src" / "backend" / "scrapping" / "scrapping_skylinewebcams.py"
API_SCRIPT = BASE_DIR / "src" / "backend" / "api_flask" / "app.py"
VENV_PYTHON = BASE_DIR / "pb_env" / "Scripts" / "python.exe"

def check_scripts_exist():
    """Vérifier que les scripts existent"""
    if not SCRAPPING_SCRIPT.exists():
        print(f"❌ Erreur: Script de scrapping introuvable: {SCRAPPING_SCRIPT}")
        return False
    if not API_SCRIPT.exists():
        print(f"❌ Erreur: Script API introuvable: {API_SCRIPT}")
        return False
    if not VENV_PYTHON.exists():
        print(f"❌ Erreur: Python virtual env introuvable: {VENV_PYTHON}")
        return False
    return True

def launch_processes():
    """Lancer les deux processus en parallèle"""
    print("=" * 70)
    print("Lancement du système complet")
    print("=" * 70)
    
    processes = []
    
    try:
        # Lancer le scrapping
        print("\nLancement du scrapping webcam...")
        print(f"   Commande: {VENV_PYTHON} {SCRAPPING_SCRIPT}")
        scrapping_process = subprocess.Popen(
            [str(VENV_PYTHON), str(SCRAPPING_SCRIPT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(BASE_DIR)
        )
        processes.append(("Scrapping", scrapping_process))
        print(f"Scrapping lancé (PID: {scrapping_process.pid})")
        
        # Attendre un peu avant de lancer l'API
        time.sleep(2)
        
        # Lancer l'API Flask
        print("\nLancement de l'API Flask...")
        print(f"   Commande: {VENV_PYTHON} {API_SCRIPT}")
        api_process = subprocess.Popen(
            [str(VENV_PYTHON), str(API_SCRIPT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(BASE_DIR)
        )
        processes.append(("API Flask", api_process))
        print(f"API Flask lancée (PID: {api_process.pid})")
        
        print("\n" + "=" * 70)
        print("Les deux processus tournent en parallèle")
        print("   - Scrapping: Capture les images webcam")
        print("   - API Flask: Traite les images détectées")
        print("=" * 70)
        print("\nAccès au dashboard: http://localhost:5000")
        print("Appuyez sur Ctrl+C pour arrêter tous les processus\n")
        
        # Garder les processus actifs
        while True:
            for name, process in processes:
                if process.poll() is not None:
                    # Le processus s'est arrêté
                    print(f"\n{name} s'est arrêté de manière inattendue")
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("Arrêt de tous les processus...")
        print("=" * 70)
        
        # Terminer tous les processus
        for name, process in processes:
            if process.poll() is None:
                print(f"   Arrêt de {name} (PID: {process.pid})...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                    print(f"   {name} arrêté")
                except subprocess.TimeoutExpired:
                    print(f"   Forçage de l'arrêt de {name}...")
                    process.kill()
        
        print("=" * 70)
        print("Tous les processus ont été arrêtés")
        sys.exit(0)
    
    except Exception as e:
        print(f"\nErreur: {e}")
        # Nettoyer
        for name, process in processes:
            if process.poll() is None:
                process.kill()
        sys.exit(1)

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Vérification des scripts...")
    print("=" * 70)
    
    if not check_scripts_exist():
        print("\n❌ Vérification échouée. Veuillez vérifier les chemins.")
        sys.exit(1)
    
    print("✅ Tous les scripts sont présents\n")
    
    launch_processes()
