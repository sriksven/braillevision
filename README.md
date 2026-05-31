---
title: BrailleVision
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
---

# BrailleVision

[![CI](https://github.com/sriksven/braillevision/actions/workflows/ci.yml/badge.svg)](https://github.com/sriksven/braillevision/actions/workflows/ci.yml)

BrailleVision is a computer-vision demo that reads camera or uploaded images of Braille and returns English text with an annotated detection overlay. The current implementation is validated on synthetic Braille images and is ready for the next phase: real embossed Braille image collection, tuning, and benchmarking.

## Status

- OpenCV-backed test suite passes locally: `20 passed`
- Coverage from the latest local run: `72%`
- Formatting and linting are clean with Black, isort, and flake8
- Flask demo runs locally at `http://127.0.0.1:7860`
- Docker build, health check, UI load, and sample upload were verified locally
- 10 public real Braille photos have been downloaded locally for smoke testing
- 80 augmented real-image variants were generated locally

## Features

- CLAHE contrast normalization for uneven lighting
- Dot detection for dark-on-light and light-on-dark images
- Braille-cell segmentation from detected dot geometry
- Grade 1 Braille lookup with capital and number indicators
- Partial Grade 2 contraction table
- Flask web demo with MJPEG stream, upload, stats, history, copy, and browser TTS
- Synthetic image generation, augmentation, and benchmark scripts
- Docker and GitHub Actions CI configuration

## Quick Start

Use Python 3.11 if available.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
python scripts/generate_synthetic.py hello --out data/samples/hello.png
python app/app.py
```

Open:

```text
http://127.0.0.1:7860
```

## Checks

```bash
.venv/bin/pytest tests/ -v --cov=src/braillevision --cov-report=term-missing
.venv/bin/black --check .
.venv/bin/isort --check-only .
.venv/bin/flake8 . --max-line-length=100
```

To auto-format:

```bash
.venv/bin/black .
.venv/bin/isort .
```

## Docker

Start Docker Desktop first, then run:

```bash
docker compose up --build
```

Open:

```text
http://localhost:7860
```

Health check:

```bash
curl http://localhost:7860/health
```

Expected response:

```json
{"status": "ok", "version": "1.0"}
```

## Project Structure

```text
src/braillevision/          Core CV pipeline and recognition logic
app/                        Flask routes and vanilla browser UI
tests/                      Unit and integration tests
scripts/                    Synthetic data, augmentation, and benchmark utilities
data/samples/               Small committed demo images and uploaded local samples
data/raw/                   Local raw real images, ignored by git
data/processed/             Generated variants, ignored by git
data/annotations/           Local annotation JSON, ignored by git
docs/                       Architecture, API, and next-step notes
.github/workflows/ci.yml    GitHub Actions test and lint workflow
```

## How It Works

The main entry point is `run_pipeline(frame)` in `src/braillevision/pipeline.py`.

```text
frame
  -> preprocessing.preprocess()
  -> detection.detect_dots()
  -> detection.filter_noise_keypoints()
  -> segmentation.cluster_dots_to_cells()
  -> recognition.cells_to_text()
  -> PipelineResult
```

`PipelineResult` contains decoded text, dot count, cell count, estimated dot spacing, confidence, detected cells, and an annotated frame.

## Synthetic Images

Generate a sample:

```bash
python scripts/generate_synthetic.py hello --out data/samples/hello.png
```

The test suite uses synthetic images for deterministic regression coverage.

## Real-Image Workflow

Real embossed Braille is the next important milestone.

1. Save real photos under `data/raw/`.
2. Run the app and upload images through the UI.
3. Tune `src/braillevision/config.py` based on detection quality.
4. Copy representative working images into `data/samples/`.
5. Add annotations under `data/annotations/`.
6. Augment and benchmark.

Example annotation:

```json
{
  "image": "sample.jpg",
  "text": "the actual english text",
  "conditions": {
    "lighting": "normal",
    "blur": 0,
    "rotation_deg": 0
  }
}
```

## Augmentation

Generate eight variants per input image:

```bash
python scripts/augment_data.py --input data/raw/ --output data/processed/
```

The script also accepts the older aliases:

```bash
python scripts/augment_data.py --src data/raw/ --out data/processed/
```

## Benchmarking

Run:

```bash
python scripts/benchmark.py --testset data/processed/
```

The benchmark script looks for annotation JSON files next to each processed image and in `data/annotations/`.

Current status: the benchmark command runs, but accuracy is blocked until real-image annotation JSON exists.

Report results as character error rate or accuracy:

```text
accuracy = 1 - CER
```

README benchmark table template:

```markdown
| Condition    | Accuracy |
|--------------|----------|
| Normal light | TBD      |
| Side light   | TBD      |
| Dim          | TBD      |
| Slight blur  | TBD      |
| 5 deg rotate | TBD      |
```

Use real numbers after collecting and annotating real images.

## Documentation

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [TODO](docs/todo.md)
- [Next Steps](docs/next_steps.md)

## Limitations

- Current automated tests use synthetic Braille images.
- Real embossed Braille needs image collection, detector tuning, and measured benchmarks.
- Grade 2 contraction support is partial.
- Upload validation is minimal and should be tightened before public deployment.
- Docker and CI are configured, but Docker still needs local daemon verification.
