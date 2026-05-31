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

from .detection import Dot, filter_noise_keypoints
from .segmentation import cluster_dots_to_cells
from .recognition import cells_to_text

ROBOFLOW_API_KEY = "lMDrLJtK2dRsHPmUfsj4"
ROBOFLOW_MODEL = "braille-detection-v2-xpwue"
ROBOFLOW_VERSION = 1
ROBOFLOW_URL = (
    f"https://detect.roboflow.com/{ROBOFLOW_MODEL}/{ROBOFLOW_VERSION}"
    f"?api_key={ROBOFLOW_API_KEY}&confidence=30&overlap=30"
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
    Returns dot detections → segments → recognizes text.
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
            ROBOFLOW_URL,
            data=b64,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = int((time.time() - start) * 1000)
        predictions = data.get("predictions", [])

        # Convert predictions to Dot objects
        dots = []
        for pred in predictions:
            cx = pred["x"]
            cy = pred["y"]
            size = max(pred["width"], pred["height"]) / 2
            dots.append(Dot(float(cx), float(cy), float(size)))

        filtered = filter_noise_keypoints(dots)
        cells = cluster_dots_to_cells(filtered)
        text = cells_to_text(cells)

        avg_conf = (
            sum(p["confidence"] for p in predictions) / len(predictions)
            if predictions
            else 0.0
        )

        return RoboflowResult(
            text=text,
            confidence=avg_conf if cells else 0.1,
            latency_ms=latency_ms,
            dot_count=len(filtered),
            cell_count=len(cells),
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
