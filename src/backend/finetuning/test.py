from roboflow import Roboflow

rf = Roboflow(api_key="UFIRA1AKd6lJ9VxThoY3")
workspace = rf.workspace()
project = workspace.project("place_publique")

# Télécharger la version 4 (la plus récente)
version_number = 4
print(f"=== Téléchargement de la version {version_number} ===")
version = project.version(version_number)
dataset = version.download("yolov11")

print(f"\nDataset téléchargé dans: {dataset.location}")
