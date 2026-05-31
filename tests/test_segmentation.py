import numpy as np

from braillevision.detection import detect_dots
from braillevision.segmentation import cluster_dots_to_cells


def test_synthetic_hello_segments_five_cells(synthetic_hello):
    dots = detect_dots(synthetic_hello)
    cells = cluster_dots_to_cells(dots)
    assert len(cells) == 5
    assert [(cell.row, cell.col) for cell in cells] == [
        (0, 0),
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 4),
    ]


def test_empty_input_segments_to_empty():
    assert cluster_dots_to_cells([]) == []


def test_small_tilt_still_segments_five_cells(synthetic_hello):
    try:
        from scipy.ndimage import rotate
    except Exception:
        return
    rotated = rotate(
        synthetic_hello, angle=5, reshape=False, mode="constant", cval=255
    ).astype(np.uint8)
    dots = detect_dots(rotated)
    cells = cluster_dots_to_cells(dots)
    assert len(cells) == 5
