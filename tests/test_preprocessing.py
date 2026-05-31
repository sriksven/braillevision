import numpy as np

from braillevision.preprocessing import (
    correct_perspective,
    enhance_contrast,
    preprocess,
    to_gray,
)


def test_to_gray_accepts_color_and_gray(blank_frame):
    gray = to_gray(blank_frame)
    assert gray.shape == blank_frame.shape[:2]
    assert gray.dtype == np.uint8
    assert to_gray(gray).shape == gray.shape


def test_enhance_contrast_preserves_shape(synthetic_hello):
    gray = to_gray(synthetic_hello)
    enhanced = enhance_contrast(gray)
    assert enhanced.shape == gray.shape
    assert enhanced.dtype == np.uint8
    assert enhanced.max() >= enhanced.min()


def test_blank_image_does_not_crash(blank_frame):
    processed = preprocess(blank_frame)
    assert processed.shape == blank_frame.shape[:2]


def test_perspective_fallback_returns_image(blank_frame):
    corrected = correct_perspective(blank_frame)
    assert corrected.shape == blank_frame.shape
