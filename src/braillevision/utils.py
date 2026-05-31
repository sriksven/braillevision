"""Small image and annotation utilities."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from braillevision.segmentation import BrailleCell

try:  # pragma: no cover
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


def load_image(path: str | Path) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img)
    if cv2 is not None:
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    return arr.copy()


def resize_max_width(frame: np.ndarray, max_width: int) -> np.ndarray:
    if frame.shape[1] <= max_width:
        return frame
    ratio = max_width / frame.shape[1]
    size = (max_width, int(frame.shape[0] * ratio))
    if cv2 is not None:
        return cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
    img = Image.fromarray(frame)
    return np.asarray(img.resize(size, Image.Resampling.LANCZOS))


def annotate_cells(frame: np.ndarray, cells: list[BrailleCell]) -> np.ndarray:
    img = np.asarray(frame).copy()
    if img.ndim == 2:
        img = np.stack([img, img, img], axis=2)
    pil = Image.fromarray(img.astype(np.uint8)).convert("RGB")
    draw = ImageDraw.Draw(pil)
    for cell in cells:
        x = int(round(cell.center_x))
        y = int(round(cell.center_y))
        draw.rectangle(
            (x - 28, y - 34, x + 28, y + 34), outline=(30, 110, 201), width=2
        )
        draw.text((x - 24, y - 50), f"{cell.row}:{cell.col}", fill=(30, 110, 201))
    return np.asarray(pil)


def encode_jpeg(frame: np.ndarray) -> bytes:
    arr = np.asarray(frame)
    if cv2 is not None:
        ok, encoded = cv2.imencode(".jpg", arr)
        if ok:
            return encoded.tobytes()
    img = Image.fromarray(arr.astype(np.uint8)).convert("RGB")
    out = BytesIO()
    img.save(out, format="JPEG", quality=88)
    return out.getvalue()


def image_to_data_url(frame: np.ndarray) -> str:
    encoded = base64.b64encode(encode_jpeg(frame)).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"
