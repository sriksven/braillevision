#!/usr/bin/env python3
"""Train YOLOv8 model on Braille detection dataset."""

from pathlib import Path

import torch
from ultralytics import YOLO


def check_gpu():
    """Check GPU availability."""
    if torch.cuda.is_available():
        print(f"[OK] GPU available (CUDA): {torch.cuda.get_device_name(0)}")
        return "0"  # CUDA device 0
    elif torch.backends.mps.is_available():
        print("[OK] GPU available (Apple Metal - MPS)")
        # MPS not directly supported by ultralytics, use CPU fallback
        # or use mps string if supported
        return "cpu"  # Fallback to CPU for compatibility
    else:
        print("[WARN] No GPU detected, using CPU")
        return "cpu"


def train_yolo():
    """Train YOLOv8 model."""
    dataset_yaml = "data/yolo_training/dataset.yaml"
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    # Check if dataset exists
    if not Path(dataset_yaml).exists():
        print(f"[ERROR] Dataset config not found: {dataset_yaml}")
        print("Run: python scripts/convert_to_yolo.py")
        return

    print("[START] Starting YOLOv8 training...\n")
    print(f"Dataset: {dataset_yaml}")
    print("Output: models/braille_finetuned.pt\n")

    device = check_gpu()

    # Load base model (nano = fastest)
    print("\nLoading YOLOv8n base model...")
    model = YOLO("yolov8n.pt")

    # Training parameters
    epochs = 50
    imgsz = 640
    # Batch size - smaller for local training
    batch_size = 16 if device == "cpu" else 32

    print("\nTraining configuration:")
    print("   Model: YOLOv8n (nano)")
    print(f"   Epochs: {epochs}")
    print(f"   Image size: {imgsz}")
    print(f"   Batch size: {batch_size}")
    print(f"   Device: {device}")
    print("   Classes: 1 (Braille dot)")

    # Train
    results = model.train(
        data=dataset_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch_size,
        device=device,
        patience=10,  # Early stopping after 10 epochs without improvement
        project="models",
        name="braille_training",
        exist_ok=True,
        save=True,
        verbose=True,
    )

    # Copy best weights to standard location
    best_model = Path("models/braille_training/weights/best.pt")
    if best_model.exists():
        import shutil

        shutil.copy(best_model, models_dir / "braille_finetuned.pt")
        print("\n[OK] Model saved to: models/braille_finetuned.pt")
        print(f"   Metrics: {results.box.map}")
    else:
        print(f"\n[WARN] Best model not found at {best_model}")


if __name__ == "__main__":
    train_yolo()
