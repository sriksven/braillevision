"""Pipeline D: Our finetuned YOLOv8 model (local inference)."""

import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

try:
    from ultralytics import YOLO

    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

from .preprocessing import preprocess

MODEL_PATH = Path("models/braille_finetuned.pt")
FALLBACK_PATH = Path("models/yolov8n.pt")

_model = None


@dataclass
class FinetunedResult:
    text: str
    confidence: float
    latency_ms: int
    dot_count: int
    cell_count: int
    model_path: str
    error: str | None = None


def _get_model():
    """Load finetuned model or fall back to base YOLOv8n."""
    global _model
    if _model is not None:
        return _model
    if not YOLO_AVAILABLE:
        return None

    if MODEL_PATH.exists():
        try:
            _model = YOLO(str(MODEL_PATH))
            print(f"[OK] Loaded finetuned model: {MODEL_PATH}")
        except Exception as e:
            print(f"[WARN] Could not load finetuned model: {e}, using fallback")
            _model = YOLO("yolov8n.pt")
    else:
        _model = YOLO("yolov8n.pt")
        print("Using base YOLOv8n (finetuned model not found yet)")
    return _model


def run_finetuned_pipeline(frame: np.ndarray) -> FinetunedResult:
    """
    Run local YOLOv8 model (finetuned or base).
    Falls back to yolov8n if finetuned weights not found.
    """
    if not YOLO_AVAILABLE:
        return FinetunedResult(
            text="",
            confidence=0.0,
            latency_ms=0,
            dot_count=0,
            cell_count=0,
            model_path="none",
            error="ultralytics not installed",
        )

    start = time.time()
    model = _get_model()
    if model is None:
        return FinetunedResult(
            text="",
            confidence=0.0,
            latency_ms=0,
            dot_count=0,
            cell_count=0,
            model_path="none",
            error="Could not load model",
        )

    try:
        processed = preprocess(frame)
        if processed.ndim == 2:
            processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)

        results = model(processed, verbose=False, conf=0.30, iou=0.45)
        boxes = results[0].boxes if results else []

        # YOLO predicts full characters, not individual dots.
        detections = []
        for box in boxes:
            x1 = box.xyxy[0][0].item()
            class_id = int(box.cls[0].item())
            class_name = model.names[class_id]
            conf = float(box.conf[0].item())
            detections.append({"x": x1, "class": class_name, "conf": conf})

        # Sort predictions left-to-right by x coordinate
        detections.sort(key=lambda d: d["x"])
        
        characters = [d["class"].lower() for d in detections]
        text = "".join(characters)

        latency_ms = int((time.time() - start) * 1000)
        confidence = sum(d["conf"] for d in detections) / len(detections) if detections else 0.1

        return FinetunedResult(
            text=text,
            confidence=confidence,
            latency_ms=latency_ms,
            dot_count=0,
            cell_count=len(detections),
            model_path=str(MODEL_PATH if MODEL_PATH.exists() else "base"),
        )

    except Exception as exc:
        return FinetunedResult(
            text="",
            confidence=0.0,
            latency_ms=int((time.time() - start) * 1000),
            dot_count=0,
            cell_count=0,
            model_path=str(MODEL_PATH),
            error=str(exc),
        )
