"""Benchmark BrailleVision on annotated images."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from braillevision.pipeline import run_pipeline
from braillevision.utils import load_image

ROOT = Path(__file__).resolve().parents[1]


def find_annotation(image_path: Path) -> Path | None:
    candidates = [
        image_path.with_suffix(".json"),
        ROOT / "data" / "annotations" / f"{image_path.stem}.json",
        ROOT / "data" / "annotations" / f"{image_path.name}.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--testset", type=Path, default=ROOT / "data" / "processed")
    args = parser.parse_args()

    rows: list[dict[str, object]] = []
    for image_path in sorted(args.testset.glob("*.*")):
        annotation_path = find_annotation(image_path)
        if annotation_path is None:
            continue
        expected = json.loads(annotation_path.read_text()).get("text", "")
        result = run_pipeline(load_image(image_path))
        distance = levenshtein(result.text, expected)
        cer = distance / max(len(expected), 1)
        rows.append(
            {
                "image": image_path.name,
                "expected": expected,
                "predicted": result.text,
                "cer": cer,
            }
        )

    if not rows:
        print("No annotated images found.")
        return

    mean_cer = sum(float(row["cer"]) for row in rows) / len(rows)
    for row in rows:
        print(
            f"{row['image']}: CER={row['cer']:.3f} "
            f"expected={row['expected']!r} predicted={row['predicted']!r}"
        )
    print(f"mean CER: {mean_cer:.3f}")


if __name__ == "__main__":
    main()
