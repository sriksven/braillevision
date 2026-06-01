"""Pipeline B: Roboflow pretrained YOLOv8 via hosted inference API."""

import base64
import time
from dataclasses import dataclass

import cv2
import numpy as np

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
import os



ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
ROBOFLOW_MODEL = "braille-detection-v2-xpwue"
ROBOFLOW_VERSION = 1


def _roboflow_url() -> str:
    key = ROBOFLOW_API_KEY or os.getenv("ROBOFLOW_API_KEY", "")
    return (
        f"https://detect.roboflow.com/{ROBOFLOW_MODEL}/{ROBOFLOW_VERSION}"
        f"?api_key={key}&confidence=30&overlap=30"
    )


@dataclass
class RoboflowResult:
    text: str
    confidence: float
    latency_ms: int
    dot_count: int
    cell_count: int
    error: str | None = None


def run_roboflow_pipeline(frame: np.ndarray) -> RoboflowResult:
    """
    Send frame to Roboflow hosted inference API.
    Returns dot detections -> segments -> recognizes text.
    """
    if not REQUESTS_AVAILABLE:
        return RoboflowResult(
            text="",
            confidence=0.0,
            latency_ms=0,
            dot_count=0,
            cell_count=0,
            error="requests not installed",
        )

    start = time.time()
    try:
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")

        response = requests.post(
            _roboflow_url(),
            data=b64,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = int((time.time() - start) * 1000)
        predictions = data.get("predictions", [])

        # YOLO predicts full characters, not individual dots.
        # Sort predictions left-to-right by x coordinate
        predictions.sort(key=lambda p: p["x"])
        
        # Extract class labels and concatenate
        characters = [p.get("class", "").lower() for p in predictions]
        text = "".join(characters)

        avg_conf = (
            sum(p["confidence"] for p in predictions) / len(predictions)
            if predictions
            else 0.1
        )

        return RoboflowResult(
            text=text,
            confidence=avg_conf,
            latency_ms=latency_ms,
            dot_count=0,
            cell_count=len(predictions),
        )

    except Exception as exc:
        return RoboflowResult(
            text="",
            confidence=0.0,
            latency_ms=int((time.time() - start) * 1000),
            dot_count=0,
            cell_count=0,
            error=str(exc),
        )
