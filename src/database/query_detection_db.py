from db_detection_main import DetectionMainDatabase

db = DetectionMainDatabase()

print("--- CONTENU DE LA TABLE : DETECTION_MAIN ---")
print(f"Base de données: {db.db_path}\n")
detections = db.get_all_detections()

if detections:
    # Header
    print(f"{'DATE':<12} | {'HEURE':<10} | {'OBJETS':<8} | {'IMAGE URL'}")
    print("-" * 70)
    for detection in detections:
        print(f"{detection['date']:<12} | {detection['time']:<10} | {detection['num_detections']:<8} | {detection['image_url']}")
    print(f"\nTotal : {len(detections)} enregistrements.")
else:
    print("La table est vide.")

db.close()