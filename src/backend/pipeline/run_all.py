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
SCRAPPING_CARDIFF = BASE_DIR / "src" / "backend" / "scrapping" / "scrapping_skylinewebcams.py"
SCRAPPING_MADRID  = BASE_DIR / "src" / "backend" / "scrapping" / "scrapping_madrid.py"
SCRAPPING_TREVI   = BASE_DIR / "src" / "backend" / "scrapping" / "scrapping_trevi.py"
SCRAPPING_MURCIA  = BASE_DIR / "src" / "backend" / "scrapping" / "scrapping_murcia.py"
SCRAPPING_LAPALMA = BASE_DIR / "src" / "backend" / "scrapping" / "scrapping_lapalma.py"
API_SCRIPT = BASE_DIR / "src" / "backend" / "api_flask" / "app.py"
# VENV_PYTHON = BASE_DIR / "venv_yolo" / "Scripts" / "python.exe"
VENV_PYTHON = Path(sys.executable)
API_PORT = int(os.environ.get("PORT", "5000"))

def check_scripts_exist():
    """Vérifier que les scripts existent"""
    required = [
        (SCRAPPING_CARDIFF, "Scrapping Cardiff"),
        (SCRAPPING_MURCIA,  "Scrapping Murcia"),
        (SCRAPPING_LAPALMA, "Scrapping La Palma"),
        (API_SCRIPT,        "API Flask"),
        (VENV_PYTHON,       "Python venv"),
    ]
    ok = True
    for path, name in required:
        if not path.exists():
            print(f"Erreur: {name} introuvable: {path}")
            ok = False
    return ok

def launch_processes():
    """Lancer les deux processus en parallèle"""
    print("=" * 70)
    print("Lancement du système complet")
    print("=" * 70)
    
    processes = []

    try:
        # Lancer les scripts de scrapping
        scrapping_scripts = [
            ("Scrapping Cardiff",  SCRAPPING_CARDIFF),
            ("Scrapping Murcia",   SCRAPPING_MURCIA),
            ("Scrapping La Palma", SCRAPPING_LAPALMA),
        ]
        for name, script in scrapping_scripts:
            if script.exists():
                print(f"\nLancement {name}...")
                proc = subprocess.Popen(
                    [str(VENV_PYTHON), str(script)],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, cwd=str(BASE_DIR)
                )
                processes.append((name, proc))
                print(f"{name} lancé (PID: {proc.pid})")
            else:
                print(f"Script {name} introuvable, ignoré : {script}")

        # Attendre avant de lancer l'API
        time.sleep(2)
        
        # Lancer l'API Flask
        print("\nLancement de l'API Flask...")
        print(f"   Commande: {VENV_PYTHON} {API_SCRIPT}")
        child_env = os.environ.copy()
        child_env["PORT"] = str(API_PORT)

        api_process = subprocess.Popen(
            [str(VENV_PYTHON), str(API_SCRIPT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(BASE_DIR),
            env=child_env
        )
        processes.append(("API Flask", api_process))
        print(f"API Flask lancée (PID: {api_process.pid})")
        
        print("\n" + "=" * 70)
        print("Les deux processus tournent en parallèle")
        print("   - Scrapping: Capture les images webcam")
        print("   - API Flask: Traite les images détectées")
        print("=" * 70)
        print(f"\nAccès au dashboard: http://localhost:{API_PORT}")
        print("Appuyez sur Ctrl+C pour arrêter tous les processus\n")
        
        # Garder les processus actifs
        stopped_reported = set()
        while True:
            for name, process in processes:
                if process.poll() is None:
                    continue

                if name in stopped_reported:
                    continue
                stopped_reported.add(name)

                exit_code = process.returncode
                print(f"\n{name} s'est arrêté de manière inattendue (code={exit_code})")

                # Afficher les derniers logs du processus arrêté
                try:
                    if process.stdout:
                        remaining = process.stdout.read().strip()
                        if remaining:
                            print(f"--- Logs {name} ---")
                            print(remaining)
                            print(f"--- Fin logs {name} ---")
                except Exception:
                    pass

                # Si l'API tombe, arrêter tout le système pour éviter un état incohérent
                if name == "API Flask":
                    print("Arrêt des autres processus car l'API est indisponible...")
                    for other_name, other_process in processes:
                        if other_process.poll() is None:
                            other_process.terminate()
                    sys.exit(1)

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
        print("\nVérification échouée. Veuillez vérifier les chemins.")
        sys.exit(1)
    
    print("Tous les scripts sont présents\n")
    
    launch_processes()
