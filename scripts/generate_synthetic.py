"""Generate synthetic Braille images with known ground truth."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from braillevision.recognition import CAPITAL_INDICATOR, pattern_for_char

ROOT = Path(__file__).resolve().parents[1]


def _patterns_for_text(text: str) -> list[tuple[int, int, int, int, int, int] | None]:
    patterns: list[tuple[int, int, int, int, int, int] | None] = []
    for char in text:
        if char == " ":
            patterns.append(None)
            continue
        if char.isupper():
            patterns.append(CAPITAL_INDICATOR)
        patterns.append(pattern_for_char(char))
    return patterns


def generate_braille_image(
    text: str,
    width: int | None = None,
    height: int = 220,
    dot_spacing: int = 22,
    dot_radius: int = 7,
    cell_gap: int = 42,
    margin: int = 36,
) -> np.ndarray:
    """Create a clean white image with dark Braille dots."""

    patterns = _patterns_for_text(text)
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

    img = img.filter(ImageFilter.SMOOTH_MORE)
    return np.asarray(img)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", help="Text to render as Grade 1 Braille.")
    parser.add_argument(
        "--out", type=Path, default=ROOT / "data" / "samples" / "sample.png"
    )
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(generate_braille_image(args.text)).save(args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
