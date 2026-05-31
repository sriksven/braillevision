import numpy as np
import pytest

from braillevision.recognition import CAPITAL_INDICATOR, pattern_for_char


def generate_braille_image(
    text: str,
    width: int | None = None,
    height: int = 220,
    dot_spacing: int = 22,
    dot_radius: int = 7,
    cell_gap: int = 42,
    margin: int = 36,
) -> np.ndarray:
    from PIL import Image, ImageDraw, ImageFilter

    patterns = []
    for char in text:
        if char == " ":
            patterns.append(None)
            continue
        if char.isupper():
            patterns.append(CAPITAL_INDICATOR)
        patterns.append(pattern_for_char(char))

    width = width or max(240, margin * 2 + len(patterns) * (dot_spacing + cell_gap))
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    x = margin
    y = margin
    for pat in patterns:
        if pat is not None:
            for idx, enabled in enumerate(pat):
                if not enabled:
                    continue
                col = idx // 3
                row = idx % 3
                cx = x + col * dot_spacing
                cy = y + row * dot_spacing
                draw.ellipse(
                    (
                        cx - dot_radius,
                        cy - dot_radius,
                        cx + dot_radius,
                        cy + dot_radius,
                    ),
                    fill=(28, 28, 28),
                )
        x += dot_spacing + cell_gap
    return np.asarray(img.filter(ImageFilter.SMOOTH_MORE))


@pytest.fixture
def blank_frame():
    return np.full((240, 320, 3), 255, dtype=np.uint8)


@pytest.fixture
def synthetic_hello():
    return generate_braille_image("hello")


@pytest.fixture
def synthetic_text():
    def factory(text: str):
        return generate_braille_image(text)

    return factory
