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

from .detection import Dot, filter_noise_keypoints
from .preprocessing import preprocess
from .segmentation import cluster_dots_to_cells
from .recognition import cells_to_text

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
            print(f"✅ Loaded finetuned model: {MODEL_PATH}")
        except Exception as e:
            print(f"⚠️ Could not load finetuned model: {e}, using fallback")
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

        dots = []
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            size = min(x2 - x1, y2 - y1) / 2
            dots.append(Dot(float(cx), float(cy), float(size)))

        filtered = filter_noise_keypoints(dots)
        cells = cluster_dots_to_cells(filtered)
        text = cells_to_text(cells)

        latency_ms = int((time.time() - start) * 1000)
        confidence = 0.75 if len(filtered) > 3 else 0.1

        return FinetunedResult(
            text=text,
            confidence=confidence,
            latency_ms=latency_ms,
            dot_count=len(filtered),
            cell_count=len(cells),
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
