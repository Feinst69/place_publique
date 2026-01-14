"""
Script de migration pour ajouter la colonne webcam_name à la table detection_class
"""
import sqlite3
import os

# Chemin vers la base de données
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
db_path = os.path.join(base_dir, "data", "final", "db_detection_class.db")

print(f"Migration de la base de données: {db_path}")

# Connexion à la base de données
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Vérifier si la table existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='detection_class'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("ℹ️  La table detection_class n'existe pas encore.")
        print("✅ Elle sera créée automatiquement par l'application avec la bonne structure.")
    else:
        # Vérifier si la colonne existe déjà
        cursor.execute("PRAGMA table_info(detection_class)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'webcam_name' in columns:
            print("✅ La colonne webcam_name existe déjà")
        else:
            print("📝 Ajout de la colonne webcam_name...")
            cursor.execute("ALTER TABLE detection_class ADD COLUMN webcam_name TEXT")
            print("✅ Colonne ajoutée")
            
            print("📝 Création de l'index...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_webcam_name ON detection_class(webcam_name)")
            print("✅ Index créé")
            
            conn.commit()
            print("\n✅ Migration terminée avec succès!")
        
except Exception as e:
    print(f"❌ Erreur lors de la migration: {e}")
    conn.rollback()
finally:
    conn.close()
