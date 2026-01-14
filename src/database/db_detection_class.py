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
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            db_path = os.path.join(base_dir, "data", "final", "db_detection_class.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn = None
        self.create_tables()
    
    def connect(self):
        """Établit la connexion à la base de données."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Ferme la connexion à la base de données."""
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """Crée la table des classes détectées si elle n'existe pas."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Table : Détails des objets détectés par classe (une ligne par classe/image)
        # Colonnes : ID | IMAGE_URL | WEBCAM_NAME | CLASS | CONFIDENCE | DETECTION_COUNT
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detection_class (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_url TEXT NOT NULL,
                webcam_name TEXT,
                class TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index pour améliorer les performances
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_image_url ON detection_class(image_url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_name ON detection_class(class)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_webcam_name ON detection_class(webcam_name)")
        
        conn.commit()
        self.close()
    
    def insert_detection_class(self, image_url: str, class_name: str, confidence: float, detection_count: int, webcam_name: str = None) -> bool:
        """
        Insère un détail de détection par classe dans la base de données.
        
        Args:
            image_url: URL/nom de l'image
            class_name: Classe de l'objet détecté
            confidence: Confiance de la détection
            detection_count: Nombre d'objets détectés de cette classe
            webcam_name: Nom de la webcam (optionnel)
        
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
                INSERT INTO detection_class (image_url, webcam_name, class, confidence, detection_count)
                VALUES (?, ?, ?, ?, ?)
            """, (image_filename, webcam_name, class_name, confidence, detection_count))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'insertion de la classe: {e}")
            conn.rollback()
            return False
        finally:
            self.close()
    
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
            self.close()
    
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
            self.close()
    
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
            self.close()
    
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
            self.close()
    
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
            self.close()
    
    def get_statistics_by_webcam(self, webcam_name: str = None) -> Dict:
        """
        Récupère les statistiques détaillées par webcam.
        
        Args:
            webcam_name: Nom de la webcam (optionnel, si None retourne toutes les webcams)
        
        Returns:
            Dictionnaire avec les statistiques par webcam et par image
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            if webcam_name:
                cursor.execute("""
                    SELECT image_url, class, confidence, detection_count, created_at
                    FROM detection_class
                    WHERE webcam_name = ?
                    ORDER BY created_at DESC, image_url
                """, (webcam_name,))
            else:
                cursor.execute("""
                    SELECT webcam_name, image_url, class, confidence, detection_count, created_at
                    FROM detection_class
                    WHERE webcam_name IS NOT NULL
                    ORDER BY webcam_name, created_at DESC, image_url
                """)
            
            results = {}
            for row in cursor.fetchall():
                if webcam_name:
                    cam = webcam_name
                else:
                    cam = row['webcam_name']
                
                if cam not in results:
                    results[cam] = {}
                
                img_url = row['image_url']
                if img_url not in results[cam]:
                    results[cam][img_url] = {
                        'detections': {},
                        'timestamp': row['created_at']
                    }
                
                results[cam][img_url]['detections'][row['class']] = {
                    'count': row['detection_count'],
                    'confidence': row['confidence']
                }
            
            return results
            
        finally:
            self.close()
    
    def get_webcam_summary(self) -> List[Dict]:
        """
        Récupère un résumé des statistiques pour chaque webcam.
        
        Returns:
            Liste de dictionnaires avec les stats par webcam
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    webcam_name,
                    COUNT(DISTINCT image_url) as total_images,
                    COUNT(*) as total_detections,
                    SUM(detection_count) as total_objects
                FROM detection_class
                WHERE webcam_name IS NOT NULL
                GROUP BY webcam_name
                ORDER BY total_objects DESC
            """)
            
            summary = []
            for row in cursor.fetchall():
                summary.append({
                    'webcam_name': row['webcam_name'],
                    'total_images': row['total_images'],
                    'total_detections': row['total_detections'],
                    'total_objects': row['total_objects']
                })
            
            return summary
            
        finally:
            self.close()
    
    def get_detection_timeline(self, webcam_name: str = None) -> Dict:
        """
        Récupère l'évolution temporelle des détections par classe.
        
        Args:
            webcam_name: Nom de la webcam (optionnel, filtre les résultats)
        
        Returns:
            Dictionnaire avec les données temporelles par classe
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            if webcam_name:
                cursor.execute("""
                    SELECT 
                        image_url,
                        class,
                        detection_count,
                        created_at
                    FROM detection_class
                    WHERE webcam_name = ?
                    ORDER BY created_at ASC
                """, (webcam_name,))
            else:
                cursor.execute("""
                    SELECT 
                        image_url,
                        class,
                        detection_count,
                        created_at
                    FROM detection_class
                    ORDER BY created_at ASC
                """)
            
            # Organiser les données par classe
            timeline_data = {}
            image_index = {}
            image_counter = 0
            
            for row in cursor.fetchall():
                img_url = row['image_url']
                class_name = row['class']
                count = row['detection_count']
                
                # Attribuer un index numérique à chaque image
                if img_url not in image_index:
                    image_index[img_url] = image_counter
                    image_counter += 1
                
                # Initialiser la classe si nécessaire
                if class_name not in timeline_data:
                    timeline_data[class_name] = {
                        'labels': [],
                        'data': []
                    }
                
                # Ajouter les données
                timeline_data[class_name]['labels'].append(image_index[img_url])
                timeline_data[class_name]['data'].append(count)
            
            return timeline_data
            
        finally:
            self.close()

if __name__ == "__main__":
    db = DetectionClassDatabase()
    print(f"Base de données 'db_detection_class' créée: {db.db_path}")
