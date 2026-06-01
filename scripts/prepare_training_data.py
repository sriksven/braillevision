#!/usr/bin/env python3
"""Download Angelina Braille dataset from GitHub and prepare for YOLOv8 training."""

import subprocess
from pathlib import Path

DATA_DIR = Path("data/training")
DATA_DIR.mkdir(parents=True, exist_ok=True)

print("Downloading Angelina Braille Dataset (ICCV 2021)...")
print("   Source: https://github.com/IlyaOvodov/AngelinaDataset")

# Clone the Angelina dataset
angelina_dir = DATA_DIR / "angelina"
if angelina_dir.exists():
    print(f"   [OK] Already exists at {angelina_dir}")
else:
    cmd = f"git clone https://github.com/IlyaOvodov/AngelinaDataset {angelina_dir}"
    print(f"   Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   [OK] Downloaded to {angelina_dir}")
    else:
        print(f"   [ERROR] Error: {result.stderr}")

# Check what's in the dataset
if angelina_dir.exists():
    print("\nAngelina Dataset Structure:")
    for item in angelina_dir.iterdir():
        if item.is_dir():
            file_count = len(list(item.glob("*")))
            print(f"   {item.name}/ ({file_count} items)")
        else:
            print(f"   {item.name}")

# Also create placeholder for Roboflow data
roboflow_dir = DATA_DIR / "roboflow_v2"
roboflow_dir.mkdir(exist_ok=True)
print(f"\nCreated directory for Roboflow: {roboflow_dir}")
print("   (Awaiting manual download due to API access constraints)")

# Summary
print(f"\n[OK] Training data directory ready: {DATA_DIR}")
print(
    f"   - Angelina: {(angelina_dir / 'dataset').exists() and 'ready' or 'needs setup'}"
)
print("   - Roboflow: ready for manual upload")
