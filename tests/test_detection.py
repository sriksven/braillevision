from braillevision.detection import Dot, detect_dots, filter_noise_keypoints


def test_synthetic_hello_detects_expected_dots(synthetic_hello):
    dots = detect_dots(synthetic_hello)
    assert len(dots) == 14


def test_blank_frame_detects_no_dots(blank_frame):
    assert detect_dots(blank_frame) == []


def test_inverted_image_also_works(synthetic_hello):
    inverted = 255 - synthetic_hello
    assert len(detect_dots(inverted)) == 14


def test_noise_filter_removes_far_outlier():
    dots = [Dot(10, 10), Dot(12, 10), Dot(11, 13), Dot(500, 500)]
    filtered = filter_noise_keypoints(dots, radius=25)
    assert len(filtered) == 3
