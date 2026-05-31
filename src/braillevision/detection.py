"""Braille dot detection."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from braillevision.config import PipelineConfig
from braillevision.preprocessing import to_gray

try:  # pragma: no cover - exercised when OpenCV is installed.
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


@dataclass(frozen=True)
class Dot:
    x: float
    y: float
    size: float = 1.0

    @property
    def pt(self) -> tuple[float, float]:
        return (self.x, self.y)


def _build_detector(cfg: PipelineConfig | None = None):
    """Create a configured OpenCV SimpleBlobDetector."""

    if cv2 is None:
        return None
    cfg = cfg or PipelineConfig()
    params = cv2.SimpleBlobDetector_Params()
    params.minThreshold = 0
    params.maxThreshold = 255
    params.thresholdStep = cfg.blob_threshold_step
    params.filterByArea = True
    params.minArea = cfg.blob_min_area
    params.maxArea = cfg.blob_max_area
    params.filterByCircularity = True
    params.minCircularity = cfg.blob_min_circularity
    params.filterByConvexity = False
    params.filterByInertia = False
    params.filterByColor = True
    params.blobColor = 0
    return cv2.SimpleBlobDetector_create(params)


def _connected_components(mask: np.ndarray, cfg: PipelineConfig) -> list[Dot]:
    seen = np.zeros(mask.shape, dtype=bool)
    dots: list[Dot] = []
    height, width = mask.shape

    for start_y, start_x in np.argwhere(mask):
        if seen[start_y, start_x]:
            continue
        q: deque[tuple[int, int]] = deque([(int(start_y), int(start_x))])
        seen[start_y, start_x] = True
        pixels: list[tuple[int, int]] = []
        while q:
            y, x = q.popleft()
            pixels.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and mask[ny, nx]
                        and not seen[ny, nx]
                    ):
                        seen[ny, nx] = True
                        q.append((ny, nx))

        area = len(pixels)
        if cfg.blob_min_area <= area <= cfg.blob_max_area:
            arr = np.asarray(pixels, dtype=np.float32)
            ys = arr[:, 0]
            xs = arr[:, 1]
            dots.append(Dot(float(xs.mean()), float(ys.mean()), float(np.sqrt(area))))
    return dots


def _detect_with_threshold(gray: np.ndarray, cfg: PipelineConfig) -> list[Dot]:
    if gray.size == 0 or float(gray.max()) == float(gray.min()):
        return []
    threshold = np.percentile(gray, 35)
    dark_mask = gray < threshold
    light_mask = gray > np.percentile(gray, 65)
    dark = _connected_components(dark_mask, cfg)
    light = _connected_components(light_mask, cfg)
    return dark if len(dark) >= len(light) else light


def detect_dots(frame: np.ndarray, cfg: PipelineConfig | None = None) -> list[Dot]:
    """Detect Braille dots, trying both dark-on-light and light-on-dark input."""

    cfg = cfg or PipelineConfig()
    gray = to_gray(frame)
    if cv2 is not None:
        detector = _build_detector(cfg)
        keypoints = detector.detect(gray)
        inverted = cv2.bitwise_not(gray)
        inv_keypoints = detector.detect(inverted)
        chosen = keypoints if len(keypoints) >= len(inv_keypoints) else inv_keypoints
        return [Dot(float(kp.pt[0]), float(kp.pt[1]), float(kp.size)) for kp in chosen]
    return _detect_with_threshold(gray, cfg)


def filter_noise_keypoints(dots: list[Dot], radius: float | None = None) -> list[Dot]:
    """Remove dots that are far from the median cluster center."""

    if len(dots) < 3:
        return list(dots)
    pts = np.asarray([(dot.x, dot.y) for dot in dots], dtype=np.float32)
    center = np.median(pts, axis=0)
    distances = np.linalg.norm(pts - center, axis=1)
    if radius is None:
        radius = float(np.median(distances) + 3.0 * np.std(distances))
    return [dot for dot, distance in zip(dots, distances) if distance <= radius]


def annotate_dots(frame: np.ndarray, dots: list[Dot]) -> np.ndarray:
    """Draw green circles around detected dots."""

    img = np.asarray(frame).copy()
    if img.ndim == 2:
        img = np.stack([img, img, img], axis=2)
    if cv2 is not None:
        for dot in dots:
            cv2.circle(
                img,
                (int(round(dot.x)), int(round(dot.y))),
                max(5, int(dot.size)),
                (0, 220, 80),
                2,
            )
        return img

    for dot in dots:
        x0, y0 = int(round(dot.x)), int(round(dot.y))
        radius = max(4, int(round(dot.size)))
        yy, xx = np.ogrid[: img.shape[0], : img.shape[1]]
        ring = np.abs((xx - x0) ** 2 + (yy - y0) ** 2 - radius**2) <= max(2, radius)
        img[ring] = np.array([0, 220, 80], dtype=img.dtype)
    return img
