import sqlite3
import os
from typing import List, Dict, Optional

class DetectionClassDatabase:
    def __init__(self, db_path: str = None):
        """
        Initialise la connexion à la base de données des classes détectées.
        
        Args:
            db_path: Chemin vers le fichier de base de données.
                    Par défaut: data/final/db_detection_class.db
        """
        if db_path is None:
            # Chemin par défaut
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            db_path = os.path.join(base_dir, "data", "final", "db_detection_class.db")
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
        """Crée la table des classes détectées si elle n'existe pas."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Table : Détails des objets détectés par classe (une ligne par classe/image)
        # Colonnes : ID | IMAGE_URL | CLASS | CONFIDENCE | DETECTION_COUNT
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detection_class (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_url TEXT NOT NULL,
                class TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index pour améliorer les performances
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_image_url ON detection_class(image_url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_name ON detection_class(class)")
        
        conn.commit()
        self.close(conn)
    
    def insert_detection_class(self, image_url: str, class_name: str, confidence: float, detection_count: int) -> bool:
        """
        Insère un détail de détection par classe dans la base de données.
        
        Args:
            image_url: URL/nom de l'image
            class_name: Classe de l'objet détecté
            confidence: Confiance de la détection
            detection_count: Nombre d'objets détectés de cette classe
        
        Returns:
            True si l'insertion a réussi, False sinon
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Extraire juste le nom du fichier si c'est un chemin
            image_filename = image_url.split('/')[-1]
            
            # Insertion dans la table detection_class avec juste le nom du fichier
            cursor.execute("""
                INSERT INTO detection_class (image_url, class, confidence, detection_count)
                VALUES (?, ?, ?, ?)
            """, (image_filename, class_name, confidence, detection_count))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'insertion de la classe: {e}")
            conn.rollback()
            return False
        finally:
            self.close(conn)
    
    def insert_batch_class(self, image_url: str, detections: List[Dict]) -> bool:
        """
        Insère plusieurs détails de détections par classe à la fois.
        
        Args:
            image_url: URL/nom de l'image
            detections: Liste de dictionnaires avec les détails
                       Format: [{"class": "person", "confidence": 0.95, "count": 2}, ...]
        
        Returns:
            True si l'insertion a réussi, False sinon
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Extraire juste le nom du fichier si c'est un chemin
            image_filename = image_url.split('/')[-1]
            
            # Insertion en batch avec juste le nom du fichier
            for detection in detections:
                cursor.execute("""
                    INSERT INTO detection_class (image_url, class, confidence, detection_count)
                    VALUES (?, ?, ?, ?)
                """, (
                    image_filename,
                    detection['class'],
                    detection['confidence'],
                    detection['count']
                ))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'insertion batch: {e}")
            conn.rollback()
            return False
        finally:
            self.close(conn)
    
    def get_class_by_image(self, image_url: str) -> List[Dict]:
        """
        Récupère toutes les classes détectées pour une image spécifique.
        
        Args:
            image_url: Le nom du fichier image
        
        Returns:
            Liste des classes détectées
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, image_url, class, confidence, detection_count, created_at
                FROM detection_class 
                WHERE image_url = ?
                ORDER BY class
            """, (image_url,))
            
            classes = [dict(row) for row in cursor.fetchall()]
            return classes
            
        finally:
            self.close(conn)
    
    def get_detections_by_class(self, class_name: str, limit: int = None) -> List[Dict]:
        """
        Récupère toutes les détections pour une classe spécifique.
        
        Args:
            class_name: Classe de l'objet
            limit: Nombre maximum de résultats
        
        Returns:
            Liste des détections
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            if limit:
                cursor.execute("""
                    SELECT id, image_url, class, confidence, detection_count, created_at
                    FROM detection_class 
                    WHERE class = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (class_name, limit))
            else:
                cursor.execute("""
                    SELECT id, image_url, class, confidence, detection_count, created_at
                    FROM detection_class 
                    WHERE class = ?
                    ORDER BY created_at DESC
                """, (class_name,))
            
            detections = [dict(row) for row in cursor.fetchall()]
            return detections
            
        finally:
            self.close(conn)
    
    def get_all_detections(self) -> List[Dict]:
        """
        Récupère tous les enregistrements de détections par classe avec image_url.
        
        Returns:
            Liste de tous les enregistrements
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, image_url, class, confidence, detection_count, created_at
                FROM detection_class
                ORDER BY created_at DESC
            """)
            
            detections = [dict(row) for row in cursor.fetchall()]
            return detections
            
        finally:
            self.close(conn)
    
    def get_class_statistics(self) -> Dict:
        """
        Récupère les statistiques par classe.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT class, COUNT(*) as count, AVG(confidence) as avg_confidence, SUM(detection_count) as total
                FROM detection_class
                GROUP BY class
                ORDER BY total DESC
            """)
            
            stats = {}
            for row in cursor.fetchall():
                stats[row['class']] = {
                    'count': row['count'],
                    'avg_confidence': round(row['avg_confidence'], 2),
                    'total_detections': row['total']
                }
            
            return stats
            
        finally:
            self.close(conn)

    def get_class_trend_per_day(self) -> List[Dict]:
        """Total d'objets détectés par classe et par jour."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT class,
                       DATE(created_at) as date,
                       SUM(detection_count) as total
                FROM detection_class
                GROUP BY class, DATE(created_at)
                ORDER BY date ASC, total DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            self.close(conn)

    def get_per_frame_counts(self) -> List[Dict]:
        """Retourne pour chaque image le nombre de person et de car détectés."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT
                    image_url,
                    created_at,
                    SUM(CASE WHEN class = 'person' THEN detection_count ELSE 0 END) as person_count,
                    SUM(CASE WHEN class = 'car'    THEN detection_count ELSE 0 END) as car_count
                FROM detection_class
                GROUP BY image_url
                ORDER BY created_at ASC
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            self.close(conn)

if __name__ == "__main__":
    db = DetectionClassDatabase()
    print(f"Base de données 'db_detection_class' créée: {db.db_path}")
