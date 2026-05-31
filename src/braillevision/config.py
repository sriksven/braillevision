"""Tunable constants for the BrailleVision pipeline."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineConfig:
    clahe_clip_limit: float = 3.0
    clahe_tile_grid_size: tuple[int, int] = (8, 8)
    blob_min_area: int = 35
    blob_max_area: int = 3000
    blob_min_circularity: float = 0.58
    blob_threshold_step: int = 10
    noise_radius_multiplier: float = 18.0
    min_dot_spacing: float = 8.0
    max_dot_spacing: float = 60.0
    cell_gap_multiplier: float = 1.75
    row_gap_multiplier: float = 3.2
    max_frame_width: int = 960
