import os
from db_detection_main import DetectionMainDatabase
from db_detection_class import DetectionClassDatabase

def reset_database():
    print("--- Réinitialisation des bases de données de détection ---")
    
    db_main = DetectionMainDatabase()
    db_class = DetectionClassDatabase()

    print(f"DB Main: {db_main.db_path}")
    print(f"DB Class: {db_class.db_path}\n")
    
    confirm = input("Êtes-vous sûr de vouloir supprimer TOUTES les données des deux bases de données ? (y/n) : ")
    
    if confirm.lower() == 'y':
        try:
            # Vider la base de données principale
            conn_main = db_main.connect()
            cursor_main = conn_main.cursor()
            cursor_main.execute("DELETE FROM detection_main")
            conn_main.commit()
            db_main.close()
            print("✓ Table detection_main vidée")
            
            # Vider la base de données des classes
            conn_class = db_class.connect()
            cursor_class = conn_class.cursor()
            cursor_class.execute("DELETE FROM detection_class")
            conn_class.commit()
            db_class.close()
            print("✓ Table detection_class vidée")
            
            print("\nSuccès : Toutes les données ont été supprimées.")
                
        except Exception as e:
            print(f"Une erreur est survenue : {e}")
    else:
        print("Opération annulée.")

if __name__ == "__main__":
    reset_database()