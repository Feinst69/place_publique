#!/usr/bin/env python3
"""
Script de validation du fichier cameras.json
Vérifie que la configuration est correcte avant de lancer le scraping
"""

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

def validate_cameras_config(config_file):
    """Valide la configuration des caméras"""
    
    print("=" * 70)
    print("Validation de la Configuration des Caméras")
    print("=" * 70)
    
    # Vérifier l'existence du fichier
    if not config_file.exists():
        print(f"❌ Erreur: Fichier non trouvé: {config_file}")
        return False
    
    # Charger le JSON
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✓ Fichier JSON valide")
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON: {e}")
        return False
    
    # Vérifier la structure de base
    if 'cameras' not in config:
        print("❌ Clé 'cameras' manquante")
        return False
    
    if 'settings' not in config:
        print("❌ Clé 'settings' manquante")
        return False
    
    print("✓ Structure de base correcte")
    
    # Valider les paramètres globaux
    settings = config['settings']
    required_settings = ['interval_minutes', 'wait_time', 'api_url']
    
    for setting in required_settings:
        if setting not in settings:
            print(f"❌ Paramètre manquant: {setting}")
            return False
    
    # Vérifier les valeurs des paramètres
    try:
        interval = float(settings['interval_minutes'])
        if interval < 0.25:
            print(f"⚠️  Avertissement: interval_minutes très court ({interval} min)")
        print(f"✓ interval_minutes: {interval} minutes")
    except (ValueError, TypeError):
        print(f"❌ interval_minutes invalide: {settings['interval_minutes']}")
        return False
    
    try:
        wait_time = float(settings['wait_time'])
        if wait_time < 5:
            print(f"⚠️  Avertissement: wait_time très court ({wait_time}s)")
        if wait_time > 60:
            print(f"⚠️  Avertissement: wait_time très long ({wait_time}s)")
        print(f"✓ wait_time: {wait_time} secondes")
    except (ValueError, TypeError):
        print(f"❌ wait_time invalide: {settings['wait_time']}")
        return False
    
    api_url = settings['api_url']
    try:
        result = urlparse(api_url)
        if not all([result.scheme, result.netloc]):
            raise ValueError("URL invalide")
        print(f"✓ api_url: {api_url}")
    except ValueError:
        print(f"❌ api_url invalide: {api_url}")
        return False
    
    # Valider les caméras
    cameras = config['cameras']
    
    if not cameras:
        print("❌ Aucune caméra configurée")
        return False
    
    if not isinstance(cameras, list):
        print("❌ 'cameras' doit être une liste")
        return False
    
    print(f"\n✓ Nombre de caméras: {len(cameras)}")
    print("-" * 70)
    
    enabled_count = 0
    camera_names = set()
    
    for i, camera in enumerate(cameras, 1):
        print(f"\nCaméra #{i}:")
        
        # Vérifier les champs obligatoires
        required_fields = ['name', 'display_name', 'url']
        for field in required_fields:
            if field not in camera:
                print(f"  ❌ Champ manquant: {field}")
                return False
        
        # Vérifier l'unicité du nom
        name = camera['name']
        if not isinstance(name, str) or not name:
            print(f"  ❌ 'name' invalide: {name}")
            return False
        
        if name in camera_names:
            print(f"  ❌ Nom de caméra dupliqué: {name}")
            return False
        
        camera_names.add(name)
        
        # Vérifier le format du nom
        if not name.replace('_', '').isalnum():
            print(f"  ⚠️  Avertissement: 'name' contient des caractères spéciaux: {name}")
        
        print(f"  ✓ name: {name}")
        print(f"  ✓ display_name: {camera['display_name']}")
        
        # Vérifier l'URL
        url = camera['url']
        if not isinstance(url, str):
            print(f"  ❌ 'url' invalide: {url}")
            return False
        
        if 'skylinewebcams.com' not in url.lower():
            print(f"  ⚠️  Avertissement: URL ne semble pas être une caméra SkylineWebcams")
            print(f"     URL: {url}")
        
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValueError()
            print(f"  ✓ url: {url[:60]}...")
        except:
            print(f"  ❌ 'url' n'est pas une URL valide")
            return False
        
        # Vérifier l'état enabled
        enabled = camera.get('enabled', True)
        if not isinstance(enabled, bool):
            print(f"  ❌ 'enabled' doit être true ou false")
            return False
        
        status = "🟢 ACTIVE" if enabled else "⚫ INACTIVE"
        print(f"  {status}")
        
        if enabled:
            enabled_count += 1
    
    print("\n" + "=" * 70)
    print(f"Caméras actives: {enabled_count}/{len(cameras)}")
    
    if enabled_count == 0:
        print("❌ Erreur: Aucune caméra n'est activée!")
        return False
    
    print("=" * 70)
    print("✓ Configuration VALIDE!")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    config_file = Path(__file__).parent / "cameras.json"
    
    try:
        is_valid = validate_cameras_config(config_file)
        sys.exit(0 if is_valid else 1)
    except Exception as e:
        print(f"❌ Erreur lors de la validation: {e}")
        sys.exit(1)
