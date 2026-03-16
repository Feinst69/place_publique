import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

class DetectionMainDatabase:
    def __init__(self, db_path: str = None):
        """
        Initialise la connexion à la base de données principale des détections.
        
        Args:
            db_path: Chemin vers le fichier de base de données.
                    Par défaut: data/final/db_detection_main.db
        """
        if db_path is None:
            # Chemin par défaut
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            db_path = os.path.join(base_dir, "data", "final", "db_detection_main.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn = None
        self.create_tables()
    
    def connect(self):
        """Établit une connexion SQLite locale à la base de données."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def close(self, conn=None):
        """Ferme une connexion SQLite locale (ou la connexion legacy si fournie)."""
        target = conn if conn is not None else self.conn
        if target:
            target.close()
    
    def create_tables(self):
        """Crée la table principale des détections si elle n'existe pas."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Table : Informations principales des détections
        # Colonnes : IMAGE_URL | DATE | HEURE | DATETIME | NUM_DETECTIONS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detection_main (
                image_url TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                datetime TEXT NOT NULL,
                num_detections INTEGER NOT NULL,
                source TEXT DEFAULT 'unknown',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index pour améliorer les performances
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_main_image_url ON detection_main(image_url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_main_datetime ON detection_main(datetime)")

        # Migration légère: ajouter la colonne source si DB existante sans ce champ
        cursor.execute("PRAGMA table_info(detection_main)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "source" not in existing_cols:
            cursor.execute("ALTER TABLE detection_main ADD COLUMN source TEXT DEFAULT 'unknown'")
        
        conn.commit()
        self.close(conn)
    
    def insert_detection(self, image_url: str, date: str, time: str, datetime_str: str, num_detections: int, source: str = "unknown") -> bool:
        """
        Insère une nouvelle détection dans la base de données.
        
        Args:
            image_url: URL/nom de l'image
            date: Date au format YYYY-MM-DD
            time: Heure au format HH:MM:SS
            datetime_str: Date et heure combinées au format YYYY-MM-DD HH:MM:SS
            num_detections: Nombre total de détections
            source: Nom du lieu/caméra (ex: Cardiff)
        
        Returns:
            True si l'insertion a réussi, False sinon
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Extraire juste le nom du fichier si c'est un chemin
            image_filename = image_url.split('/')[-1]
            
            # Vérifier si la détection existe déjà
            cursor.execute("SELECT COUNT(*) FROM detection_main WHERE image_url = ?", (image_filename,))
            if cursor.fetchone()[0] > 0:
                print(f"Info: La détection '{image_filename}' existe déjà (doublon ignoré).")
                self.close(conn)
                return False
            
            # Insertion dans la table detection_main avec juste le nom du fichier
            cursor.execute("""
                INSERT INTO detection_main (image_url, date, time, datetime, num_detections, source)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (image_filename, date, time, datetime_str, num_detections, source))

            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'insertion: {e}")
            conn.rollback()
            return False
        finally:
            self.close(conn)
    
    def get_all_detections(self, limit: int = None, offset: int = 0) -> List[Dict]:
        """
        Récupère toutes les détections.
        
        Args:
            limit: Nombre maximum de résultats (None = tous)
            offset: Décalage pour la pagination
        
        Returns:
            Liste des détections
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            if limit:
                cursor.execute("""
                    SELECT * FROM detection_main 
                    ORDER BY datetime DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            else:
                cursor.execute("SELECT * FROM detection_main ORDER BY datetime DESC")
            
            detections = [dict(row) for row in cursor.fetchall()]
            return detections
            
        finally:
            self.close(conn)
    
    def get_detection_by_url(self, image_url: str) -> Optional[Dict]:
        """
        Récupère une détection par son image_url.
        
        Args:
            image_url: Le nom du fichier image
        
        Returns:
            Dictionnaire contenant les données de détection ou None
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM detection_main WHERE image_url = ?", (image_url,))
            detection = cursor.fetchone()
            
            if not detection:
                return None
            
            return dict(detection)
            
        finally:
            self.close(conn)
    
    def get_detections_by_date(self, date: str) -> List[Dict]:
        """
        Récupère toutes les détections d'une date spécifique.

        Args:
            date: Date au format YYYY-MM-DD

        Returns:
            Liste des détections
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM detection_main 
                WHERE date = ? 
                ORDER BY time DESC
            """, (date,))

            detections = [dict(row) for row in cursor.fetchall()]
            return detections

        finally:
            self.close(conn)

    def get_detections_per_day(self) -> List[Dict]:
        """Nombre d'images analysées et d'objets détectés par jour."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT date,
                       COUNT(*) as images,
                       SUM(num_detections) as objects
                FROM detection_main
                GROUP BY date
                ORDER BY date ASC
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            self.close(conn)

    def get_hourly_activity(self) -> List[Dict]:
        """Nombre d'analyses par heure de la journée (0-23)."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT CAST(substr(time, 1, 2) AS INTEGER) as hour,
                       COUNT(*) as images,
                       SUM(num_detections) as objects
                FROM detection_main
                GROUP BY hour
                ORDER BY hour ASC
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            self.close(conn)

    def get_summary(self) -> Dict:
        """Résumé global : total images, objets, moyenne, max, première/dernière."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*) as total_images,
                       SUM(num_detections) as total_objects,
                       ROUND(AVG(num_detections), 2) as avg_per_image,
                       MAX(num_detections) as max_per_image,
                       MIN(datetime) as first_detection,
                       MAX(datetime) as last_detection
                FROM detection_main
            """)
            row = cursor.fetchone()
            return dict(row) if row else {}
        finally:
            self.close(conn)

if __name__ == "__main__":
    db = DetectionMainDatabase()
    print(f"Base de données 'db_detection_main' créée: {db.db_path}")
