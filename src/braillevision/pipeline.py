"""End-to-end BrailleVision pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from braillevision.config import PipelineConfig
from braillevision.detection import annotate_dots, detect_dots, filter_noise_keypoints
from braillevision.preprocessing import preprocess, to_gray
from braillevision.recognition import cells_to_text
from braillevision.segmentation import (
    BrailleCell,
    cluster_dots_to_cells,
    estimate_dot_spacing,
)
from braillevision.utils import annotate_cells, resize_max_width


@dataclass
class PipelineResult:
    text: str
    dot_count: int
    cell_count: int
    dot_spacing: float
    annotated_frame: np.ndarray
    confidence: float
    cells: list[BrailleCell]


def _empty_result(frame: np.ndarray) -> PipelineResult:
    return PipelineResult(
        text="",
        dot_count=0,
        cell_count=0,
        dot_spacing=0.0,
        annotated_frame=np.asarray(frame).copy(),
        confidence=0.0,
        cells=[],
    )


def _confidence(text: str, cell_count: int) -> float:
    if cell_count == 0:
        return 0.0
    unknown = text.count("?")
    decoded = max(cell_count - unknown, 0)
    return round(decoded / cell_count, 3)


def run_pipeline(
    frame: np.ndarray, cfg: PipelineConfig | None = None, grade2: bool = False
) -> PipelineResult:
    """Run preprocessing, dot detection, segmentation, and recognition."""

    cfg = cfg or PipelineConfig()
    try:
        source = resize_max_width(np.asarray(frame), cfg.max_frame_width)
        processed = preprocess(source, cfg)
        dots = detect_dots(processed, cfg)
        spacing = estimate_dot_spacing(dots, cfg) if dots else 0.0
        filtered = filter_noise_keypoints(
            dots, radius=spacing * cfg.noise_radius_multiplier if spacing else None
        )
        cells = cluster_dots_to_cells(filtered, cfg)
        text = cells_to_text(cells, grade2=grade2)
        annotated = annotate_cells(annotate_dots(to_gray(source), filtered), cells)
        return PipelineResult(
            text=text,
            dot_count=len(filtered),
            cell_count=len(cells),
            dot_spacing=round(float(spacing), 2),
            annotated_frame=annotated,
            confidence=_confidence(text, len(cells)),
            cells=cells,
        )
    except Exception:
        return _empty_result(frame)
