# Contributing

## Local Setup

Use Python 3.11 when possible.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
pre-commit install
```

Confirm OpenCV is installed:

```bash
.venv/bin/python -c "import cv2; print(cv2.__version__)"
```

## Required Checks

Run these before committing:

```bash
.venv/bin/pytest tests/ -v --cov=src/braillevision --cov-report=term-missing
.venv/bin/black --check .
.venv/bin/isort --check-only .
.venv/bin/flake8 . --max-line-length=100
```

Auto-format with:

```bash
.venv/bin/black .
.venv/bin/isort .
```

## Development Notes

- Keep CV logic inside `src/braillevision/`.
- Keep Flask, upload handling, and browser behavior inside `app/`.
- Do not commit large raw datasets. `data/raw/`, `data/processed/`, and `data/annotations/` are ignored except for `.gitkeep` files.
- Add focused tests for every detector, segmentation, or recognition change.
- Synthetic images are good for regression tests, but real-image benchmark cases should include annotation JSON.
- If you tune `PipelineConfig`, record the image conditions that motivated the change.

## Docker Check

Start Docker Desktop first:

```bash
docker compose up --build
curl http://localhost:7860/health
docker compose down
```

Expected health response:

```json
{"status": "ok", "version": "1.0"}
```

