"""Create lighting, blur, and rotation variants for Braille images."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter


def augment_image(path: Path, out_dir: Path) -> None:
    img = Image.open(path).convert("RGB")
    variants = {
        "normal": img,
        "dim": ImageEnhance.Brightness(img).enhance(0.65),
        "bright": ImageEnhance.Brightness(img).enhance(1.35),
        "side_light": ImageEnhance.Contrast(
            ImageEnhance.Brightness(img).enhance(0.85)
        ).enhance(1.6),
        "contrast": ImageEnhance.Contrast(img).enhance(1.45),
        "blur": img.filter(ImageFilter.GaussianBlur(1.2)),
        "rotate_pos5": img.rotate(5, expand=False, fillcolor="white"),
        "rotate_neg5": img.rotate(-5, expand=False, fillcolor="white"),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, variant in variants.items():
        variant.save(out_dir / f"{path.stem}_{name}{path.suffix}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", "--src", dest="src", type=Path, default=Path("data/samples")
    )
    parser.add_argument(
        "--output", "--out", dest="out", type=Path, default=Path("data/processed")
    )
    args = parser.parse_args()
    for image_path in sorted(args.src.glob("*.*")):
        augment_image(image_path, args.out)


if __name__ == "__main__":
    main()
