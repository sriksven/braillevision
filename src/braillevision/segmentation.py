"""Group detected dots into Braille cells."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from braillevision.config import PipelineConfig
from braillevision.detection import Dot


@dataclass(frozen=True)
class BrailleCell:
    row: int
    col: int
    pattern: tuple[int, int, int, int, int, int]
    center_x: float
    center_y: float


def _as_points(dots: list[Dot] | np.ndarray) -> np.ndarray:
    if isinstance(dots, np.ndarray):
        arr = dots.astype(np.float32)
        return arr.reshape((-1, 2)) if arr.size else np.empty((0, 2), dtype=np.float32)
    return np.asarray([(dot.x, dot.y) for dot in dots], dtype=np.float32)


def estimate_dot_spacing(
    dots: list[Dot] | np.ndarray, cfg: PipelineConfig | None = None
) -> float:
    """Estimate within-cell dot spacing from nearest-neighbor distances."""

    cfg = cfg or PipelineConfig()
    pts = _as_points(dots)
    if len(pts) < 2:
        return cfg.min_dot_spacing
    diff = pts[:, None, :] - pts[None, :, :]
    distances = np.linalg.norm(diff, axis=2)
    distances[distances == 0] = np.inf
    nearest = distances.min(axis=1)
    valid = nearest[(nearest >= cfg.min_dot_spacing) & (nearest <= cfg.max_dot_spacing)]
    if len(valid) == 0:
        return cfg.min_dot_spacing
    return float(np.percentile(valid, 25))


def _cluster_axis(values: np.ndarray, gap: float) -> list[float]:
    if len(values) == 0:
        return []
    ordered = np.sort(values)
    groups: list[list[float]] = [[float(ordered[0])]]
    for value in ordered[1:]:
        if float(value) - groups[-1][-1] > gap:
            groups.append([float(value)])
        else:
            groups[-1].append(float(value))
    return [float(np.mean(group)) for group in groups]


def _nearest_index(value: float, centers: list[float]) -> int:
    return int(np.argmin([abs(value - center) for center in centers]))


def cluster_dots_to_cells(
    dots: list[Dot] | np.ndarray, cfg: PipelineConfig | None = None
) -> list[BrailleCell]:
    """Assign dots to Braille cells and map each dot to positions 1-6."""

    cfg = cfg or PipelineConfig()
    pts = _as_points(dots)
    if len(pts) == 0:
        return []

    spacing = max(estimate_dot_spacing(pts, cfg), cfg.min_dot_spacing)
    x_cols = _cluster_axis(pts[:, 0], spacing * 0.8)
    y_rows = _cluster_axis(pts[:, 1], spacing * cfg.row_gap_multiplier)
    if not x_cols or not y_rows:
        return []

    x_cols = sorted(x_cols)
    cell_column_groups: list[list[float]] = [[x_cols[0]]]
    for center in x_cols[1:]:
        if center - cell_column_groups[-1][-1] > spacing * cfg.cell_gap_multiplier:
            cell_column_groups.append([center])
        else:
            cell_column_groups[-1].append(center)

    cells_by_key: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for x, y in pts:
        x_col = _nearest_index(float(x), x_cols)
        cell_col = next(
            idx
            for idx, group in enumerate(cell_column_groups)
            if x_cols[x_col] in group
        )
        row = _nearest_index(float(y), y_rows)
        cells_by_key.setdefault((row, cell_col), []).append((float(x), float(y)))

    cells: list[BrailleCell] = []
    for (row, col), cell_pts in cells_by_key.items():
        arr = np.asarray(cell_pts, dtype=np.float32)
        group = cell_column_groups[col]
        left_x = group[0]
        right_x = group[-1] if len(group) > 1 else left_x + spacing
        top_y = min(arr[:, 1])
        pattern = [0, 0, 0, 0, 0, 0]
        for x, y in arr:
            dot_col = 0 if abs(x - left_x) <= abs(x - right_x) else 1
            dot_row = int(np.clip(round((y - top_y) / spacing), 0, 2))
            pattern[dot_row + dot_col * 3] = 1
        cells.append(
            BrailleCell(
                row=row,
                col=col,
                pattern=tuple(pattern),
                center_x=float(arr[:, 0].mean()),
                center_y=float(arr[:, 1].mean()),
            )
        )

    return sorted(cells, key=lambda cell: (cell.row, cell.col))
