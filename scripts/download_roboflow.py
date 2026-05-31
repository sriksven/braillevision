#!/usr/bin/env python3
"""Download Roboflow Braille Detection V2 dataset."""

import os
import shutil
from pathlib import Path

try:
    from roboflow import Roboflow
except ImportError:
    print("⚠️ roboflow not installed, installing...")
    os.system("pip install roboflow -q")
    from roboflow import Roboflow

# Roboflow credentials
API_KEY = "lMDrLJtK2dRsHPmUfsj4"
WORKSPACE = "braille-detection"
PROJECT = "braille-detection-v2"
VERSION = 2

print("📥 Downloading Roboflow Braille Detection V2...")
print(f"   Workspace: {WORKSPACE}")
print(f"   Project: {PROJECT}")
print(f"   Version: {VERSION}")

rf = Roboflow(api_key=API_KEY)
project = rf.workspace(WORKSPACE).project(PROJECT)
dataset = project.version(VERSION).download("yolov8")

print(f"✅ Downloaded to: {dataset.location}")
print(f"   Contents: {os.listdir(dataset.location)}")

# Show dataset structure
for root, dirs, files in os.walk(dataset.location):
    level = root.replace(dataset.location, "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    sub_indent = " " * 2 * (level + 1)
    for file in files[:3]:  # Show first 3 files
        print(f"{sub_indent}{file}")
    if len(files) > 3:
        print(f"{sub_indent}... and {len(files) - 3} more files")
