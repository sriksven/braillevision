#!/usr/bin/env python3
"""Convert Angelina labelImg annotations to YOLO format and prepare training dataset."""

import json
import os
from pathlib import Path
from shutil import copy2
import random

# Paths
ANGELINA_DIR = Path("data/training/angelina")
ROBOFLOW_DIR = Path("data/training/roboflow_v2")
YOLO_DIR = Path("data/yolo_training")

# YOLO subdirectories
YOLO_IMAGES_DIR = YOLO_DIR / "images"
YOLO_LABELS_DIR = YOLO_DIR / "labels"

def setup_yolo_structure():
    """Create YOLO directory structure."""
    for split in ["train", "val", "test"]:
        (YOLO_IMAGES_DIR / split).mkdir(parents=True, exist_ok=True)
        (YOLO_LABELS_DIR / split).mkdir(parents=True, exist_ok=True)
    print(f"✅ Created YOLO directory structure at {YOLO_DIR}")

def convert_labelimg_to_yolo(json_path, img_width, img_height):
    """Convert labelImg JSON to YOLO format annotations.

    Returns list of YOLO annotation strings (one per line).
    YOLO format: class_id center_x center_y width height (all normalized 0-1)
    We use class_id=0 for all Braille dots (character-agnostic detection).
    """
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to parse {json_path}: {e}")
        return []

    annotations = []
    shapes = data.get("shapes", [])

    for shape in shapes:
        if shape.get("shape_type") != "rectangle":
            continue

        points = shape.get("points", [])
        if len(points) < 2:
            continue

        # Get bounding box corners
        x1, y1 = points[0]
        x2, y2 = points[1]

        # Normalize to [0, 1]
        x_min = min(x1, x2) / img_width
        x_max = max(x1, x2) / img_width
        y_min = min(y1, y2) / img_height
        y_max = max(y1, y2) / img_height

        # Convert to center format
        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2
        width = x_max - x_min
        height = y_max - y_min

        # Skip degenerate boxes
        if width <= 0 or height <= 0:
            continue

        # YOLO format: class_id=0 (Braille dot detection is class-agnostic)
        annotations.append(f"0 {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")

    return annotations

def process_angelina():
    """Convert Angelina dataset to YOLO format."""
    print("\n📂 Processing Angelina dataset...")

    image_count = 0
    annotation_count = 0

    for img_path in sorted(ANGELINA_DIR.rglob("*.labeled.jpg")) + sorted(ANGELINA_DIR.rglob("*.labeled.png")):
        # Skip git directory
        if ".git" in img_path.parts:
            continue

        # Find corresponding JSON annotation (replace .jpg/.png with .json)
        json_path = img_path.parent / (img_path.stem + ".json")
        if not json_path.exists():
            continue

        try:
            # Read image dimensions from JSON
            with open(json_path) as f:
                data = json.load(f)
            img_width = data.get("imageWidth", 1024)
            img_height = data.get("imageHeight", 1024)
        except:
            print(f"⚠️ Skipping {img_path.name} (can't read annotation)")
            continue

        # Convert annotations
        yolo_annotations = convert_labelimg_to_yolo(json_path, img_width, img_height)
        if not yolo_annotations:
            continue

        # Copy image to YOLO structure
        unique_name = f"angelina_{image_count:04d}"
        target_img = YOLO_IMAGES_DIR / "all" / f"{unique_name}{img_path.suffix}"
        target_img.parent.mkdir(parents=True, exist_ok=True)

        copy2(img_path, target_img)

        # Write YOLO labels
        target_label = YOLO_LABELS_DIR / "all" / f"{unique_name}.txt"
        target_label.parent.mkdir(parents=True, exist_ok=True)
        with open(target_label, 'w') as f:
            f.writelines(yolo_annotations)

        image_count += 1
        annotation_count += len(yolo_annotations)

    print(f"   ✅ Converted {image_count} images with {annotation_count} total annotations")
    return image_count

def process_roboflow():
    """Check for Roboflow dataset (manual download required)."""
    print("\n📂 Checking Roboflow dataset...")

    if not ROBOFLOW_DIR.exists() or not list(ROBOFLOW_DIR.glob("*")):
        print("   ⚠️ Roboflow dataset not found (manual download required)")
        print("   Instructions: Download from Roboflow, extract to data/training/roboflow_v2/")
        return 0

    # Count images if they exist
    images = list(ROBOFLOW_DIR.rglob("*.jpg")) + list(ROBOFLOW_DIR.rglob("*.png"))
    print(f"   ℹ️ Found {len(images)} images in Roboflow directory")
    return len(images)

def create_train_val_test_split(total_images, train_ratio=0.7, val_ratio=0.15):
    """Create train/val/test splits."""
    print(f"\n📊 Creating train/val/test splits...")

    # List all images and labels
    all_images = sorted(list((YOLO_IMAGES_DIR / "all").glob("*")))

    if not all_images:
        print("   ⚠️ No images found to split")
        return

    # Shuffle
    random.seed(42)
    random.shuffle(all_images)

    # Calculate split sizes
    n = len(all_images)
    train_count = int(n * train_ratio)
    val_count = int(n * val_ratio)
    test_count = n - train_count - val_count

    # Split
    train_images = all_images[:train_count]
    val_images = all_images[train_count:train_count + val_count]
    test_images = all_images[train_count + val_count:]

    # Move files
    for split, images in [("train", train_images), ("val", val_images), ("test", test_images)]:
        for img_path in images:
            label_path = YOLO_LABELS_DIR / "all" / img_path.stem
            label_path = label_path.with_suffix(".txt")

            # Copy image and label
            copy2(img_path, YOLO_IMAGES_DIR / split / img_path.name)
            if label_path.exists():
                copy2(label_path, YOLO_LABELS_DIR / split / label_path.name)

    print(f"   ✅ Train: {len(train_images)}, Val: {len(val_images)}, Test: {len(test_images)}")

def create_dataset_yaml():
    """Create dataset.yaml for YOLOv8 training."""
    yaml_content = """path: data/yolo_training
train: images/train
val: images/val
test: images/test

nc: 1
names: ['dot']
"""

    yaml_path = YOLO_DIR / "dataset.yaml"
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)

    print(f"\n📝 Created {yaml_path}")

def main():
    print("🚀 Converting datasets to YOLO format...\n")

    setup_yolo_structure()

    # Create temporary "all" directories
    (YOLO_IMAGES_DIR / "all").mkdir(parents=True, exist_ok=True)
    (YOLO_LABELS_DIR / "all").mkdir(parents=True, exist_ok=True)

    angelina_count = process_angelina()
    roboflow_count = process_roboflow()
    total = angelina_count + roboflow_count

    if total == 0:
        print("\n❌ No images processed. Check your datasets.")
        return

    create_train_val_test_split(total)
    create_dataset_yaml()

    # Cleanup temporary directories
    import shutil
    if (YOLO_IMAGES_DIR / "all").exists():
        shutil.rmtree(YOLO_IMAGES_DIR / "all")
    if (YOLO_LABELS_DIR / "all").exists():
        shutil.rmtree(YOLO_LABELS_DIR / "all")

    print(f"\n✅ Training data ready at {YOLO_DIR}")
    print(f"   Total images: {total}")
    print(f"   Run: yolo detect train model=yolov8n.pt data={YOLO_DIR}/dataset.yaml epochs=50")

if __name__ == "__main__":
    main()
