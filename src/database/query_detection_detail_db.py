from db_detection_class import DetectionClassDatabase

db = DetectionClassDatabase()

print("--- CONTENU DE LA TABLE : DETECTION_CLASS ---")
print(f"Base de données: {db.db_path}\n")

# Récupérer toutes les détections par classe avec image_url
detections = db.get_all_detections()

if detections:
    # Header
    print(f"{'IMAGE URL':<40} | {'CLASSE':<15} | {'CONF.':<8} | {'NOMBRE':<8}")
    print("-" * 90)
    for detection in detections:
        conf = f"{detection['confidence']:.2f}"
        print(f"{detection['image_url']:<40} | {detection['class']:<15} | {conf:<8} | {detection['detection_count']:<8}")
    print(f"\nTotal : {len(detections)} enregistrements.")
else:
    print("La table est vide.")

db.close()