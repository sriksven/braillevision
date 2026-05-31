"""Image preprocessing helpers."""

from __future__ import annotations

import numpy as np

from braillevision.config import PipelineConfig

try:  # pragma: no cover - exercised when OpenCV is installed.
    import cv2
except Exception:  # pragma: no cover - the fallback is covered in this env.
    cv2 = None


def to_gray(frame: np.ndarray) -> np.ndarray:
    """Return a grayscale uint8 image from BGR/RGB or already-gray input."""

    if frame is None:
        raise ValueError("frame cannot be None")
    arr = np.asarray(frame)
    if arr.ndim == 2:
        gray = arr
    elif arr.ndim == 3 and arr.shape[2] >= 3:
        if cv2 is not None:
            gray = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_BGR2GRAY)
        else:
            gray = np.dot(arr[:, :, :3], [0.114, 0.587, 0.299])
    else:
        raise ValueError(f"unsupported frame shape: {arr.shape}")
    return np.clip(gray, 0, 255).astype(np.uint8)


def enhance_contrast(gray: np.ndarray, cfg: PipelineConfig | None = None) -> np.ndarray:
    """Apply CLAHE when available, otherwise use percentile normalization."""

    cfg = cfg or PipelineConfig()
    gray = to_gray(gray)
    if cv2 is not None:
        clahe = cv2.createCLAHE(
            clipLimit=cfg.clahe_clip_limit,
            tileGridSize=cfg.clahe_tile_grid_size,
        )
        return clahe.apply(gray)

    lo, hi = np.percentile(gray, [2, 98])
    if hi <= lo:
        return gray.copy()
    stretched = (gray.astype(np.float32) - lo) * (255.0 / (hi - lo))
    return np.clip(stretched, 0, 255).astype(np.uint8)


def correct_perspective(frame: np.ndarray) -> np.ndarray:
    """Find a page-like quadrilateral and warp it; fall back to original."""

    if cv2 is None:
        return np.asarray(frame).copy()

    img = np.asarray(frame)
    gray = to_gray(img)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return img.copy()

    contour = max(contours, key=cv2.contourArea)
    peri = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
    if len(approx) != 4:
        return img.copy()

    pts = approx.reshape(4, 2).astype(np.float32)
    sums = pts.sum(axis=1)
    diffs = np.diff(pts, axis=1).ravel()
    rect = np.array(
        [
            pts[np.argmin(sums)],
            pts[np.argmin(diffs)],
            pts[np.argmax(sums)],
            pts[np.argmax(diffs)],
        ],
        dtype=np.float32,
    )
    width = int(
        max(np.linalg.norm(rect[2] - rect[3]), np.linalg.norm(rect[1] - rect[0]))
    )
    height = int(
        max(np.linalg.norm(rect[1] - rect[2]), np.linalg.norm(rect[0] - rect[3]))
    )
    if width < 20 or height < 20:
        return img.copy()
    dst = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(img, matrix, (width, height))


def preprocess(frame: np.ndarray, cfg: PipelineConfig | None = None) -> np.ndarray:
    """Run perspective correction, grayscale conversion, and contrast enhancement."""

    cfg = cfg or PipelineConfig()
    flattened = correct_perspective(frame)
    return enhance_contrast(to_gray(flattened), cfg)
