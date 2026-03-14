#!/usr/bin/env python3
"""
train_pipeline.py — Pipeline complet de fine-tuning YOLOv11 sur données COCO JSON.

Usage:
    python train_pipeline.py --data_root "C:\...\car" --label car
"""

import argparse
import json
import os
import random
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.20
TEST_RATIO = 0.10

EPOCHS = 100
IMGSZ = 640
BATCH = 8
PATIENCE = 20
OPTIMIZER = "AdamW"
LR0 = 0.01
LRF = 0.1
WARMUP_EPOCHS = 5
CLOSE_MOSAIC = 10
BASE_MODEL = "yolo11s.pt"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def log_info(msg: str):
    print(f"[INFO] {msg}")


def log_warn(msg: str):
    print(f"[WARNING] {msg}")


def log_error(msg: str):
    print(f"[ERROR] {msg}", file=sys.stderr)


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)


# ---------------------------------------------------------------------------
# STEP 0 — Argument parsing & validation
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Fine-tune YOLOv11 on COCO-annotated data."
    )
    parser.add_argument(
        "--data_root",
        type=str,
        required=True,
        help="Absolute path to root folder containing train_* sub-folders.",
    )
    parser.add_argument(
        "--label",
        type=str,
        required=True,
        help="Short label for output naming (e.g. car, pedestrian).",
    )
    parser.add_argument(
        "--class_mapping",
        type=str,
        default=None,
        help='Optional class renaming, e.g. "cars:car,vehicle:car".',
    )
    return parser.parse_args()


def discover_train_dirs(data_root: Path):
    """Return sorted list of train_* directories inside data_root."""
    dirs = sorted(
        [
            d
            for d in data_root.iterdir()
            if d.is_dir() and d.name.startswith("train_")
        ]
    )
    return dirs


def find_coco_json(train_dir: Path) -> Path | None:
    """Find a COCO JSON file inside a train_* directory."""
    for f in train_dir.iterdir():
        if f.suffix == ".json":
            return f
    return None


def find_images(train_dir: Path) -> list[Path]:
    """Return image files in the given directory."""
    return [f for f in train_dir.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS]


def validate_inputs(data_root: Path, label: str):
    """Validate that data_root exists and all train_* folders are well-formed."""
    if not data_root.exists():
        log_error(f"Le dossier --data_root n'existe pas : {data_root}")
        sys.exit(1)

    train_dirs = discover_train_dirs(data_root)
    if not train_dirs:
        log_error(
            f"Aucun sous-dossier train_* trouvé dans {data_root}"
        )
        sys.exit(1)

    for td in train_dirs:
        json_file = find_coco_json(td)
        if json_file is None:
            log_error(f"Pas de fichier JSON COCO trouvé dans {td}")
            sys.exit(1)
        imgs = find_images(td)
        if not imgs:
            log_error(f"Aucune image trouvée dans {td}")
            sys.exit(1)

    names = ", ".join(d.name for d in train_dirs)
    log_info(f"Dossiers détectés : {names} ({len(train_dirs)} splits trouvés)")
    log_info(f"Label de sortie : {label}  →  modèle final : best_{label}.pt")
    return train_dirs


# ---------------------------------------------------------------------------
# STEP 1 — Merge COCO JSONs & restructure
# ---------------------------------------------------------------------------
def parse_class_mapping(raw: str | None) -> dict[str, str]:
    """Parse --class_mapping 'cars:car,vehicle:car' into a dict."""
    if not raw:
        return {}
    mapping = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if ":" not in pair:
            log_warn(f"class_mapping entrée ignorée (pas de ':') : {pair}")
            continue
        src, dst = pair.split(":", 1)
        mapping[src.strip().lower()] = dst.strip().lower()
    return mapping


def normalize_cat_name(name: str, class_mapping: dict[str, str]) -> str:
    """Lowercase + strip + apply user mapping."""
    normed = name.strip().lower()
    return class_mapping.get(normed, normed)


def load_and_merge_coco(
    train_dirs: list[Path],
    class_mapping: dict[str, str] | None = None,
):
    """
    Load all COCO JSON files, merge into a single dataset with re-indexed
    image and annotation IDs.  Category names are normalised (lower+strip)
    and optionally remapped via *class_mapping*.
    """
    if class_mapping is None:
        class_mapping = {}

    merged_images = []
    merged_annotations = []
    categories_by_name: dict[str, int] = {}

    next_img_id = 0
    next_ann_id = 0

    # First pass: build a unified category list across all JSONs
    all_cats_raw = []
    for td in train_dirs:
        json_path = find_coco_json(td)
        with open(json_path, "r", encoding="utf-8") as f:
            coco = json.load(f)
        for cat in coco.get("categories", []):
            all_cats_raw.append(cat)

    # Deduplicate categories by normalised name
    unified_categories = []
    for cat in all_cats_raw:
        name = normalize_cat_name(cat["name"], class_mapping)
        if name not in categories_by_name:
            new_id = len(categories_by_name)
            categories_by_name[name] = new_id
            unified_categories.append({"id": new_id, "name": name})

    if class_mapping:
        log_info(f"Class mapping appliqué : {class_mapping}")
    log_info(
        f"Catégories unifiées ({len(unified_categories)}) : "
        f"{', '.join(c['name'] for c in unified_categories)}"
    )

    # Second pass: merge images & annotations
    image_file_map = {}  # (folder_path, filename) -> new_img_id
    skipped_anns = 0
    for td in train_dirs:
        json_path = find_coco_json(td)
        with open(json_path, "r", encoding="utf-8") as f:
            coco = json.load(f)

        # Build local category_id → unified_id mapping
        local_cat_map = {}
        for cat in coco.get("categories", []):
            normed = normalize_cat_name(cat["name"], class_mapping)
            local_cat_map[cat["id"]] = categories_by_name[normed]

        # Build local image_id mapping
        local_img_map = {}  # old_id -> new_id
        for img in coco.get("images", []):
            old_id = img["id"]
            fname = img["file_name"]

            key = (str(td), fname)
            if key in image_file_map:
                local_img_map[old_id] = image_file_map[key]
                continue

            new_id = next_img_id
            next_img_id += 1
            local_img_map[old_id] = new_id
            image_file_map[key] = new_id

            merged_images.append(
                {
                    "id": new_id,
                    "file_name": fname,
                    "width": img["width"],
                    "height": img["height"],
                    "source_dir": str(td),
                }
            )

        # Re-index annotations — filter invalid bboxes
        for ann in coco.get("annotations", []):
            old_img_id = ann["image_id"]
            if old_img_id not in local_img_map:
                continue
            bbox = ann["bbox"]
            bw, bh = float(bbox[2]), float(bbox[3])
            if bw <= 0 or bh <= 0:
                skipped_anns += 1
                continue
            new_ann = {
                "id": next_ann_id,
                "image_id": local_img_map[old_img_id],
                "category_id": local_cat_map.get(
                    ann["category_id"], ann["category_id"]
                ),
                "bbox": bbox,
                "area": ann.get("area", 0),
                "iscrowd": ann.get("iscrowd", 0),
            }
            next_ann_id += 1
            merged_annotations.append(new_ann)

    if skipped_anns:
        log_warn(
            f"{skipped_anns} annotations ignorées (bbox w<=0 ou h<=0)"
        )

    merged_coco = {
        "images": merged_images,
        "annotations": merged_annotations,
        "categories": unified_categories,
    }

    log_info(
        f"Fusion terminée : {len(merged_images)} images, "
        f"{len(merged_annotations)} annotations, "
        f"{len(unified_categories)} classe(s)"
    )
    return merged_coco


def coco_bbox_to_yolo(bbox, img_w, img_h):
    """Convert COCO bbox [x, y, w, h] (top-left) to YOLO [cx, cy, w, h] normalised."""
    x, y, w, h = [float(v) for v in bbox]
    cx = (x + w / 2.0) / img_w
    cy = (y + h / 2.0) / img_h
    nw = w / img_w
    nh = h / img_h
    # Clamp to [0, 1]
    cx = max(0.0, min(1.0, cx))
    cy = max(0.0, min(1.0, cy))
    nw = max(0.0, min(1.0, nw))
    nh = max(0.0, min(1.0, nh))
    return cx, cy, nw, nh


def build_yolo_dataset(merged_coco: dict, data_root: Path, label: str):
    """
    Split the merged dataset into train/val/test, copy images and write
    YOLO-format label files. Returns the dataset directory path and split counts.
    """
    set_seed(SEED)

    dataset_dir = data_root.parent / f"dataset_{label}"
    for split in ("train", "val", "test"):
        (dataset_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (dataset_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    images = merged_coco["images"]
    # Build annotation lookup: image_id -> list of annotations
    ann_by_img = defaultdict(list)
    for ann in merged_coco["annotations"]:
        ann_by_img[ann["image_id"]].append(ann)

    # Split
    indices = list(range(len(images)))
    train_idx, temp_idx = train_test_split(
        indices, test_size=(1 - TRAIN_RATIO), random_state=SEED
    )
    relative_test = TEST_RATIO / (VAL_RATIO + TEST_RATIO)
    val_idx, test_idx = train_test_split(
        temp_idx, test_size=relative_test, random_state=SEED
    )

    split_map = {}
    for i in train_idx:
        split_map[i] = "train"
    for i in val_idx:
        split_map[i] = "val"
    for i in test_idx:
        split_map[i] = "test"

    counts = {"train": 0, "val": 0, "test": 0}
    total_labels_written = 0

    for idx, img_info in enumerate(images):
        split = split_map[idx]
        counts[split] += 1

        src_path = Path(img_info["source_dir"]) / img_info["file_name"]
        dst_img = dataset_dir / "images" / split / img_info["file_name"]

        if src_path.exists():
            shutil.copy2(str(src_path), str(dst_img))
        else:
            log_warn(f"Image introuvable, ignorée : {src_path}")
            continue

        # Write YOLO label file
        label_name = Path(img_info["file_name"]).stem + ".txt"
        label_path = dataset_dir / "labels" / split / label_name

        anns = ann_by_img.get(img_info["id"], [])
        lines = []
        for ann in anns:
            cx, cy, nw, nh = coco_bbox_to_yolo(
                ann["bbox"], img_info["width"], img_info["height"]
            )
            lines.append(f"{ann['category_id']} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")
            total_labels_written += 1

        with open(label_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    log_info(
        f"Dataset YOLO créé dans {dataset_dir}"
    )
    log_info(
        f"Split : train={counts['train']}, val={counts['val']}, test={counts['test']}"
    )
    log_info(f"Labels écrits : {total_labels_written}")

    # Post-conversion verification
    verify_annotations(dataset_dir, counts)

    return dataset_dir, counts, total_labels_written


def verify_annotations(dataset_dir: Path, counts: dict):
    """Check label files vs images and report annotation stats."""
    log_info("--- Vérification post-conversion ---")
    for split in ("train", "val", "test"):
        img_dir = dataset_dir / "images" / split
        lbl_dir = dataset_dir / "labels" / split
        imgs = [
            f for f in img_dir.iterdir()
            if f.suffix.lower() in IMAGE_EXTENSIONS
        ] if img_dir.exists() else []
        with_ann = 0
        without_ann = 0
        for img_path in imgs:
            lbl_path = lbl_dir / (img_path.stem + ".txt")
            if lbl_path.exists() and lbl_path.stat().st_size > 0:
                with_ann += 1
            else:
                without_ann += 1
        total = with_ann + without_ann
        pct_bg = (without_ann / total * 100) if total else 0
        status = "OK" if pct_bg <= 30 else "ATTENTION"
        log_info(
            f"  {split:5s} : {with_ann}/{total} avec annotations, "
            f"{without_ann} backgrounds ({pct_bg:.0f}%) [{status}]"
        )
        if pct_bg > 50:
            log_warn(
                f"  {split} contient >50% de backgrounds — "
                f"vérifiez les annotations COCO source"
            )


# ---------------------------------------------------------------------------
# STEP 2 — Create data.yaml
# ---------------------------------------------------------------------------
def create_data_yaml(dataset_dir: Path, categories: list[dict]) -> Path:
    """Create the data.yaml config file for YOLO training."""
    yaml_path = dataset_dir / "data.yaml"
    class_names = [c["name"] for c in sorted(categories, key=lambda c: c["id"])]

    lines = [
        f"train: {dataset_dir / 'images' / 'train'}",
        f"val: {dataset_dir / 'images' / 'val'}",
        f"test: {dataset_dir / 'images' / 'test'}",
        "",
        f"nc: {len(class_names)}",
        f"names: {class_names}",
    ]
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    log_info(f"data.yaml généré : {yaml_path}")
    return yaml_path


# ---------------------------------------------------------------------------
# STEP 3 — Fine-tune YOLO v11
# ---------------------------------------------------------------------------
def train_yolo(data_yaml: Path, label: str, project_root: Path):
    """Launch YOLO fine-tuning and return the results object + best model path."""
    from ultralytics import YOLO

    # Configure MLflow tracking URI BEFORE loading YOLO
    # (Ultralytics callbacks read MLFLOW_TRACKING_URI at init)
    mlflow_dir = project_root / "runs" / "mlflow"
    mlflow_dir.mkdir(parents=True, exist_ok=True)
    mlflow_uri = (
        "file:///" + str(mlflow_dir.resolve()).replace("\\", "/")
    )
    os.environ["MLFLOW_TRACKING_URI"] = mlflow_uri
    log_info(f"MLFLOW_TRACKING_URI = {mlflow_uri}")

    log_info(f"Chargement du modèle de base : {BASE_MODEL}")
    model = YOLO(BASE_MODEL)

    run_name = f"yolo11_{label}"
    log_info(f"Lancement du fine-tuning ({EPOCHS} epochs, batch={BATCH}, imgsz={IMGSZ}) ...")

    results = model.train(
        data=str(data_yaml),
        epochs=EPOCHS,
        imgsz=IMGSZ,
        batch=BATCH,
        patience=PATIENCE,
        optimizer=OPTIMIZER,
        lr0=LR0,
        lrf=LRF,
        warmup_epochs=WARMUP_EPOCHS,
        mosaic=1.0,
        degrees=10.0,
        scale=0.5,
        fliplr=0.5,
        close_mosaic=CLOSE_MOSAIC,
        name=run_name,
        seed=SEED,
        verbose=True,
    )

    # Locate best.pt
    train_dir = Path(results.save_dir)
    best_pt = train_dir / "weights" / "best.pt"

    if not best_pt.exists():
        log_error(f"best.pt introuvable dans {train_dir / 'weights'}")
        sys.exit(1)

    # Copy to models/
    models_dir = project_root / "models"
    models_dir.mkdir(exist_ok=True)
    dest = models_dir / f"best_{label}.pt"
    shutil.copy2(str(best_pt), str(dest))
    log_info(f"Modèle copié : {dest}")

    return model, results, best_pt, dest


# ---------------------------------------------------------------------------
# STEP 5 — Evaluate on test set
# ---------------------------------------------------------------------------
def evaluate_test(model_path: Path, data_yaml: Path):
    """Run validation on the test split and return metrics."""
    from ultralytics import YOLO

    log_info("Évaluation sur le jeu de test ...")
    model = YOLO(str(model_path))
    metrics = model.val(data=str(data_yaml), split="test")

    results_dict = {
        "mAP50": float(metrics.box.map50),
        "mAP50-95": float(metrics.box.map),
        "precision": float(metrics.box.mp),
        "recall": float(metrics.box.mr),
    }
    log_info(
        f"Test — mAP50={results_dict['mAP50']:.4f}  "
        f"mAP50-95={results_dict['mAP50-95']:.4f}  "
        f"precision={results_dict['precision']:.4f}  "
        f"recall={results_dict['recall']:.4f}"
    )
    return results_dict


# ---------------------------------------------------------------------------
# STEP 4 — MLflow tracking
# ---------------------------------------------------------------------------
def setup_mlflow(label: str, data_root: str, data_yaml: Path,
                 merged_coco: dict, counts: dict, total_labels: int,
                 train_results, test_metrics: dict,
                 best_model_dest: Path, train_save_dir: Path):
    """Log everything to MLflow."""
    import mlflow

    # Use the same file:/// URI set for Ultralytics callbacks
    mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI", "")
    if mlflow_uri:
        mlflow.set_tracking_uri(mlflow_uri)

    experiment_name = f"yolo11_{label}_finetune"
    mlflow.set_experiment(experiment_name)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"run_{label}_{timestamp}"

    with mlflow.start_run(run_name=run_name):
        # ---- Params ----
        mlflow.log_param("data_root", data_root)
        mlflow.log_param("label", label)
        mlflow.log_param("base_model", BASE_MODEL)
        mlflow.log_param("epochs", EPOCHS)
        mlflow.log_param("imgsz", IMGSZ)
        mlflow.log_param("batch", BATCH)
        mlflow.log_param("patience", PATIENCE)
        mlflow.log_param("optimizer", OPTIMIZER)
        mlflow.log_param("lr0", LR0)
        mlflow.log_param("lrf", LRF)
        mlflow.log_param("warmup_epochs", WARMUP_EPOCHS)
        mlflow.log_param("close_mosaic", CLOSE_MOSAIC)
        mlflow.log_param("seed", SEED)
        mlflow.log_param("mosaic", 1.0)
        mlflow.log_param("degrees", 10.0)
        mlflow.log_param("scale", 0.5)
        mlflow.log_param("fliplr", 0.5)
        mlflow.log_param("train_ratio", TRAIN_RATIO)
        mlflow.log_param("val_ratio", VAL_RATIO)
        mlflow.log_param("test_ratio", TEST_RATIO)

        # Dataset info
        class_names = [c["name"] for c in merged_coco["categories"]]
        mlflow.log_param("num_classes", len(class_names))
        mlflow.log_param("class_names", str(class_names))
        mlflow.log_param("num_images_train", counts["train"])
        mlflow.log_param("num_images_val", counts["val"])
        mlflow.log_param("num_images_test", counts["test"])
        mlflow.log_param("num_images_total", sum(counts.values()))
        mlflow.log_param("num_annotations_total", total_labels)

        # ---- Training metrics (per-epoch from CSV) ----
        results_csv = train_save_dir / "results.csv"
        if results_csv.exists():
            import csv
            with open(results_csv, "r") as f:
                reader = csv.DictReader(f)
                for epoch_idx, row in enumerate(reader):
                    row = {k.strip(): v.strip() for k, v in row.items()}
                    for key, mlflow_key in [
                        ("metrics/mAP50(B)", "train/mAP50"),
                        ("metrics/mAP50-95(B)", "train/mAP50-95"),
                        ("metrics/precision(B)", "train/precision"),
                        ("metrics/recall(B)", "train/recall"),
                        ("train/box_loss", "train/box_loss"),
                        ("train/cls_loss", "train/cls_loss"),
                        ("train/dfl_loss", "train/dfl_loss"),
                    ]:
                        if key in row:
                            try:
                                mlflow.log_metric(mlflow_key, float(row[key]), step=epoch_idx)
                            except (ValueError, TypeError):
                                pass

        # ---- Test metrics ----
        for k, v in test_metrics.items():
            mlflow.log_metric(f"test/{k}", v)

        # ---- Artifacts ----
        if data_yaml.exists():
            mlflow.log_artifact(str(data_yaml))

        # Confusion matrix & PR curves
        for artifact_name in [
            "confusion_matrix.png",
            "confusion_matrix_normalized.png",
            "PR_curve.png",
            "P_curve.png",
            "R_curve.png",
            "F1_curve.png",
            "results.png",
            "results.csv",
        ]:
            artifact_path = train_save_dir / artifact_name
            if artifact_path.exists():
                mlflow.log_artifact(str(artifact_path))

        # Best model
        if best_model_dest.exists():
            mlflow.log_artifact(str(best_model_dest))

        log_info(f"MLflow — experiment='{experiment_name}', run='{run_name}'")
        log_info("MLflow — paramètres, métriques et artefacts loggés avec succès")

    return experiment_name, run_name


# ---------------------------------------------------------------------------
# STEP 6 — Generate README
# ---------------------------------------------------------------------------
def generate_readme(
    label: str,
    data_root: str,
    dataset_dir: Path,
    merged_coco: dict,
    counts: dict,
    total_labels: int,
    test_metrics: dict,
    experiment_name: str,
    run_name: str,
    project_root: Path,
):
    """Generate a README_<label>.md file documenting the pipeline run."""
    class_names = [c["name"] for c in merged_coco["categories"]]
    num_classes = len(class_names)

    md = f"""# Fine-tuning YOLOv11 — {label}

## 1. Vue d'ensemble

| Élément | Valeur |
|---------|--------|
| **Objectif** | Détecter **{label}** dans des images de webcams |
| **Modèle de base** | `{BASE_MODEL}` (Ultralytics YOLOv11-small) |
| **Dataset** | {counts['train'] + counts['val'] + counts['test']} images, {total_labels} annotations |
| **Classes** | {num_classes} — {', '.join(class_names)} |

## 2. Lancer le pipeline

```bash
python train_pipeline.py --data_root "{data_root}" --label {label}
```

### Arguments

| Argument | Description |
|----------|-------------|
| `--data_root` | Chemin absolu vers le dossier contenant les sous-dossiers `train_*` |
| `--label` | Nom court pour le nommage des fichiers de sortie (ex: `car`, `pedestrian`) |

## 3. Structure du projet

```
{data_root}/
├── train_1/
│   ├── *.png / *.jpg
│   └── _annotations.coco.json
├── train_2/
│   └── ...
├── train_3/
│   └── ...
└── ...

dataset_{label}/          ← Généré automatiquement
├── images/
│   ├── train/           ({counts['train']} images)
│   ├── val/             ({counts['val']} images)
│   └── test/            ({counts['test']} images)
├── labels/
│   ├── train/
│   ├── val/
│   └── test/
└── data.yaml

models/
└── best_{label}.pt       ← Modèle fine-tuné
```

## 4. Préparation des données

1. **Scan automatique** de tous les sous-dossiers `train_*` dans `--data_root`
2. **Fusion** de tous les JSON COCO en un dataset unique (réindexation des IDs)
3. **Conversion** COCO → YOLO (`classe cx cy w h` normalisés entre 0 et 1)
4. **Split** aléatoire (seed={SEED}) :
   - Train : {TRAIN_RATIO*100:.0f}% → **{counts['train']} images**
   - Val : {VAL_RATIO*100:.0f}% → **{counts['val']} images**
   - Test : {TEST_RATIO*100:.0f}% → **{counts['test']} images**
5. **Total annotations** : {total_labels}
6. **Classes** : {', '.join(class_names)}

## 5. Fine-tuning

| Hyperparamètre | Valeur |
|-----------------|--------|
| Modèle de base | `{BASE_MODEL}` |
| Epochs | {EPOCHS} |
| Image size | {IMGSZ} |
| Batch size | {BATCH} |
| Patience (early stopping) | {PATIENCE} |
| Optimizer | {OPTIMIZER} |
| Learning rate | {LR0} |
| Augmentation | mosaic=1.0, flipud=0.5, fliplr=0.5 |
| Seed | {SEED} |

## 6. MLflow

### Lancer l'interface

```bash
mlflow ui --backend-store-uri runs/mlflow --port 5000
```

Puis ouvrir [http://localhost:5000](http://localhost:5000) dans un navigateur.

### Ce qui est tracké

- **Paramètres** : data_root, label, hyperparamètres, info dataset
- **Métriques par epoch** : mAP50, mAP50-95, precision, recall, box_loss, cls_loss, dfl_loss
- **Métriques finales (test)** : mAP50, mAP50-95, precision, recall
- **Artefacts** : data.yaml, confusion matrix, courbes PR/P/R/F1, best_{label}.pt

| Champ | Valeur |
|-------|--------|
| Experiment | `{experiment_name}` |
| Run | `{run_name}` |

## 7. Résultats

| Métrique | Valeur |
|----------|--------|
| **mAP50** | {test_metrics.get('mAP50', 'N/A'):.4f} |
| **mAP50-95** | {test_metrics.get('mAP50-95', 'N/A'):.4f} |
| **Precision** | {test_metrics.get('precision', 'N/A'):.4f} |
| **Recall** | {test_metrics.get('recall', 'N/A'):.4f} |

## 8. Utilisation du modèle

```python
from ultralytics import YOLO

# Charger le modèle fine-tuné
model = YOLO("models/best_{label}.pt")

# Inférer sur une image
results = model("path/to/image.png")

# Afficher les résultats
for r in results:
    r.show()           # Affiche l'image annotée
    print(r.boxes)     # Bounding boxes
    print(r.boxes.cls) # Classes détectées
```

## 9. Reproductibilité

| Élément | Détail |
|---------|--------|
| Seed | {SEED} |
| Python | {sys.version.split()[0]} |
| Ultralytics | voir `pip show ultralytics` |
| MLflow | voir `pip show mlflow` |
| NumPy | {np.__version__} |
| scikit-learn | voir `pip show scikit-learn` |
| OS | {sys.platform} |
"""

    readme_path = project_root / f"README_{label}.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(md)

    log_info(f"README généré : {readme_path}")
    return readme_path


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    args = parse_args()
    data_root = Path(args.data_root).resolve()
    label = args.label
    project_root = Path(__file__).resolve().parent

    log_info("=" * 60)
    log_info("  Pipeline de fine-tuning YOLOv11")
    log_info("=" * 60)

    # ── Validation ──────────────────────────────────────────
    train_dirs = validate_inputs(data_root, label)

    # ── ÉTAPE 1 — Fusion & restructuration ──────────────────
    log_info("-" * 40)
    log_info("ÉTAPE 1 — Fusion et restructuration des données")
    class_mapping = parse_class_mapping(args.class_mapping)
    merged_coco = load_and_merge_coco(train_dirs, class_mapping)
    dataset_dir, counts, total_labels = build_yolo_dataset(
        merged_coco, data_root, label
    )

    # ── ÉTAPE 2 — data.yaml ────────────────────────────────
    log_info("-" * 40)
    log_info("ÉTAPE 2 — Création du data.yaml")
    data_yaml = create_data_yaml(dataset_dir, merged_coco["categories"])

    # ── ÉTAPE 3 — Fine-tuning ──────────────────────────────
    log_info("-" * 40)
    log_info("ÉTAPE 3 — Fine-tuning YOLO v11")
    model, train_results, best_pt, best_model_dest = train_yolo(
        data_yaml, label, project_root
    )
    train_save_dir = Path(train_results.save_dir)

    # ── ÉTAPE 5 — Évaluation test ──────────────────────────
    log_info("-" * 40)
    log_info("ÉTAPE 5 — Évaluation sur le jeu de test")
    test_metrics = evaluate_test(best_model_dest, data_yaml)

    # ── ÉTAPE 4 — MLflow tracking ──────────────────────────
    log_info("-" * 40)
    log_info("ÉTAPE 4 — Tracking MLflow")
    experiment_name, run_name = setup_mlflow(
        label=label,
        data_root=str(data_root),
        data_yaml=data_yaml,
        merged_coco=merged_coco,
        counts=counts,
        total_labels=total_labels,
        train_results=train_results,
        test_metrics=test_metrics,
        best_model_dest=best_model_dest,
        train_save_dir=train_save_dir,
    )

    # ── ÉTAPE 6 — README ──────────────────────────────────
    log_info("-" * 40)
    log_info("ÉTAPE 6 — Génération du README")
    generate_readme(
        label=label,
        data_root=str(data_root),
        dataset_dir=dataset_dir,
        merged_coco=merged_coco,
        counts=counts,
        total_labels=total_labels,
        test_metrics=test_metrics,
        experiment_name=experiment_name,
        run_name=run_name,
        project_root=project_root,
    )

    # ── Résumé final ───────────────────────────────────────
    log_info("=" * 60)
    log_info("  Pipeline terminé avec succès !")
    log_info("=" * 60)
    log_info(f"  Dataset   : {dataset_dir}")
    log_info(f"  data.yaml : {data_yaml}")
    log_info(f"  Modèle    : {best_model_dest}")
    log_info(f"  README    : {project_root / f'README_{label}.md'}")
    log_info(f"  MLflow    : mlflow ui --backend-store-uri runs/mlflow --port 5000  (experiment: {experiment_name})")


if __name__ == "__main__":
    main()
